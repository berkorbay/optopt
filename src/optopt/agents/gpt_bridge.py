"""Local bridge to a hosted OpenAI model through the ChatGPT subscription (Codex Responses backend), for the D-004
LLM-agent arm. Runs with Hermes Agent's own Python environment and reuses its OAuth token reader and request headers,
so a decision is one HTTPS call and its latency is real. Prompts carry only public-instance features and solver state.

  cd <hermes-agent checkout> && venv/bin/python <optopt>/agents/gpt_bridge.py --model gpt-6-luna
  POST 127.0.0.1:8112/ask {"system": str, "user": str, "effort": "low"} -> {"text": str, "ms": float, "model": str}
"""
import argparse
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, ".")  # hermes-agent checkout (cwd)
import httpx  # noqa: E402
from agent.auxiliary_client import _read_codex_access_token  # noqa: E402
from agent.codex_headers import codex_cloudflare_headers  # noqa: E402

URL = "https://chatgpt.com/backend-api/codex/responses"


def ask(model, system, user, effort="low", timeout=60.0):
    token = _read_codex_access_token()
    h = codex_cloudflare_headers(token)
    h.update({"Accept": "text/event-stream", "Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    body = {"model": model, "store": False, "stream": True, "instructions": system,
            "input": [{"type": "message", "role": "user", "content": [{"type": "input_text", "text": user}]}],
            "reasoning": {"effort": effort}}
    text, usage = [], None
    with httpx.Client(timeout=httpx.Timeout(timeout, connect=15.0)) as c:
        with c.stream("POST", URL, headers=h, json=body) as r:
            if r.status_code != 200:
                r.read()
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
            for line in r.iter_lines():
                if not line.startswith("data:"):
                    continue
                try:
                    ev = json.loads(line[5:].strip())
                except json.JSONDecodeError:
                    continue
                if ev.get("type") == "response.output_text.delta":
                    text.append(ev.get("delta", ""))
                elif ev.get("type") == "response.completed":
                    usage = (ev.get("response") or {}).get("usage")
    return "".join(text), usage


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gpt-6-luna")
    ap.add_argument("--port", type=int, default=8112)
    a = ap.parse_args()

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            t0 = time.perf_counter()
            try:
                txt, usage = ask(a.model, req["system"], req["user"], req.get("effort", "low"), req.get("timeout", 60.0))
                out = {"text": txt, "usage": usage}
            except Exception as e:  # reported to the agent, which then keeps the current setting
                out = {"error": f"{type(e).__name__}: {e}"}
            out.update(ms=round(1000 * (time.perf_counter() - t0), 1), model=a.model)
            b = json.dumps(out).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def log_message(self, *x):
            pass

    print(f"gpt bridge ({a.model}) on 127.0.0.1:{a.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", a.port), H).serve_forever()


if __name__ == "__main__":
    main()
