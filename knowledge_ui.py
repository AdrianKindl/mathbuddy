"""Knowledge: Streamlit screens only. Content is in knowledge_content.py, the rules
in knowledge.py and the storage in knowledge_db.py.

app.py calls `render()` to show the Knowledge tab and `leave()` when the user
switches to another section. Everything this file keeps in st.session_state
starts with "kn_", so it cannot clash with the other tabs.
"""

import random
import uuid
from datetime import datetime, timezone

import streamlit as st

import knowledge_db
from knowledge import (
    ROUND_LENGTH,
    Outcome,
    Round,
    Status,
    current_task,
    generate_task,
    neighbours,
    position,
    practised,
    skip_task,
    start_round,
    submit_answer,
)
from knowledge_content import CATEGORIES, category_of, get_category, get_trick
from tasks import LEVELS
from ui_components import (
    EXAMPLE_SEED,
    answer_flash,
    answer_focus,
    answer_form,
    example_box,
    pick,
)

TRICKS_MODE = "Tricks"
TEXTBOOK_MODE = "Textbook"
DESCRIPTION = "Learn mental-math tricks step by step, then practise exactly that trick."
PRACTICE_NOTE = f"{ROUND_LENGTH} tasks for this trick, no time limit."
IGNORED_HINT = "Numbers only, e.g. 4250"
TILES_PER_ROW = 3
FLASH = {Outcome.CORRECT: "green", Outcome.WRONG: "red"}
ROUND_KEYS = ("kn_round", "kn_round_id", "kn_rng", "kn_flash", "kn_hint", "kn_feedback")

state = st.session_state


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# --- Changing screens ---


def _go(screen: str) -> None:
    state.kn_screen = screen


def _open_category(category_id: str) -> None:
    state.kn_category = category_id
    state.kn_screen = "category"


def _open_trick(trick_id: str) -> None:
    state.kn_trick = trick_id
    state.kn_category = category_of(trick_id).id
    state.kn_screen = "trick"


def _clear_round() -> None:
    for name in ROUND_KEYS:
        state.pop(name, None)


def _begin(trick_id: str, level: str) -> None:
    _clear_round()
    state.pop("kn_result", None)
    state.kn_rng = random.Random()
    state.kn_round = start_round(trick_id, level, state.kn_rng)
    state.kn_round_id = str(uuid.uuid4())
    state.kn_attempt = state.get("kn_attempt", 0) + 1
    state.kn_screen = "running"


def _finish(practice_round: Round) -> None:
    """Save the completed round and show the result. Safe to repeat (K R6)."""
    knowledge_db.save_round(state.kn_round_id, practice_round, _utc_now())
    state.kn_result = practice_round
    feedback = state.get("kn_feedback")
    _clear_round()
    state.kn_feedback = feedback  # the result also shows how the last task went
    state.kn_screen = "result"


def _apply(practice_round: Round, outcome: Outcome) -> None:
    state.kn_attempt += 1  # the flash and the focus script run again for every attempt
    state.kn_round = practice_round
    state.kn_hint = outcome == Outcome.IGNORED
    state.kn_flash = FLASH.get(outcome)
    if outcome != Outcome.IGNORED:
        state.kn_feedback = practice_round.attempts[-1]
    if practice_round.status == Status.COMPLETED:
        _finish(practice_round)


def leave() -> None:
    """For app.py: the user switched to another section. A running round is not saved."""
    if "kn_screen" not in state:
        return
    _clear_round()
    state.pop("kn_result", None)
    if state.kn_screen in ("setup", "running", "result"):
        state.kn_screen = "trick"


# --- Callbacks ---


def _on_start() -> None:
    _begin(state.kn_trick, state.get("kn_level") or LEVELS[0])


def _on_submit() -> None:
    _apply(*submit_answer(state.kn_round, state.kn_answer))


def _on_skip() -> None:
    _apply(*skip_task(state.kn_round))


def _on_leave_round() -> None:
    _clear_round()  # leaving early saves nothing (K R6)
    state.kn_screen = "trick"


def _on_again() -> None:
    result = state.kn_result
    _begin(result.trick_id, result.level)


def _on_back_to_trick() -> None:
    state.pop("kn_result", None)
    _clear_round()
    state.kn_screen = "trick"


# --- Screens ---


def render_overview() -> None:
    st.header("Knowledge", anchor=False)
    st.caption(DESCRIPTION)
    st.subheader("Operations", anchor=False)
    # One row of columns at a time, so the tiles keep the catalogue order.
    for start in range(0, len(CATEGORIES), TILES_PER_ROW):
        columns = st.columns(TILES_PER_ROW)
        for column, category in zip(columns, CATEGORIES[start : start + TILES_PER_ROW]):
            column.button(
                f"{category.name} ({len(category.tricks)})",
                key=f"kn_category_{category.id}",
                on_click=_open_category,
                args=(category.id,),
                width="stretch",
            )


def render_category() -> None:
    category = get_category(state.kn_category)
    st.button("← Back", key="kn_back", on_click=_go, args=("overview",))
    st.header(category.name, anchor=False)
    st.caption(category.subtitle)

    done = practised(knowledge_db.list_rounds())
    for trick in category.tricks:
        tick = " ✓" if trick.id in done else ""
        st.button(
            f"{trick.name} · {trick.difficulty}{tick}",
            key=f"kn_trick_{trick.id}",
            on_click=_open_trick,
            args=(trick.id,),
            width="stretch",
        )


def _steps_markdown(example) -> str:
    return "\n".join(
        f"{number}. **{step.text}** · `{step.calculation}`"
        for number, step in enumerate(example.steps, start=1)
    )


def render_trick() -> None:
    trick = get_trick(state.kn_trick)
    category = category_of(trick.id)
    st.button("← Back", key="kn_back", on_click=_go, args=("category",))
    st.header(trick.name, anchor=False)
    st.caption(trick.description)

    for example in trick.examples:
        with st.container(border=True):
            st.markdown(
                f"**{example.label}**  \n"
                f":blue-badge[{category.name}] :orange-badge[{example.difficulty}]"
            )
            st.subheader(example.equation, anchor=False)

    if trick.note:
        st.info(trick.note)

    st.subheader("Steps", anchor=False)
    for example in trick.examples:
        if len(trick.examples) > 1:
            st.markdown(f"**{example.label}** · {example.equation}")
        st.markdown(_steps_markdown(example))

    previous_id, next_id = neighbours(trick.id)
    number, total = position(trick.id)
    left, middle, right = st.columns(3, vertical_alignment="center")
    left.button(
        "← Previous",
        key="kn_prev",
        disabled=previous_id is None,
        on_click=_open_trick,
        args=(previous_id,),
        width="stretch",
    )
    middle.markdown(f"<div style='text-align: center'>{number} / {total}</div>",
                    unsafe_allow_html=True)  # fmt: skip
    right.button(
        "Next →",
        key="kn_next",
        disabled=next_id is None,
        on_click=_open_trick,
        args=(next_id,),
        width="stretch",
    )
    st.button("Practice", key="kn_practice", type="primary", on_click=_go, args=("setup",),
              width="stretch")  # fmt: skip


def render_setup() -> None:
    trick = get_trick(state.kn_trick)
    st.button("← Back", key="kn_back", on_click=_go, args=("trick",))
    st.header(f"Practise: {trick.name}", anchor=False)
    st.caption(PRACTICE_NOTE)
    level = pick(st.segmented_control, "Level", LEVELS, "kn_level")
    example = generate_task(trick.id, level, random.Random(EXAMPLE_SEED))
    example_box("Calculate", example.text)
    st.button("Start", key="kn_start", type="primary", on_click=_on_start)


def _render_feedback() -> None:
    """How the previous task went. After a wrong answer or skip, the answer is shown."""
    attempt = state.get("kn_feedback")
    if attempt is None:
        return
    task = attempt.task
    if attempt.outcome == Outcome.CORRECT:
        st.success(f"Correct! {task.text} = {task.answer:,}")
    elif attempt.outcome == Outcome.WRONG:
        st.error(
            f"Not quite. You answered {attempt.given} for {task.text}. "
            f"The answer is {task.answer:,}."
        )
    else:
        st.warning(f"Skipped {task.text}. The answer is {task.answer:,}.")


def render_running() -> None:
    practice_round = state.kn_round
    task = current_task(practice_round)
    done = len(practice_round.attempts)

    st.caption(f"{get_trick(practice_round.trick_id).name} · {practice_round.level}")
    st.markdown(f"**Task {done + 1} / {ROUND_LENGTH}**")
    st.progress(done / ROUND_LENGTH)
    st.header(task.text, anchor=False)
    answer_form("kn_", _on_submit, _on_skip, placeholder="Whole number")

    if state.get("kn_hint"):
        st.warning(IGNORED_HINT)
    _render_feedback()
    st.button("Back to trick", key="kn_leave", on_click=_on_leave_round)

    answer_flash("kn_", state.get("kn_flash"), state.kn_attempt)
    answer_focus("kn_", state.kn_attempt)


def render_result() -> None:
    result = state.kn_result
    st.header(f"Practice finished: {get_trick(result.trick_id).name}", anchor=False)
    st.caption(f"Level: {result.level}")
    _render_feedback()

    correct, wrong, skipped = st.columns(3)
    correct.metric("Correct", f"{result.correct} / {ROUND_LENGTH}")
    wrong.metric("Wrong", result.wrong)
    skipped.metric("Skipped", result.skipped)

    again, back = st.columns(2)
    again.button("Practise again", key="kn_again", type="primary", on_click=_on_again,
                 width="stretch")  # fmt: skip
    back.button("Back to trick", key="kn_to_trick", on_click=_on_back_to_trick,
                width="stretch")  # fmt: skip


SCREENS = {
    "overview": render_overview,
    "category": render_category,
    "trick": render_trick,
    "setup": render_setup,
    "running": render_running,
    "result": render_result,
}


def render() -> None:
    if "kn_screen" not in state:  # once per browser session
        knowledge_db.init_db()
        state.kn_screen = "overview"
        state.kn_attempt = 0

    mode = pick(
        st.segmented_control, "Mode", [TRICKS_MODE, TEXTBOOK_MODE], "kn_mode",
        label_visibility="collapsed",
    )  # fmt: skip
    if mode == TEXTBOOK_MODE:
        st.header("Textbook", anchor=False)
        st.info("Coming soon")
        return

    if state.kn_screen == "running" and "kn_round" not in state:
        state.kn_screen = "trick"  # nothing to continue
    SCREENS[state.kn_screen]()
