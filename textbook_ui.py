"""Knowledge, Textbook mode: Streamlit screens only (spec 010, stage 1).

knowledge_ui.py calls `render()` when the Tricks / Textbook toggle is on
Textbook. Content is in textbook_content.py, navigation in textbook.py.
Everything this file keeps in st.session_state starts with "tb_".
"""

from collections.abc import Callable

import pandas as pd
import streamlit as st

from knowledge_content import category_of as trick_category_of
from knowledge_content import get_trick
from textbook import neighbours, position
from textbook_content import CATEGORIES, Article, category_of, get_article, get_category
from ui_components import back_button, card_header, list_rows, previous_next_bar, tile_grid

DESCRIPTION = (
    "Short articles that explain the background behind mental math, "
    "with worked examples and reference tables."
)

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
    list_rows(
        [
            (f"{article.name} · {article.difficulty}", f"tb_article_{article.id}",
             (article.id,))
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
    # Practice comes in stage 2 of spec 010.
    st.button("Practice", key="tb_practice", type="primary", disabled=True, width="stretch",
              help="Practice for articles is coming soon.")  # fmt: skip


def render(on_open_trick: Callable[[str], None]) -> None:
    """`on_open_trick` switches to Tricks mode and opens the given trick."""
    if "tb_screen" not in state:
        state.tb_screen = "overview"

    if state.tb_screen == "article":
        render_article(on_open_trick)
    elif state.tb_screen == "category":
        render_category()
    else:
        render_overview()
