"""Knowledge: Streamlit screens only. Content is in knowledge_content.py, the rules
in knowledge.py and the storage in knowledge_db.py.

app.py calls `render()` to show the Knowledge tab and `leave()` when the user
switches to another section. Everything this file keeps in st.session_state
starts with "kn_", so it cannot clash with the other tabs. The practice round
itself runs in the flow shared with Textbook (practice_ui.py).
"""

import random

import streamlit as st

import activity_db
import knowledge_db
import textbook_ui
from knowledge import (
    ROUND_LENGTH,
    Outcome,
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
from practice_ui import Practice
from stats import Kind
from tasks import LEVELS
from ui_components import (
    EXAMPLE_SEED,
    back_button,
    card_header,
    example_box,
    list_rows,
    pick,
    previous_next_bar,
    tile_grid,
)

TRICKS_MODE = "Tricks"
TEXTBOOK_MODE = "Textbook"
DESCRIPTION = "Learn mental-math tricks step by step, then practise exactly that trick."
PRACTICE_NOTE = f"{ROUND_LENGTH} tasks for this trick, no time limit."
IGNORED_HINT = "Numbers only, e.g. 4250"

state = st.session_state


def _show_feedback(attempt) -> None:
    """How the previous task went. After a wrong answer or skip, the answer is shown."""
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



def save_owned_round(round_id, practice_round, finished_at) -> None:
    """Save the completed round and record the signed in player (spec 012)."""
    knowledge_db.save_round(round_id, practice_round, finished_at)
    activity_db.assign_owner(Kind.TRICKS, round_id, state.user.id)


PRACTICE = Practice(
    "kn_",
    start_round=start_round,
    submit_answer=submit_answer,
    skip_task=skip_task,
    current_task=current_task,
    save_round=save_owned_round,
    item_of=lambda practice_round: practice_round.trick_id,
    item_screen="trick",
    back_label="Back to trick",
    back_key="kn_to_trick",
    show_task=lambda task: st.header(task.text, anchor=False),
    show_feedback=_show_feedback,
    hint=lambda task: IGNORED_HINT,
    placeholder=lambda task: "Whole number",
    length=ROUND_LENGTH,
)


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


def leave() -> None:
    """For app.py: the user switched to another section. A running round is not saved."""
    PRACTICE.leave()
    textbook_ui.leave()


def _on_start() -> None:
    PRACTICE.begin(state.kn_trick, state.get("kn_level") or LEVELS[0])


def _open_trick_from_textbook(trick_id: str) -> None:
    """A related-trick link in an article: switch to Tricks and open that trick.

    A round that was running in Tricks ends without saving, as when leaving it.
    """
    PRACTICE.clear()
    state.pop("kn_result", None)
    state.kn_mode = TRICKS_MODE
    _open_trick(trick_id)


# --- Screens ---


def render_overview() -> None:
    st.header("Knowledge", anchor=False)
    st.caption(DESCRIPTION)
    st.subheader("Operations", anchor=False)
    tile_grid(
        [
            (f"{category.name} ({len(category.tricks)})", f"kn_category_{category.id}",
             (category.id,))
            for category in CATEGORIES
        ],
        _open_category,
    )  # fmt: skip


def render_category() -> None:
    category = get_category(state.kn_category)
    back_button("kn_back", _go, ("overview",))
    st.header(category.name, anchor=False)
    st.caption(category.subtitle)

    done = practised(knowledge_db.list_rounds_for(state.user.id))  # spec 014
    list_rows(
        [
            (f"{trick.name} · {trick.difficulty}{' ✓' if trick.id in done else ''}",
             f"kn_trick_{trick.id}", (trick.id,))
            for trick in category.tricks
        ],
        _open_trick,
    )  # fmt: skip


def _steps_markdown(example) -> str:
    return "\n".join(
        f"{number}. **{step.text}** · `{step.calculation}`"
        for number, step in enumerate(example.steps, start=1)
    )


def render_trick() -> None:
    trick = get_trick(state.kn_trick)
    category = category_of(trick.id)
    back_button("kn_back", _go, ("category",))
    st.header(trick.name, anchor=False)
    st.caption(trick.description)

    for example in trick.examples:
        with st.container(border=True):
            card_header(example.label, category.name, example.difficulty)
            st.subheader(example.equation, anchor=False)

    if trick.note:
        st.info(trick.note)

    st.subheader("Steps", anchor=False)
    for example in trick.examples:
        if len(trick.examples) > 1:
            st.markdown(f"**{example.label}** · {example.equation}")
        st.markdown(_steps_markdown(example))

    previous_next_bar("kn_", *neighbours(trick.id), *position(trick.id), _open_trick)
    st.button("Practice", key="kn_practice", type="primary", on_click=_go, args=("setup",),
              width="stretch")  # fmt: skip


def render_setup() -> None:
    trick = get_trick(state.kn_trick)
    back_button("kn_back", _go, ("trick",))
    st.header(f"Practise: {trick.name}", anchor=False)
    st.caption(PRACTICE_NOTE)
    level = pick(st.segmented_control, "Level", LEVELS, "kn_level")
    example = generate_task(trick.id, level, random.Random(EXAMPLE_SEED))
    example_box("Calculate", example.text)
    st.button("Start", key="kn_start", type="primary", on_click=_on_start)


def render_running() -> None:
    practice_round = state.kn_round
    PRACTICE.render_running(f"{get_trick(practice_round.trick_id).name} · {practice_round.level}")


def render_result() -> None:
    PRACTICE.render_result(f"Practice finished: {get_trick(state.kn_result.trick_id).name}")


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
        textbook_ui.render(on_open_trick=_open_trick_from_textbook)
        return

    if state.kn_screen == "running" and "kn_round" not in state:
        state.kn_screen = "trick"  # nothing to continue
    SCREENS[state.kn_screen]()
