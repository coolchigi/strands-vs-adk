"""What the ADK brain does when Gemini stops a call, with no model behind it."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from impl.adk.brain import ANSWER_PLEASE, IN_YOUR_OWN_WORDS, NoAnswer, ask_again
from impl.adk.telemetry import Recitation, raise_for


def test_a_recitation_stop_is_its_own_error():
    # a lesson call once ended the whole run with "RuntimeError lesson failed: RECITATION None"
    with pytest.raises(Recitation):
        raise_for(SimpleNamespace(error_code="RECITATION", error_message=None), "lesson")


def test_a_recitation_stop_is_asked_again_with_the_reason():
    prompts = []

    def call(prompt):
        prompts.append(prompt)
        if len(prompts) < 3:
            raise Recitation("stopped")
        return "a lesson"

    assert ask_again(call, "write u3-l1") == "a lesson"
    assert prompts[0] == "write u3-l1" and prompts[2].endswith(IN_YOUR_OWN_WORDS)


def test_it_gives_up_after_its_tries():
    def call(prompt):
        raise Recitation("stopped")

    with pytest.raises(Recitation):
        ask_again(call, "p", tries=2)


def test_an_agent_that_ends_without_an_answer_is_asked_again_with_the_reason():
    # the TypeScript research agent searched for 2 minutes and stopped without answering
    prompts = []

    def call(prompt):
        prompts.append(prompt)
        if len(prompts) == 1:
            raise NoAnswer("spec ended its turn without an answer")
        return "a spec"

    assert ask_again(call, "find the docs") == "a spec"
    assert prompts[1] == "find the docs" + ANSWER_PLEASE


def test_a_busy_gemini_is_retried_instead_of_ending_the_build(monkeypatch):
    # one 503 from Gemini once ended a 70-minute build at lesson 12
    import json
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    from google.genai import types
    from pydantic import BaseModel

    from impl.adk import brain

    answers = [(503, {"error": {"code": 503, "message": "busy", "status": "UNAVAILABLE"}}),
               (200, {"candidates": [{"content": {"role": "model", "parts": [{"text": '{"value": "hi"}'}]},
                                      "finishReason": "STOP", "index": 0}]})]
    seen = []

    class Gemini(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_POST(self):
            self.rfile.read(int(self.headers.get("content-length", 0)))
            status, body = answers[min(len(seen), len(answers) - 1)]
            seen.append(status)
            data = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Gemini)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv("GOOGLE_API_KEY", "not-a-real-key")
    monkeypatch.setenv("GOOGLE_GEMINI_BASE_URL", f"http://127.0.0.1:{server.server_address[1]}/")
    # the shipped policy waits 2 s first; the same policy with a shorter wait keeps the test quick
    monkeypatch.setattr(brain, "RETRIES", brain.RunConfig(http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(attempts=8, initial_delay=0.1, max_delay=0.2))))

    class Answer(BaseModel):
        value: str

    try:
        assert brain.AdkBrain().ask("lesson", "write it", "u1-l1", Answer).value == "hi"
    finally:
        server.shutdown()
    assert seen == [503, 200]


def test_retries_ride_out_a_few_minutes_of_errors():
    from impl.adk.brain import RETRIES

    retry = RETRIES.http_options.retry_options
    assert (retry.attempts, retry.initial_delay, retry.max_delay) == (8, 2, 60)
