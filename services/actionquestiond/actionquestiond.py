"""Driver intent / action-question manager for shadow learning.

Questions are allowed only to resolve preference/route ambiguity between options
already judged legal, physically safe and vehicle-capable. Never asks the driver
to arbitrate an unresolved safety or legality question.
"""

from dataclasses import dataclass
from enum import Enum


class QuestionPolicy(str, Enum):
    NO_QUESTION = "NO_QUESTION"
    ASK_DRIVER = "ASK_DRIVER"
    WAIT_CONSERVATIVELY = "WAIT_CONSERVATIVELY"
    TAKEOVER_RECOMMENDED = "TAKEOVER_RECOMMENDED"


@dataclass(frozen=True)
class IntentContext:
    legal_known: bool
    safety_known: bool
    capability_known: bool
    valid_options: tuple[str, ...]
    preferred_option: str | None = None
    route_requires_choice: bool = False
    decision_margin: float = 1.0
    time_to_decision_s: float = 99.0
    driver_available: bool = True


@dataclass(frozen=True)
class ActionQuestion:
    policy: QuestionPolicy
    prompt: str | None
    options: tuple[str, ...]
    default_action: str
    reason: str


def decide(ctx: IntentContext) -> ActionQuestion:
    if not ctx.legal_known:
        return ActionQuestion(QuestionPolicy.WAIT_CONSERVATIVELY, None, (), "WAIT", "LEGALITY_UNRESOLVED")
    if not ctx.safety_known:
        return ActionQuestion(QuestionPolicy.WAIT_CONSERVATIVELY, None, (), "WAIT", "SAFETY_UNRESOLVED")
    if not ctx.capability_known:
        return ActionQuestion(QuestionPolicy.WAIT_CONSERVATIVELY, None, (), "WAIT", "BMW_CAPABILITY_UNRESOLVED")

    opts = tuple(dict.fromkeys(ctx.valid_options))
    if not opts:
        return ActionQuestion(QuestionPolicy.TAKEOVER_RECOMMENDED, None, (), "WAIT", "NO_VALID_OPTION")
    if len(opts) == 1:
        return ActionQuestion(QuestionPolicy.NO_QUESTION, None, opts, opts[0], "SINGLE_VALID_OPTION")

    # Do not distract the driver with a question when the decision horizon is short.
    if ctx.time_to_decision_s < 5.0:
        default = ctx.preferred_option if ctx.preferred_option in opts else "WAIT"
        return ActionQuestion(QuestionPolicy.WAIT_CONSERVATIVELY, None, opts, default, "TOO_LATE_TO_ASK")

    ambiguous = ctx.decision_margin < 0.15
    if ctx.driver_available and (ambiguous or ctx.route_requires_choice):
        prompt = "Choose preferred action: " + " / ".join(opts)
        default = ctx.preferred_option if ctx.preferred_option in opts else "WAIT"
        return ActionQuestion(QuestionPolicy.ASK_DRIVER, prompt, opts, default, "SAFE_PREFERENCE_AMBIGUITY")

    default = ctx.preferred_option if ctx.preferred_option in opts else "WAIT"
    return ActionQuestion(QuestionPolicy.NO_QUESTION, None, opts, default, "USE_EXISTING_PREFERENCE")
