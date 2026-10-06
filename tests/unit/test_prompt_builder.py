from app.prompt_builder import MISSING_INFORMATION_ANSWER, SYSTEM_PROMPT, build_user_prompt
from tests.conftest import make_context


# ---------- SYSTEM_PROMPT ----------

def test_system_prompt_contains_exact_missing_information_answer():
    assert f'"{MISSING_INFORMATION_ANSWER}"' in SYSTEM_PROMPT


def test_system_prompt_requires_context_only_and_citations():
    assert "ONLY from the context" in SYSTEM_PROMPT
    assert "Never invent a product requirement" in SYSTEM_PROMPT
    assert "square brackets" in SYSTEM_PROMPT


def test_missing_information_answer_text():
    assert MISSING_INFORMATION_ANSWER == "The information is not specified in the knowledge base."


# ---------- build_user_prompt ----------

def test_prompt_contains_context_and_question():
    prompt = build_user_prompt(
        "What is the maximum password length?",
        [make_context("T15 Password maximum is 15 symbols.")],
    )
    assert "T15" in prompt
    assert "15 symbols" in prompt
    assert "What is the maximum password length?" in prompt


def test_prompt_exact_structure_for_one_context():
    context = make_context(
        "Requirement T15: Max 15",
        source="requirements.md",
        section="Password",
        requirement_ids=("T15",),
    )
    assert build_user_prompt("Max?", [context]) == (
        "<context>\n"
        '<document index="1" source="requirements.md" section="Password" '
        'requirement_ids="T15">\n'
        "Requirement T15: Max 15\n"
        "</document>\n"
        "</context>\n\n"
        "<question>\n"
        "Max?\n"
        "</question>"
    )


def test_documents_are_numbered_from_one_in_given_order():
    contexts = [make_context("first"), make_context("second"), make_context("third")]
    prompt = build_user_prompt("q", contexts)

    assert prompt.index('index="1"') < prompt.index("first")
    assert prompt.index('index="2"') < prompt.index("second")
    assert prompt.index('index="3"') < prompt.index("third")
    assert 'index="4"' not in prompt


def test_documents_are_separated_by_blank_line():
    prompt = build_user_prompt("q", [make_context("a"), make_context("b")])
    assert "</document>\n\n<document" in prompt


def test_multiple_requirement_ids_are_comma_separated():
    prompt = build_user_prompt("q", [make_context(requirement_ids=("T41", "T42"))])
    assert 'requirement_ids="T41, T42"' in prompt


def test_missing_requirement_ids_are_marked_none():
    prompt = build_user_prompt("q", [make_context(requirement_ids=())])
    assert 'requirement_ids="none"' in prompt


def test_empty_context_list_still_builds_prompt():
    assert build_user_prompt("q", []) == "<context>\n\n</context>\n\n<question>\nq\n</question>"


def test_question_is_stripped():
    prompt = build_user_prompt("   Max length?  \n", [make_context()])
    assert "<question>\nMax length?\n</question>" in prompt


def test_special_characters_in_text_and_question_are_escaped():
    prompt = build_user_prompt(
        "Is <b> & </question> allowed?",
        [make_context("Use <script> & stuff")],
    )
    assert "Use &lt;script&gt; &amp; stuff" in prompt
    assert "Is &lt;b&gt; &amp; &lt;/question&gt; allowed?" in prompt
    assert prompt.count("</question>") == 1


def test_special_characters_in_attributes_are_escaped():
    prompt = build_user_prompt("q", [make_context(section="A & B <C>", source="a<b>.md")])
    assert 'section="A &amp; B &lt;C&gt;"' in prompt
    assert 'source="a&lt;b&gt;.md"' in prompt
