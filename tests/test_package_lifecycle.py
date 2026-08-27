from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_readme_states_the_publication_decision_and_entry_conditions() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "**Package lifecycle:** source-installable candidate only." in readme
    assert "demonstrated user demand" in readme
    assert "name-availability check" in readme
    assert "compatibility tests" in readme
