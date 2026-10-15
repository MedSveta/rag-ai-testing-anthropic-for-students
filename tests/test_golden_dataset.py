"""Проверка самого golden dataset: правильно ли заполнен файл.

Сервер для этих тестов не нужен — они читают только JSON и базу знаний.
"""

import re

import pytest

from tests.golden import PROJECT_ROOT, load_golden_cases

REQUIRED_FIELDS = {
    "id",
    "question",
    "knowledge_status",
    "expected_requirement_ids",
    "expected_answer",
    "expected_contains",
}
ALLOWED_STATUSES = {"known", "missing", "off_topic"}

CASES = load_golden_cases()


def requirement_ids_in_knowledge_base():
    """Все ID требований, которые есть в базе знаний: {"T1", "T2", ..., "F14"}."""
    text = (PROJECT_ROOT / "knowledge" / "requirements.md").read_text(encoding="utf-8")
    return set(re.findall(r"\*\*([TF]\d+)\*\*", text))


def test_dataset_is_not_empty():
    assert len(CASES) > 0


def test_case_ids_are_unique():
    ids = [case["id"] for case in CASES]
    duplicates = {case_id for case_id in ids if ids.count(case_id) > 1}

    assert not duplicates, f"Повторяющиеся id: {duplicates}"


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_case_has_required_fields(case):
    missing = REQUIRED_FIELDS - set(case)

    assert not missing, f"Не хватает полей: {missing}"


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_case_has_valid_status(case):
    assert case["knowledge_status"] in ALLOWED_STATUSES


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_question_is_not_blank(case):
    assert case["question"].strip()


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_known_case_has_expected_ids_and_others_do_not(case):
    if case["knowledge_status"] == "known":
        assert case["expected_requirement_ids"], "У known-случая должны быть ожидаемые ID"
    else:
        assert case["expected_requirement_ids"] == [], "У missing/off_topic не должно быть ожидаемых ID"


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_expected_ids_exist_in_knowledge_base(case):
    unknown = set(case["expected_requirement_ids"]) - requirement_ids_in_knowledge_base()

    assert not unknown, f"Таких требований нет в базе знаний: {unknown}"


def test_dataset_covers_all_statuses():
    statuses = {case["knowledge_status"] for case in CASES}

    assert statuses == ALLOWED_STATUSES
