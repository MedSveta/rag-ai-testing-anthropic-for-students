import pytest

from app.chunker import CHUNKER_VERSION, Chunk, MarkdownSectionChunker, _slug
from tests.conftest import KNOWLEDGE_FILE


# ---------- _slug ----------

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Password Requirements", "password-requirements"),
        ("New Contact — Phone Number", "new-contact-phone-number"),
        ("  --Hello!!World--  ", "hello-world"),
        ("", "section"),
        ("   ", "section"),
        ("— — —", "section"),
    ],
)
def test_slug(value, expected):
    assert _slug(value) == expected


def test_slug_is_limited_to_90_characters():
    assert len(_slug("a" * 200)) == 90


# ---------- constructor validation ----------

def test_default_parameters():
    chunker = MarkdownSectionChunker()
    assert chunker.max_chars == 1800
    assert chunker.overlap_chars == 180


@pytest.mark.parametrize(
    ("max_chars", "overlap_chars"),
    [(199, 0), (200, 200), (500, 600), (500, -1)],
)
def test_invalid_parameters_are_rejected(max_chars, overlap_chars):
    with pytest.raises(ValueError):
        MarkdownSectionChunker(max_chars=max_chars, overlap_chars=overlap_chars)


@pytest.mark.parametrize(("max_chars", "overlap_chars"), [(200, 0), (200, 199)])
def test_boundary_parameters_are_accepted(max_chars, overlap_chars):
    MarkdownSectionChunker(max_chars=max_chars, overlap_chars=overlap_chars)


# ---------- requirement chunks ----------

def test_requirement_line_becomes_atomic_chunk():
    markdown = "# Password\n- **T14** — Password must have minimum 8 symbols\n"
    chunks = MarkdownSectionChunker().chunk(markdown, source="kb.md")

    assert chunks == [
        Chunk(
            id="t14-password",
            text="Section: Password\nRequirement T14: Password must have minimum 8 symbols",
            source="kb.md",
            section="Password",
            requirement_ids=("T14",),
        )
    ]


def test_each_requirement_gets_its_own_chunk():
    markdown = (
        "# Password\n"
        "- **T14** — Minimum 8 symbols\n"
        "- **T15** — Maximum 15 symbols\n"
        "- **F8** — Error is displayed\n"
    )
    chunks = MarkdownSectionChunker().chunk(markdown)

    assert [c.requirement_ids for c in chunks] == [("T14",), ("T15",), ("F8",)]
    assert [c.id for c in chunks] == ["t14-password", "t15-password", "f8-password"]


@pytest.mark.parametrize(
    "line",
    [
        "- **T1** — Email is required",
        "- **T1** - Email is required",
        "  -   **T1**   —   Email is required  ",
        "- **t1** — Email is required",
    ],
)
def test_requirement_line_formats(line):
    chunks = MarkdownSectionChunker().chunk(f"# Email\n{line}\n")
    assert len(chunks) == 1
    assert chunks[0].requirement_ids == ("T1",)
    assert chunks[0].text.endswith("Requirement T1: Email is required")


def test_requirement_without_bold_is_treated_as_prose():
    chunks = MarkdownSectionChunker().chunk("# Email\n- T1 — Email is required\n")
    assert len(chunks) == 1
    assert chunks[0].id == "email-001"
    assert chunks[0].requirement_ids == ("T1",)


def test_requirement_id_uses_leaf_heading_but_text_uses_full_path():
    markdown = "# Technical\n## Phone Number\n- **T41** — Minimum 10 symbols\n"
    chunk = MarkdownSectionChunker().chunk(markdown)[0]

    assert chunk.id == "t41-phone-number"
    assert chunk.section == "Technical > Phone Number"
    assert chunk.text.startswith("Section: Technical > Phone Number\n")


# ---------- sections and prose ----------

def test_text_before_first_heading_goes_to_document_overview():
    chunks = MarkdownSectionChunker().chunk("Intro text.\n# Next\nMore.")
    assert chunks[0].section == "Document Overview"
    assert "Intro text." in chunks[0].text


def test_heading_path_is_rebuilt_when_level_goes_up():
    markdown = "# A\n## B\n### C\nc text\n## D\nd text\n# E\ne text\n"
    sections = [c.section for c in MarkdownSectionChunker().chunk(markdown)]
    assert sections == ["A > B > C", "A > D", "E"]


def test_prose_chunk_ids_are_numbered_across_document():
    markdown = "# A\nfirst\n# B\nsecond\n"
    ids = [c.id for c in MarkdownSectionChunker().chunk(markdown)]
    assert ids == ["a-001", "b-002"]


def test_prose_collects_requirement_ids_without_duplicates():
    markdown = "# Notes\nSee T5 and F2, and T5 again. Not T5x.\n"
    chunk = MarkdownSectionChunker().chunk(markdown)[0]
    assert chunk.requirement_ids == ("T5", "F2")


def test_section_with_requirements_and_prose_produces_both():
    markdown = "# Phone\nIntro about phones.\n- **T41** — Minimum 10\n"
    chunks = MarkdownSectionChunker().chunk(markdown)
    assert [c.id for c in chunks] == ["t41-phone", "phone-001"]
    assert "T41" not in chunks[1].text


def test_heading_only_sections_produce_no_chunks():
    assert MarkdownSectionChunker().chunk("# A\n## B\n") == []


def test_empty_document_produces_no_chunks():
    assert MarkdownSectionChunker().chunk("") == []


# ---------- skipped training sections ----------

def test_skip_section_excludes_entire_subtree():
    markdown = """# Product
Text.

# Suggested RAG Test Questions
Do not index.

## Password
How often must a password be changed?

### More
Still test data.

# Real Knowledge
- **T1** — Customer email is required
"""
    chunks = MarkdownSectionChunker().chunk(markdown)
    joined = "\n".join(chunk.text for chunk in chunks)

    assert "Do not index" not in joined
    assert "How often" not in joined
    assert "Still test data" not in joined
    assert "Suggested RAG Test Questions" not in joined
    assert "T1" in joined


def test_skipped_nested_section_ends_at_same_level_heading():
    markdown = (
        "# Product\n"
        "## Suggested RAG Test Questions\nhidden\n"
        "### Deep\nhidden too\n"
        "## Visible\nshown\n"
    )
    chunks = MarkdownSectionChunker().chunk(markdown)
    assert [c.section for c in chunks] == ["Product > Visible"]


# ---------- _clean_prose ----------

def test_clean_prose_removes_separators_and_collapses_blank_lines():
    lines = ["", "first  ", "---", "", "", "", "second", "", ""]
    assert MarkdownSectionChunker._clean_prose(lines) == "first\n\nsecond"


def test_clean_prose_keeps_markdown_bullets_and_quotes():
    lines = ["- item", "> quote"]
    assert MarkdownSectionChunker._clean_prose(lines) == "- item\n> quote"


def test_clean_prose_of_only_blank_lines_is_empty():
    assert MarkdownSectionChunker._clean_prose(["", "  ", "---"]) == ""


# ---------- _split_long ----------

def test_split_long_keeps_short_text_whole():
    chunker = MarkdownSectionChunker(max_chars=200, overlap_chars=0)
    assert chunker._split_long("short") == ["short"]


def test_split_long_text_exactly_max_chars_is_not_split():
    chunker = MarkdownSectionChunker(max_chars=200, overlap_chars=0)
    text = "x" * 200
    assert chunker._split_long(text) == [text]


def test_split_long_splits_on_paragraphs_without_overlap():
    chunker = MarkdownSectionChunker(max_chars=200, overlap_chars=0)
    paragraphs = ["a" * 150, "b" * 150, "c" * 150]
    parts = chunker._split_long("\n\n".join(paragraphs))
    assert parts == paragraphs


def test_split_long_adds_overlap_from_previous_part():
    chunker = MarkdownSectionChunker(max_chars=200, overlap_chars=10)
    parts = chunker._split_long("a" * 150 + "\n\n" + "b" * 150)

    assert len(parts) == 2
    assert parts[0] == "a" * 150
    assert parts[1] == "a" * 10 + "\n\n" + "b" * 150


def test_long_section_produces_several_prose_chunks_with_same_section():
    chunker = MarkdownSectionChunker(max_chars=200, overlap_chars=0)
    markdown = "# Long\n" + "\n\n".join(["word " * 30] * 3)
    chunks = chunker.chunk(markdown)

    assert len(chunks) > 1
    assert {c.section for c in chunks} == {"Long"}
    assert [c.id for c in chunks] == [f"long-{i:03d}" for i in range(1, len(chunks) + 1)]


# ---------- load() ----------

def test_load_uses_file_name_as_source(tmp_path):
    path = tmp_path / "custom.md"
    path.write_text("# A\n- **T1** — Text\n", encoding="utf-8")
    chunks = MarkdownSectionChunker().load(path)
    assert chunks[0].source == "custom.md"


def test_load_reads_utf8(tmp_path):
    path = tmp_path / "kb.md"
    path.write_text("# Пароль\nМинимум 8 символов — обязательно\n", encoding="utf-8")
    chunks = MarkdownSectionChunker().load(path)
    assert "Минимум 8 символов" in chunks[0].text


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        MarkdownSectionChunker().load(tmp_path / "missing.md")


# ---------- real knowledge base ----------

def test_real_knowledge_base_has_no_training_question_leakage():
    chunks = MarkdownSectionChunker().load(KNOWLEDGE_FILE)
    joined = "\n".join(chunk.text for chunk in chunks)

    assert chunks
    assert "Suggested RAG Test Questions" not in joined
    assert "How often must a password be changed?" not in joined
    assert "two-factor authentication" not in joined.lower()


def test_real_knowledge_base_requirement_chunks_are_atomic():
    chunks = MarkdownSectionChunker().load(KNOWLEDGE_FILE)
    t14 = [chunk for chunk in chunks if chunk.requirement_ids == ("T14",)]
    t15 = [chunk for chunk in chunks if chunk.requirement_ids == ("T15",)]

    assert len(t14) == 1
    assert len(t15) == 1
    assert "minimum 8" in t14[0].text.lower()
    assert "maximum 15" in t15[0].text.lower()
    assert t14[0].id.startswith("t14-")
    assert t15[0].id.startswith("t15-")


def test_real_knowledge_base_chunk_ids_are_unique():
    chunks = MarkdownSectionChunker().load(KNOWLEDGE_FILE)
    ids = [chunk.id for chunk in chunks]
    assert len(ids) == len(set(ids))


def test_chunker_version_is_defined():
    assert CHUNKER_VERSION
