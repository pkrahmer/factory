"""The story format: frontmatter in a fixed order, sections, and the numbered log."""

from __future__ import annotations

from factory import story

TEXT = """---
attempts: 0
stage: doing
pr: 7
---
# Thing

## Acceptance criteria

1. A title is stored.
2. `make check` stays green.
3. docs: none (internal).

## Log (append only)

1. 2026-01-01 human: created.
2. intake: accepted
   - the sections: all present
"""


def test_split_and_render_round_trip_with_the_fields_in_order() -> None:
    meta, body = story.split(TEXT)
    assert meta == {"attempts": 0, "stage": "doing", "pr": 7}
    rendered = story.render(meta, body)
    assert rendered.startswith("---\nstage: doing\npr: 7\nattempts: 0\n---\n# Thing\n")
    assert story.split(rendered) == (meta, body)


def test_update_writes_null_and_keeps_strings_readable() -> None:
    text = story.update(TEXT, blocked=None, comments_seen=2)
    assert "\npr: 7\nblocked: null\ncomments_seen: 2\nattempts: 0\n" in text
    stamped = story.update(TEXT, outcome="2026-10-05T10:00:00Z")
    assert story.split(stamped)[0]["outcome"] == "2026-10-05T10:00:00Z"


def test_a_story_without_frontmatter_gets_one() -> None:
    text = story.update("# Fresh\n\nBody.\n", stage="ready", pr=None)
    assert text == "---\nstage: ready\npr: null\n---\n# Fresh\n\nBody.\n"


def test_acceptance_fields_follow_the_machine_fields() -> None:
    text = story.render({"outcome": "accepted", "stories": ["F0001-S0001"], "stage": "done"}, "")
    assert text.startswith("---\nstage: done\nstories: [F0001-S0001]\noutcome: accepted\n---\n")


def test_entries_ignore_numbered_lists_above_the_log() -> None:
    _, body = story.split(TEXT)
    assert story.entries(body) == [
        (1, "2026-01-01 human: created."),
        (2, "intake: accepted\n- the sections: all present"),
    ]
    assert story.last_entry(body).startswith("intake: accepted")


def test_append_takes_the_next_number_and_indents_continuations() -> None:
    _, body = story.split(TEXT)
    body = story.append(body, "reviewer: two findings\n1. a\n2. b\nverdict: rework")
    assert body.endswith(
        "2. intake: accepted\n   - the sections: all present\n"
        "3. reviewer: two findings\n   1. a\n   2. b\n   verdict: rework\n"
    )
    assert story.entries(body)[-1] == (3, "reviewer: two findings\n1. a\n2. b\nverdict: rework")


def test_append_from_entry_nine_to_ten_widens_the_indent() -> None:
    body = "## Log (append only)\n\n" + "".join(f"{n}. e{n}\n" for n in range(1, 10))
    body = story.append(body, "ten\nmore")
    assert body.endswith("9. e9\n10. ten\n    more\n")


def test_append_before_a_later_section_and_into_a_missing_log() -> None:
    body = "## Log (append only)\n\n1. first\n\n## Later\n\ntext\n"
    assert story.append(body, "second") == (
        "## Log (append only)\n\n1. first\n2. second\n\n## Later\n\ntext\n"
    )
    assert story.append("# T\n", "first") == "# T\n\n## Log (append only)\n\n1. first\n"
    assert story.append("## Log (append only)\n", "first") == "## Log (append only)\n\n1. first\n"


def test_section_and_insert_under_a_heading() -> None:
    _, body = story.split(TEXT)
    assert story.section(body, "Acceptance criteria").startswith("1. A title is stored.")
    assert story.section(body, "Missing") == ""
    report = "## Verdict\n\naccepted with drafts\n\n## 1 Scope\n"
    assert story.insert_under(report, "Verdict", "Refused: no.") == (
        "## Verdict\n\nRefused: no.\n\naccepted with drafts\n\n## 1 Scope\n"
    )


def test_with_log_keeps_the_sections_and_takes_the_log_from_the_source() -> None:
    worked = "# T\n\n## Assignment\n\nnew\n\n## Log (append only)\n\n1. a\n2. mine\n"
    source = "# T\n\n## Assignment\n\nold\n\n## Log (append only)\n\n1. a\n"
    assert story.with_log(worked, source) == (
        "# T\n\n## Assignment\n\nnew\n\n## Log (append only)\n\n1. a\n"
    )
    later = "## Log (append only)\n\n1. x\n\n## After\n\ntext\n"
    assert story.with_log(later, source) == ("## Log (append only)\n\n1. a\n\n## After\n\ntext\n")
    assert story.with_log("# T\n", source) == "# T\n\n## Log (append only)\n\n1. a\n"
