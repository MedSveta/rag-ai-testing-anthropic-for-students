"""Загрузка golden dataset — эталонного набора вопросов и ожидаемых ответов.

Данные лежат в test_data/golden_dataset.json, код тестов их только читает.
"""

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_DATASET = PROJECT_ROOT / "test_data" / "golden_dataset.json"


def load_golden_cases():
    """Прочитать все случаи из JSON-файла и вернуть список словарей."""
    with open(GOLDEN_DATASET, encoding="utf-8") as file:
        return json.load(file)


def golden_params(knowledge_status):
    """Случаи с нужным статусом в виде pytest.param — готово для parametrize.

    Если у случая есть поле known_issue, тест помечается как xfail.
    """
    params = []
    for case in load_golden_cases():
        if case["knowledge_status"] != knowledge_status:
            continue
        marks = []
        if "known_issue" in case:
            marks.append(pytest.mark.xfail(reason=case["known_issue"], strict=False))
        params.append(pytest.param(case, id=case["id"], marks=marks))
    return params
