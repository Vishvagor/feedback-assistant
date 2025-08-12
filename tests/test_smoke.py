from src.pipeline import analyze_text_block

def test_smoke():
    themes, sent, acts = analyze_text_block("""
    The new UI is great but the dashboard is slow.
    Support was helpful. Export feature has a bug.
    Onboarding is confusing; docs unclear.
    """)
    assert isinstance(themes, str)
    assert isinstance(sent, str)
    assert isinstance(acts, str)
