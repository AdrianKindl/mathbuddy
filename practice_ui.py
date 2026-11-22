"""The practice flow shared by Knowledge Tricks (knowledge_ui.py) and Textbook
(textbook_ui.py): a round of tasks without a time limit, from the first task to
the result. Streamlit only: no rules and no SQL.

Each screen gives the flow its own rules (start, submit, skip, save) and its own
way to show a task and feedback. The flow keeps its state under its prefix
("kn_" or "tb_"), so the two modes never mix.
"""

import random
import uuid
from collections.abc import Callable
from datetime import datetime, timezone

import streamlit as st

from ui_components import answer_flash, answer_focus, answer_form

FLASH = {"correct": "green", "wrong": "red"}  # outcome values of both rule modules
PRACTICE_SCREENS = ("setup", "running", "result")

state = st.session_state


class Practice:
    def __init__(
        self,
        prefix: str,
        *,
        start_round: Callable,  # (item id, level, random.Random) -> round
        submit_answer: Callable,  # (round, raw text) -> (round, outcome)
        skip_task: Callable,  # (round) -> (round, outcome)
        current_task: Callable,  # (round) -> task or None
        save_round: Callable,  # (round id, round, finished_at) -> None
        item_of: Callable,  # (round) -> item id
        item_screen: str,  # the screen of the trick or article
        back_label: str,  # "Back to trick", "Back to article"
        back_key: str,  # key of that button on the result screen
        show_task: Callable,  # (task) -> None, draws the task
        show_feedback: Callable,  # (attempt) -> None, how the previous task went
        hint: Callable,  # (task) -> text shown for input that is not evaluated
        placeholder: Callable = lambda task: None,
        is_choice: Callable = lambda task: False,
        length: int = 10,
    ) -> None:
        self.prefix = prefix
        self.start_round = start_round
        self.submit_answer = submit_answer
        self.skip_task = skip_task
        self.current_task = current_task
        self.save_round = save_round
        self.item_of = item_of
        self.item_screen = item_screen
        self.back_label = back_label
        self.back_key = back_key
        self.show_task = show_task
        self.show_feedback = show_feedback
        self.hint = hint
        self.placeholder = placeholder
        self.is_choice = is_choice
        self.length = length

    def key(self, name: str) -> str:
        return f"{self.prefix}{name}"

    # --- State ---

    def clear(self) -> None:
        for name in ("round", "round_id", "rng", "flash", "hint", "feedback"):
            state.pop(self.key(name), None)

    def begin(self, item_id: str, level: str) -> None:
        self.clear()
        state.pop(self.key("result"), None)
        state[self.key("rng")] = random.Random()
        state[self.key("round")] = self.start_round(item_id, level, state[self.key("rng")])
        state[self.key("round_id")] = str(uuid.uuid4())
        state[self.key("attempt")] = state.get(self.key("attempt"), 0) + 1
        state[self.key("screen")] = "running"

    def _finish(self, practice_round) -> None:
        """Save the completed round and show the result. Safe to repeat."""
        self.save_round(state[self.key("round_id")], practice_round, datetime.now(timezone.utc))
        state[self.key("result")] = practice_round
        feedback = state.get(self.key("feedback"))
        self.clear()
        state[self.key("feedback")] = feedback  # the result also shows the last task
        state[self.key("screen")] = "result"

    def _apply(self, practice_round, outcome) -> None:
        state[self.key("attempt")] += 1  # the flash and the focus script run again
        state[self.key("round")] = practice_round
        state[self.key("hint")] = outcome == "ignored"
        state[self.key("flash")] = FLASH.get(outcome)
        if outcome != "ignored":
            state[self.key("feedback")] = practice_round.attempts[-1]
        if practice_round.status == "completed":
            self._finish(practice_round)

    def leave(self) -> None:
        """The user switched to another section: a running round is not saved."""
        if self.key("screen") not in state:
            return
        self.clear()
        state.pop(self.key("result"), None)
        if state[self.key("screen")] in PRACTICE_SCREENS:
            state[self.key("screen")] = self.item_screen

    # --- Callbacks ---

    def on_submit(self) -> None:
        self._apply(*self.submit_answer(state[self.key("round")], state[self.key("answer")]))

    def on_choice(self, label: str) -> None:
        self._apply(*self.submit_answer(state[self.key("round")], label))

    def on_skip(self) -> None:
        self._apply(*self.skip_task(state[self.key("round")]))

    def on_leave_round(self) -> None:
        self.clear()  # leaving early saves nothing
        state[self.key("screen")] = self.item_screen

    def on_again(self) -> None:
        result = state[self.key("result")]
        self.begin(self.item_of(result), result.level)

    def on_back_to_item(self) -> None:
        state.pop(self.key("result"), None)
        self.clear()
        state[self.key("screen")] = self.item_screen

    # --- Screens ---

    def _render_feedback(self) -> None:
        attempt = state.get(self.key("feedback"))
        if attempt is not None:
            self.show_feedback(attempt)

    def render_running(self, caption: str) -> None:
        practice_round = state[self.key("round")]
        task = self.current_task(practice_round)
        done = len(practice_round.attempts)

        st.caption(caption)
        st.markdown(f"**Task {done + 1} / {self.length}**")
        st.progress(done / self.length)
        self.show_task(task)

        choice = self.is_choice(task)
        if choice:
            for index, (column, label) in enumerate(zip(st.columns(len(task.choices)),
                                                        task.choices)):  # fmt: skip
                column.button(label, key=self.key(f"choice_{index}"), on_click=self.on_choice,
                              args=(label,), width="stretch")  # fmt: skip
            st.button("Skip", key=self.key("skip"), on_click=self.on_skip)
        else:
            answer_form(self.prefix, self.on_submit, self.on_skip,
                        placeholder=self.placeholder(task))  # fmt: skip

        if state.get(self.key("hint")):
            st.warning(self.hint(task))
        self._render_feedback()
        st.button(self.back_label, key=self.key("leave"), on_click=self.on_leave_round)

        if not choice:  # the flash and the focus belong to the answer field
            attempt = state[self.key("attempt")]
            answer_flash(self.prefix, state.get(self.key("flash")), attempt)
            answer_focus(self.prefix, attempt)

    def render_result(self, title: str) -> None:
        result = state[self.key("result")]
        st.header(title, anchor=False)
        st.caption(f"Level: {result.level}")
        self._render_feedback()

        correct, wrong, skipped = st.columns(3)
        correct.metric("Correct", f"{result.correct} / {self.length}")
        wrong.metric("Wrong", result.wrong)
        skipped.metric("Skipped", result.skipped)

        again, back = st.columns(2)
        again.button("Practise again", key=self.key("again"), type="primary",
                     on_click=self.on_again, width="stretch")  # fmt: skip
        back.button(self.back_label, key=self.back_key, on_click=self.on_back_to_item,
                    width="stretch")  # fmt: skip
