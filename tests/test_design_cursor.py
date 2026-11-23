"""Spec 017: the stylesheet carries our own glove cursor, with fallbacks and the I-beam in fields."""

import re
import xml.etree.ElementTree as ET
from urllib.parse import unquote

import design

CURSOR_URL = re.compile(r'url\("data:image/svg\+xml,([^"]+)"\)\s+(\d+)\s+(\d+),\s*(\w+)')


def cursors() -> list[tuple[str, int, int, str]]:
    """Every SVG cursor in the stylesheet: (decoded svg, hotspot x, hotspot y, fallback)."""
    found = CURSOR_URL.findall(design.stylesheet())
    return [(unquote(svg), int(x), int(y), fallback) for svg, x, y, fallback in found]


def test_there_is_a_normal_and_a_clickable_glove():
    css = design.stylesheet()
    assert re.search(r"--mb-cursor-hand:\s*url\(", css)
    assert re.search(r"--mb-cursor-click:\s*url\(", css)
    assert len(cursors()) == 2


def test_each_glove_has_a_standard_fallback_cursor():
    assert sorted(fallback for *_, fallback in cursors()) == ["auto", "pointer"]


def test_gloves_are_small_valid_svgs_in_our_purple():
    for svg, x, y, _ in cursors():
        root = ET.fromstring(svg)
        assert root.tag.endswith("svg")
        assert int(root.get("width")) <= 32 and int(root.get("height")) <= 32
        assert 0 <= x < 32 and 0 <= y < 32  # the hotspot lies inside the image
        assert "#5b36f0" in svg.lower()


def test_the_glove_is_used_everywhere_and_on_clickable_things():
    css = design.stylesheet()
    assert re.search(r"\.stApp \*\s*\{\s*cursor: var\(--mb-cursor-hand\)", css)
    assert re.search(r"\(button, a\[href\][^{]*\{\s*cursor: var\(--mb-cursor-click\)", css)


def test_typing_fields_keep_the_text_cursor():
    css = design.stylesheet()
    assert re.search(r"input:not\(\[type=\"checkbox\"\]\)[^{]*textarea\)\s*\{\s*cursor: text;", css)
