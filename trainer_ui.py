"""Trainer: Streamlit screens only. The rules live in trainer.py and trainer_tasks.py.

app.py calls `render()` to show the Trainer and `leave()` when the user
switches to another section. Everything this file keeps in st.session_state
starts with "tr_", so it cannot clash with the Tests screen in app.py.
"""

import math
import random
import time
import uuid
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

import trainer_db
from tasks import LEVELS
from trainer import (
    CATEGORIES,
    COUNTDOWN_SECONDS,
    LIMITS,
    NUMBER_TYPES_CATEGORY,
    OPERATIONS_CATEGORY,
    EndReason,
    Mode,
    Outcome,
    Session,
    SettingsError,
    Status,
    abort_session,
    elapsed_seconds,
    finish_if_expired,
    format_duration,
    is_time_up,
    levels_text,
    limit_text,
    make_settings,
    remaining_seconds,
    skip_task,
    start_session,
    submit_answer,
    summarize,
)
from trainer_tasks import (
    ANSWER_HINTS,
    DECIMALS,
    FRACTIONS,
    LARGE,
    MONEY,
    NATURAL,
    NUMBER_TYPES,
    OPERATIONS,
    SPECIAL,
    SPECIAL_TRAININGS,
    AnswerKind,
    Topic,
    generate_task,
)

NO_VALUE = "–"
FLASH_COLORS = {Outcome.CORRECT: "rgb(22, 163, 74)", Outcome.WRONG: "rgb(220, 38, 38)"}
FLASH_MS = 700
LONG_TASK_LENGTH = 40  # longer tasks, such as word problems, use a smaller heading
HISTORY_LENGTH = 10
EXAMPLE_SEED = 7  # a fixed seed, so the example does not change on every rerun

NUMBER_TYPE_NOTES = {
    NATURAL: "Whole numbers. Type answers as whole numbers.",
    DECIMALS: "Numbers with one or two decimals. Type answers with a point, e.g. 12.5.",
    LARGE: "Thousands and millions. Type answers without separators, e.g. 4250000.",
    MONEY: "Amounts in euros and cents. Type answers like 12.50.",
    FRACTIONS: "Type answers as a fraction in lowest terms, e.g. 3/4, or as a whole number.",
}

SPECIAL_NOTES = {
    "Word problems": "Short everyday stories that hide one calculation.",
    "Mixed tasks": "Several operations in one task. Brackets first, then × and ÷, then + and −.",
    "Digit sums": "Add up all the digits of a number.",
    "Rule of three": "Work out the value for one, then for the amount that is asked.",
    "Equations": "Find the number that x stands for.",
    "Chain calculations": "Carry one result through a chain of steps.",
    "Fun with fractions": "Simplify fractions and find the GCD and the LCM.",
}

MODE_NOTES = {
    Mode.TASK_COUNT: "A fixed number of tasks. The time is measured but does not run out.",
    Mode.TOTAL_TIME: "Solve as many tasks as you can before the time runs out.",
    Mode.TIME_PER_TASK: "Every task has its own time limit. "
    "The session ends when one task takes too long.",
}

LIMIT_INPUTS = {  # mode: (label, key, value at the start, step of the + and − buttons)
    Mode.TASK_COUNT: ("Number of tasks", "tr_limit_tasks", 10, 5),
    Mode.TOTAL_TIME: ("Total time in seconds", "tr_limit_total", 120, 30),
    Mode.TIME_PER_TASK: ("Seconds per task", "tr_limit_per_task", 10, 1),
}

PLACEHOLDERS = {
    AnswerKind.WHOLE: "Whole number",
    AnswerKind.DECIMAL: "Decimal, e.g. 12.5",
    AnswerKind.MONEY: "Amount, e.g. 12.50",
    AnswerKind.FRACTION: "Fraction, e.g. 3/4",
}

END_MESSAGES = {
    EndReason.ALL_TASKS_DONE: "All tasks done.",
    EndReason.TIME_UP: "Time's up.",
    EndReason.TOO_SLOW: "The last task took too long, so the session ended.",
}

RESULT_WORDS = {Outcome.CORRECT: "Correct", Outcome.WRONG: "Wrong", Outcome.SKIPPED: "Skipped"}

state = st.session_state


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _percent(value: float | None) -> str:
    return NO_VALUE if value is None else f"{value:.1%}"


# --- Changing screens ---


def _begin() -> None:
    settings = state.tr_settings
    state.tr_session = start_session(settings, _utc_now())
    state.tr_session_id = str(uuid.uuid4())
    state.tr_rng = random.Random()
    state.tr_task = generate_task(settings.topics, state.tr_rng)
    state.tr_feedback = None
    state.tr_flash = None
    state.tr_show_hint = False
    state.tr_attempt = 0
    state.tr_phase = "running"


def _clear_session() -> None:
    for name in (
        "tr_session",
        "tr_session_id",
        "tr_rng",
        "tr_task",
        "tr_feedback",
        "tr_flash",
        "tr_show_hint",
    ):
        state.pop(name, None)
    state.tr_phase = "setup"


def _finish(session: Session) -> None:
    """Save the session and prepare the result. Safe to repeat for the same session."""
    trainer_db.save_session(state.tr_session_id, session)
    # When the time ran out, the task on screen was never answered.
    unanswered = None if session.end_reason == EndReason.ALL_TASKS_DONE else state.tr_task
    state.tr_result = {"session": session, "unanswered": unanswered}
    _clear_session()
    state.tr_phase = "result"


def _apply(session: Session, outcome: Outcome) -> None:
    state.tr_attempt += 1  # the flash and the focus script run again for every attempt
    state.tr_session = session
    if session.status == Status.FINISHED:
        _finish(session)
        return

    state.tr_show_hint = outcome == Outcome.IGNORED
    state.tr_flash = outcome if outcome in FLASH_COLORS else None
    if outcome != Outcome.IGNORED:
        state.tr_feedback = session.attempts[-1]
        state.tr_task = generate_task(
            session.settings.topics, state.tr_rng, previous=state.tr_task
        )


def _end_early(now: datetime) -> None:
    """End the running session: discarded, unless its time was already up."""
    session = abort_session(state.tr_session, now)
    if session.status == Status.FINISHED:
        _finish(session)
    else:
        _clear_session()


def leave() -> None:
    """For app.py: the user switched to another section."""
    if "tr_phase" not in state:
        return
    if state.tr_phase == "running":
        _end_early(_utc_now())
    state.pop("tr_result", None)
    state.tr_phase = "setup"


# --- Callbacks: each one reads the clock first, so the time is as close as
# possible to when the action arrived ---


def _on_submit() -> None:
    now = _utc_now()
    _apply(*submit_answer(state.tr_session, state.tr_task, state.tr_answer, now))


def _on_skip() -> None:
    now = _utc_now()
    _apply(*skip_task(state.tr_session, state.tr_task, now))


def _on_abort() -> None:
    _end_early(_utc_now())


def _on_cancel_countdown() -> None:
    _clear_session()


def _on_train_again() -> None:
    state.tr_settings = state.tr_result["session"].settings
    state.pop("tr_result", None)
    state.tr_phase = "countdown"


def _on_change_settings() -> None:
    state.pop("tr_result", None)
    state.tr_phase = "setup"


# --- Setup screen ---


def _pick(widget, label: str, options, key: str, **options_for_widget) -> str:
    """One choice out of a few. It cannot be empty and is remembered for the session."""
    options = list(options)
    choice = widget(
        label,
        options,
        default=options[0],
        required=True,
        key=key,
        persist_state="session",
        **options_for_widget,
    )
    return choice or options[0]


def _pick_operation() -> tuple[str, list[Topic]]:
    operation = _pick(st.pills, "Operation", OPERATIONS, "tr_operation")
    level = _pick(st.segmented_control, "Level", LEVELS, "tr_level")
    return operation, [Topic(NATURAL, operation, level)]


def _pick_number_type() -> tuple[str, list[Topic]]:
    number_type = _pick(st.pills, "Number type", NUMBER_TYPES, "tr_number_type")
    st.caption(NUMBER_TYPE_NOTES[number_type])
    st.markdown("Operations and their levels")

    topics = []
    for position, operation in enumerate(NUMBER_TYPES[number_type]):
        use_column, level_column = st.columns([1, 2], vertical_alignment="center")
        use = use_column.checkbox(
            operation,
            value=position == 0,
            key=f"tr_use_{number_type}_{operation}",
            persist_state="session",
        )
        level = _pick(
            level_column.segmented_control,
            f"Level for {operation}",
            LEVELS,
            f"tr_level_{number_type}_{operation}",
            label_visibility="collapsed",
            disabled=not use,
        )
        if use:
            topics.append(Topic(number_type, operation, level))
    return number_type, topics


def _pick_special() -> tuple[str, list[Topic]]:
    training = _pick(st.pills, "Training", SPECIAL_TRAININGS, "tr_special")
    st.caption(SPECIAL_NOTES[training])
    level = _pick(st.segmented_control, "Level", LEVELS, "tr_special_level")
    return training, [Topic(SPECIAL, training, level)]


def _pick_mode() -> tuple[str, int]:
    mode = _pick(st.segmented_control, "Mode", [mode.value for mode in Mode], "tr_mode")
    st.caption(MODE_NOTES[mode])
    label, key, value, step = LIMIT_INPUTS[mode]
    low, high = LIMITS[mode]
    limit = st.number_input(
        f"{label} ({low} to {high})",
        min_value=low,
        max_value=high,
        value=value,
        step=step,
        key=key,
        persist_state="session",
    )
    return mode, limit


def _render_example(topics: list[Topic]) -> None:
    if not topics:
        return
    example = generate_task(topics, random.Random(EXAMPLE_SEED))
    with st.container(border=True):
        st.caption(f"Example task · {example.prompt}")
        st.markdown(f"**{example.text}**")


def _render_history() -> None:
    st.subheader("Recent sessions", anchor=False)
    sessions = trainer_db.list_sessions(limit=HISTORY_LENGTH)
    if not sessions:
        st.caption("No finished sessions yet. Sessions you end early are not saved.")
        return
    rows = [
        {
            "Date": saved.finished_at.strftime("%Y-%m-%d"),
            "Training": saved.name,
            "Level": saved.levels,
            "Mode": limit_text(saved.mode, saved.limit),
            "Correct": saved.correct,
            "Wrong": saved.wrong,
            "Skipped": saved.skipped,
            "Time": format_duration(saved.duration_seconds),
        }
        for saved in sessions
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True)


def render_setup() -> None:
    st.header("Trainer", anchor=False)
    st.caption("Practise at your own pace. After a mistake you see how to solve the task.")

    category = _pick(
        st.segmented_control, "Training", CATEGORIES, "tr_category", label_visibility="collapsed"
    )
    if category == OPERATIONS_CATEGORY:
        name, topics = _pick_operation()
    elif category == NUMBER_TYPES_CATEGORY:
        name, topics = _pick_number_type()
    else:
        name, topics = _pick_special()
    _render_example(topics)

    mode, limit = _pick_mode()

    if st.button("Start training", key="tr_start", type="primary"):
        try:
            state.tr_settings = make_settings(category, name, topics, mode, limit)
        except SettingsError as error:  # nothing starts, and the reason is shown
            st.error(str(error))
        else:
            state.tr_phase = "countdown"
            st.rerun()

    _render_history()


# --- Countdown ---


def render_countdown() -> None:
    number = st.empty()
    st.button("Cancel", key="tr_cancel", on_click=_on_cancel_countdown)
    # While this script sleeps, the elements of the previous screen would stay
    # visible below. Empty placeholders overwrite them.
    for _ in range(40):
        st.empty()

    for remaining in range(COUNTDOWN_SECONDS, 0, -1):
        number.header(str(remaining), anchor=False)
        time.sleep(1)

    _begin()
    st.rerun()


# --- Running session ---


@st.fragment(run_every="1s")
def _render_status() -> None:
    """Only this part refreshes every second, so typing is not disturbed."""
    session = state.get("tr_session")
    if session is None:
        return
    now = _utc_now()
    if is_time_up(session, now):
        st.rerun(scope="app")

    settings = session.settings
    task_number = len(session.attempts) + 1
    remaining = remaining_seconds(session, now)
    if settings.mode == Mode.TASK_COUNT:
        shown = {
            "Task": f"{task_number} of {settings.limit}",
            "Time": format_duration(elapsed_seconds(session, now)),
        }
        progress = len(session.attempts) / settings.limit
    elif settings.mode == Mode.TOTAL_TIME:
        shown = {"Time left": format_duration(math.ceil(remaining)), "Task": task_number}
        progress = remaining / settings.limit
    else:
        shown = {"Time left for this task": math.ceil(remaining), "Task": task_number}
        progress = remaining / settings.limit
    shown["Correct"] = session.correct
    shown["Wrong or skipped"] = session.wrong + session.skipped

    for column, (label, value) in zip(st.columns(len(shown)), shown.items()):
        column.metric(label, value)
    st.progress(min(1.0, max(0.0, progress)))


def _render_feedback() -> None:
    """Show how the previous task went. This is where the Trainer teaches."""
    attempt = state.get("tr_feedback")
    if attempt is None:
        return
    if attempt.outcome == Outcome.CORRECT:
        st.success(f"Correct! {attempt.solution}")
    elif attempt.outcome == Outcome.WRONG:
        st.error(
            f"Not quite. You answered **{attempt.given}**, the answer is **{attempt.answer}**."
            f"\n\n{attempt.solution}"
        )
    else:
        st.warning(f"Skipped. The answer is **{attempt.answer}**.\n\n{attempt.solution}")


def _render_flash() -> None:
    color = FLASH_COLORS.get(state.get("tr_flash"))
    if color is None:
        return
    # A new animation name per attempt makes the same colour replay.
    name = f"tr-flash-{state.tr_attempt}"
    st.html(
        f"""<style>
        @keyframes {name} {{
            0%, 60% {{
                background-color: {color};
                border-color: {color};
                box-shadow: 0 0 0 3px {color}, 0 0 18px 6px {color};
            }}
        }}
        .st-key-tr_answer [data-testid="stTextInputRootElement"] {{
            animation: {name} {FLASH_MS}ms ease-out;
        }}
        </style>"""
    )


def _render_focus_script() -> None:
    """Put the cursor back in the answer field. Clicking a button would move it away."""
    st.html(
        f"""<script data-attempt="{state.tr_attempt}">
        requestAnimationFrame(() => {{
            document.querySelector(".st-key-tr_answer input")?.focus();
        }});
        </script>""",
        unsafe_allow_javascript=True,
    )


def render_running() -> None:
    task = state.tr_task
    # The status gets a container of its own. Without it, Streamlit sometimes
    # drops the element that follows a self-refreshing fragment, when the
    # refresh and a submitted answer arrive at the same moment.
    with st.container():
        _render_status()

    st.caption(task.prompt)
    if len(task.text) <= LONG_TASK_LENGTH:
        st.header(task.text, anchor=False)
    else:
        st.subheader(task.text, anchor=False)

    with st.form("tr_answer_form", clear_on_submit=True, border=False):
        st.text_input(
            "Answer", key="tr_answer", autocomplete="off", placeholder=PLACEHOLDERS[task.kind]
        )
        submit_column, skip_column = st.columns(2)
        # Submit comes first, because Enter triggers the first button in a form.
        submit_column.form_submit_button(
            "Submit", key="tr_submit", type="primary", on_click=_on_submit, width="stretch"
        )
        skip_column.form_submit_button(
            "Skip", key="tr_skip", on_click=_on_skip, width="stretch"
        )

    if state.tr_show_hint:
        st.warning(ANSWER_HINTS[task.kind])
    _render_feedback()
    st.button("End training", key="tr_abort", on_click=_on_abort)

    _render_flash()
    _render_focus_script()


# --- Result ---


def _render_review(session: Session) -> None:
    st.subheader("Review", anchor=False)
    if not session.attempts:
        st.caption("No task was answered.")
        return
    rows = [
        {
            "Task": attempt.text,
            "Your answer": attempt.given or NO_VALUE,
            "Correct answer": attempt.answer,
            "Result": RESULT_WORDS[attempt.outcome],
            "Seconds": round(attempt.seconds, 1),
        }
        for attempt in session.attempts
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True)

    missed = [attempt for attempt in session.attempts if attempt.outcome != Outcome.CORRECT]
    if missed:
        st.subheader("How to solve the ones you missed", anchor=False)
        for attempt in missed:
            st.markdown(f"**{attempt.text}**  \n{attempt.solution}")


def render_result() -> None:
    session = state.tr_result["session"]
    unanswered = state.tr_result["unanswered"]
    settings = session.settings
    summary = summarize(session)

    st.header(f"Training finished: {settings.name}", anchor=False)
    st.caption(
        f"{settings.category} · {levels_text(settings)} · "
        f"{limit_text(settings.mode, settings.limit)}"
    )
    st.info(END_MESSAGES[session.end_reason])
    if unanswered is not None:
        st.markdown(f"**Not answered in time:** {unanswered.text}  \n{unanswered.solution}")

    average = summary.average_seconds
    shown = {
        "Correct": summary.correct,
        "Wrong": summary.wrong,
        "Skipped": summary.skipped,
        "Accuracy": _percent(summary.accuracy),
        "Time": format_duration(summary.duration_seconds),
        "Per task": NO_VALUE if average is None else f"{average:.1f} s",
    }
    for column, (label, value) in zip(st.columns(len(shown)), shown.items()):
        column.metric(label, value)

    again_column, change_column = st.columns(2)
    again_column.button(
        "Train again", key="tr_again", type="primary", on_click=_on_train_again, width="stretch"
    )
    change_column.button(
        "Change settings", key="tr_change", on_click=_on_change_settings, width="stretch"
    )

    _render_review(session)


# --- Entry point ---


def render() -> None:
    if "tr_phase" not in state:  # once per browser session
        trainer_db.init_db()
        state.tr_phase = "setup"

    if state.tr_phase == "running":
        session = finish_if_expired(state.tr_session, _utc_now())
        if session.status == Status.FINISHED:
            _finish(session)

    if state.tr_phase == "countdown":
        render_countdown()
    elif state.tr_phase == "running":
        render_running()
    elif state.tr_phase == "result":
        render_result()
    else:
        render_setup()
