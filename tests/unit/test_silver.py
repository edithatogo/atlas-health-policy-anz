from australian_health_policy_atlas.silver import normalize_html, normalize_text


def test_html_ignores_script_and_preserves_blocks() -> None:
    segments = normalize_html(
        "x", "<h1>Title</h1><script>bad()</script><p>Must act.</p>"
    )
    assert [item.text for item in segments] == ["Title", "Must act."]


def test_text_normalization_is_deterministic() -> None:
    one = normalize_text("x", "A\n\nB")
    two = normalize_text("x", "A\n\nB")
    assert one == two
