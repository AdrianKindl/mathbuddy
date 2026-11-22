"""Knowledge, Textbook mode: Streamlit screens only (spec 010).

knowledge_ui.py calls `render()` when the Tricks / Textbook toggle is on
Textbook, and `leave()` when the user switches section. Content is in
textbook_content.py, the rules in textbook.py, the storage in textbook_db.py.
The practice round runs in the flow shared with Tricks (practice_ui.py).
Everything this file keeps in st.session_state starts with "tb_".
"""

from collections.abc import Callable

import pandas as pd
import streamlit as st

import activity_db
import textbook_db
from knowledge_content import category_of as trick_category_of
from knowledge_content import get_trick
from practice_ui import Practice
from stats import Kind
from tasks import LEVELS
from textbook import (
    ROUND_LENGTH,
    AnswerType,
    Outcome,
    answer_text,
    current_task,
    neighbours,
    position,
    practised,
    skip_task,
    start_round,
    submit_answer,
)
from textbook_content import CATEGORIES, Article, category_of, get_article, get_category
from ui_components import (
    back_button,
    card_header,
    list_rows,
    pick,
    previous_next_bar,
    tile_grid,
)

DESCRIPTION = (
    "Short articles that explain the background behind mental math, "
    "with worked examples and reference tables."
)
PRACTICE_NOTE = f"{ROUND_LENGTH} tasks for this article, no time limit."
HINTS = {
    AnswerType.WHOLE: "Whole numbers only, e.g. -12",
    AnswerType.DECIMAL: "Numbers only, e.g. 66.7",
    AnswerType.ESTIMATE: "A whole number, e.g. 90",
    AnswerType.CHOICE: "Choose one of the buttons",
}
PLACEHOLDERS = {
    AnswerType.WHOLE: "Whole number",
    AnswerType.DECIMAL: "Number, e.g. 66.7",
    AnswerType.ESTIMATE: "Your estimate",
}

state = st.session_state


def _shown(text: str) -> str:
    """Text as Streamlit markdown shows it literally: a "$" would start maths."""
    return text.replace("$", r"\$")


# --- Changing screens ---


def _go(screen: str) -> None:
    state.tb_screen = screen


def _open_category(category_id: str) -> None:
    state.tb_category = category_id
    state.tb_screen = "category"


def _open_article(article_id: str) -> None:
    state.tb_article = article_id
    state.tb_category = category_of(article_id).id
    state.tb_screen = "article"


# --- Practice (stage 2), in the flow shared with Tricks ---


def _show_feedback(attempt) -> None:
    """How the previous task went. After a wrong answer or skip, the answer is shown (T R8)."""
    task = attempt.task
    right = _shown(answer_text(task))
    if attempt.outcome == Outcome.CORRECT:
        st.success(f"Correct! The answer is {right}.")
    elif attempt.outcome == Outcome.WRONG:
        st.error(f"Not quite. You answered {_shown(attempt.given)}. The answer is {right}.")
    else:
        st.warning(f"Skipped. The answer is {right}.")



def save_owned_round(round_id, practice_round, finished_at) -> None:
    """Save the completed round and record the signed in player (spec 012)."""
    textbook_db.save_round(round_id, practice_round, finished_at)
    activity_db.assign_owner(Kind.TEXTBOOK, round_id, state.user.id)


PRACTICE = Practice(
    "tb_",
    start_round=start_round,
    submit_answer=submit_answer,
    skip_task=skip_task,
    current_task=current_task,
    save_round=save_owned_round,
    item_of=lambda practice_round: practice_round.article_id,
    item_screen="article",
    back_label="Back to article",
    back_key="tb_to_article",
    show_task=lambda task: st.subheader(task.prompt, anchor=False),
    show_feedback=_show_feedback,
    hint=lambda task: HINTS[task.kind],
    placeholder=lambda task: PLACEHOLDERS.get(task.kind),
    is_choice=lambda task: task.kind == AnswerType.CHOICE,
    length=ROUND_LENGTH,
)


def leave() -> None:
    """The user switched to another section: a running round is not saved (T R9)."""
    PRACTICE.leave()


def _on_start() -> None:
    PRACTICE.begin(state.tb_article, state.get("tb_level") or LEVELS[0])


# --- Screens ---


def render_overview() -> None:
    st.header("Textbook", anchor=False)
    st.caption(DESCRIPTION)
    tile_grid(
        [
            (f"{category.name} ({len(category.articles)})", f"tb_category_{category.id}",
             (category.id,))
            for category in CATEGORIES
        ],
        _open_category,
    )  # fmt: skip


def render_category() -> None:
    category = get_category(state.tb_category)
    back_button("tb_back", _go, ("overview",))
    st.header(category.name, anchor=False)
    done = practised(textbook_db.list_rounds())
    list_rows(
        [
            (f"{article.name} · {article.difficulty}{' ✓' if article.id in done else ''}",
             f"tb_article_{article.id}", (article.id,))
            for article in category.articles
        ],
        _open_article,
    )  # fmt: skip


def _render_body(article: Article) -> None:
    if len(article.body) == 1:
        st.markdown(_shown(article.body[0]))
    else:
        st.markdown("\n".join(f"- {_shown(item)}" for item in article.body))


def _render_table(article: Article) -> None:
    table = article.table
    with st.container(border=True):
        st.markdown(f"**{_shown(table.title)}**")
        st.caption(_shown(table.subtitle))
        frame = pd.DataFrame(list(table.rows), columns=list(table.columns))
        frame.index = [""] * len(frame)  # no row numbers next to the table
        st.table(frame)


def _render_related(article: Article, on_open_trick: Callable[[str], None]) -> None:
    st.subheader("Related tricks", anchor=False)
    for trick_id in article.related:
        trick = get_trick(trick_id)
        st.button(
            f"{trick.name} ({trick_category_of(trick_id).name})",
            key=f"tb_trick_{trick_id}",
            on_click=on_open_trick,
            args=(trick_id,),
        )


def render_article(on_open_trick: Callable[[str], None]) -> None:
    article = get_article(state.tb_article)
    category = category_of(article.id)
    back_button("tb_back", _go, ("category",))
    st.header(article.name, anchor=False)

    st.subheader("Overview", anchor=False)
    st.markdown(_shown(article.overview))

    with st.container(border=True):
        card_header(article.card_title, category.name, article.difficulty)
        _render_body(article)

    if article.note:
        st.info(_shown(article.note))

    if article.examples:
        st.subheader("Examples", anchor=False)
        for example in article.examples:
            with st.container(border=True):
                st.markdown(f"**{_shown(example.title)}**")
                st.markdown("  \n".join(_shown(line) for line in example.lines))

    if article.table:
        _render_table(article)

    if article.related:
        _render_related(article, on_open_trick)

    previous_next_bar("tb_", *neighbours(article.id), *position(article.id), _open_article)
    st.button("Practice", key="tb_practice", type="primary", on_click=_go, args=("setup",),
              width="stretch")  # fmt: skip


def render_setup() -> None:
    article = get_article(state.tb_article)
    back_button("tb_back", _go, ("article",))
    st.header(f"Practise: {article.name}", anchor=False)
    st.caption(PRACTICE_NOTE)
    pick(st.segmented_control, "Level", LEVELS, "tb_level")
    st.button("Start", key="tb_start", type="primary", on_click=_on_start)


def render_running() -> None:
    practice_round = state.tb_round
    name = get_article(practice_round.article_id).name
    PRACTICE.render_running(f"{name} · {practice_round.level}")


def render_result() -> None:
    PRACTICE.render_result(f"Practice finished: {get_article(state.tb_result.article_id).name}")


def render(on_open_trick: Callable[[str], None]) -> None:
    """`on_open_trick` switches to Tricks mode and opens the given trick."""
    if "tb_screen" not in state:  # once per browser session
        textbook_db.init_db()
        state.tb_screen = "overview"
        state.tb_attempt = 0

    if state.tb_screen == "running" and "tb_round" not in state:
        state.tb_screen = "article"  # nothing to continue
    screen = state.tb_screen
    if screen == "article":
        render_article(on_open_trick)
    elif screen == "category":
        render_category()
    elif screen == "setup":
        render_setup()
    elif screen == "running":
        render_running()
    elif screen == "result":
        render_result()
    else:
        render_overview()
