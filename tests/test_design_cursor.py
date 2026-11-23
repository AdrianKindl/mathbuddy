"""Spec 017: the stylesheet carries our own cursors, with fallbacks and the I-beam in fields."""

import re
import xml.etree.ElementTree as ET
from urllib.parse import unquote

import design

CURSOR_URL = re.compile(r'url\("data:image/svg\+xml,([^"]+)"\)\s+(\d+)\s+(\d+),\s*(\w+)')


def cursors() -> list[tuple[str, int, int, str]]:
    """Every SVG cursor in the stylesheet: (decoded svg, hotspot x, hotspot y, fallback)."""
    found = CURSOR_URL.findall(design.stylesheet())
    return [(unquote(svg), int(x), int(y), fallback) for svg, x, y, fallback in found]


def test_there_is_a_normal_and_a_clickable_cursor():
    css = design.stylesheet()
    assert re.search(r"--mb-cursor-hand:\s*url\(", css)
    assert re.search(r"--mb-cursor-click:\s*url\(", css)
    assert len(cursors()) == 2


def test_each_cursor_has_a_standard_fallback_cursor():
    assert sorted(fallback for *_, fallback in cursors()) == ["auto", "pointer"]


def test_both_hotspots_sit_at_the_tip():
    assert [(x, y) for _, x, y, _ in cursors()] == [(7, 6), (7, 6)]


def test_cursors_are_small_valid_svgs_in_our_purple():
    for svg, x, y, _ in cursors():
        root = ET.fromstring(svg)
        assert root.tag.endswith("svg")
        assert int(root.get("width")) <= 32 and int(root.get("height")) <= 32
        assert 0 <= x < 32 and 0 <= y < 32  # the hotspot lies inside the image
        assert re.search(r"#(6c47ff|5b2fff)", svg.lower())


def test_the_cursors_are_used_everywhere_and_on_clickable_things():
    css = design.stylesheet()
    assert re.search(r"\.stApp \*\s*\{\s*cursor: var\(--mb-cursor-hand\)", css)
    assert re.search(r"\(button, a\[href\][^{]*\{\s*cursor: var\(--mb-cursor-click\)", css)


def test_typing_fields_keep_the_text_cursor():
    css = design.stylesheet()
    assert re.search(r"input:not\(\[type=\"checkbox\"\]\)[^{]*textarea\)\s*\{\s*cursor: text;", css)
