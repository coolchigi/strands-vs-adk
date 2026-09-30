"""Counting what a run costs, and stopping it before it costs too much. ADK side.

ADK has no metrics object on a result. Usage arrives on each `llm_response`, so the meter
is two callbacks that have to be passed in when an agent is built: `before_model_callback`
refuses a call once the run is over its cap, `after_model_callback` counts.

Gemini 3.x bills thinking as output and reports it separately, as `thoughts_token_count`.

ADK hands an exception from a callback back twice: first as an error event whose
error_code is the exception's class name, then raised when the stream ends. `raise_for`
acts on the event, so the run stops straight away with the cap still recognisable.
"""

from __future__ import annotations

from learning.budget import Budget, BudgetExceeded, Usage, price_for  # noqa: F401  (re-exported)


class Recitation(RuntimeError):
    """Gemini stopped because its answer matched text it was trained on too closely.

    Lessons are written from documentation, so this happens. Asking again usually works.
    """


def raise_for(event, label: str) -> None:
    if not event.error_code:
        return
    if event.error_code == "BudgetExceeded" or "BudgetExceeded" in (event.error_message or ""):
        raise BudgetExceeded(event.error_message)
    if event.error_code == "RECITATION":
        raise Recitation(f"{label}: Gemini stopped with RECITATION")
    raise RuntimeError(f"{label} failed: {event.error_code} {event.error_message}")


class Meter(Budget):
    DEFAULT_LIMIT = "5"

    def callbacks(self, role: str, model: str | None = None) -> dict:
        """Spread into Agent(...). Every agent has to be built with these to be counted.
        `model` is what the agent runs on, so its tokens are priced right after a switch."""
        model = model or self.current_model()

        def before(callback_context=None, llm_request=None, **kw):
            self.check()
            return None

        def after(callback_context=None, llm_response=None, **kw):
            meta = getattr(llm_response, "usage_metadata", None)
            if meta is None:
                return None  # streamed partials carry no usage
            self.by_role.setdefault(role, Usage()).calls += 1
            self.charge(role, meta.prompt_token_count or 0,
                        (meta.candidates_token_count or 0) + (meta.thoughts_token_count or 0), model)
            return None

        return {"before_model_callback": before, "after_model_callback": after}
