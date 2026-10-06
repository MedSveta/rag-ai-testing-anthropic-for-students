from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import PROJECT_ROOT, Settings, get_settings


def test_project_root_points_to_repository_root():
    assert (PROJECT_ROOT / "app" / "config.py").exists()
    assert (PROJECT_ROOT / "pyproject.toml").exists()


def test_defaults_without_env_file():
    settings = Settings(_env_file=None)

    assert settings.anthropic_api_key is None
    assert settings.anthropic_model == "claude-sonnet-5"
    assert settings.max_output_tokens == 700
    assert settings.knowledge_path == "knowledge/requirements.md"
    assert settings.chroma_path == ".chroma"
    assert settings.chroma_collection == "phonebook_requirements"
    assert settings.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
    assert settings.top_k == 4
    assert settings.min_relevance_score == 0.35
    assert settings.auto_index is True
    assert settings.anthropic_input_cost_per_million == 0.0
    assert settings.anthropic_output_cost_per_million == 0.0


def test_environment_variables_override_defaults(monkeypatch):
    monkeypatch.setenv("TOP_K", "7")
    monkeypatch.setenv("MIN_RELEVANCE_SCORE", "0.5")
    monkeypatch.setenv("AUTO_INDEX", "false")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-test")

    settings = Settings(_env_file=None)

    assert settings.top_k == 7
    assert settings.min_relevance_score == 0.5
    assert settings.auto_index is False
    assert settings.anthropic_model == "claude-test"


def test_environment_variable_names_are_case_insensitive(monkeypatch):
    monkeypatch.setenv("top_k", "9")
    assert Settings(_env_file=None).top_k == 9


def test_values_are_read_from_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("TOP_K=6\nANTHROPIC_API_KEY=file-key\nUNKNOWN_SETTING=x\n", encoding="utf-8")

    settings = Settings(_env_file=env_file)

    assert settings.top_k == 6
    assert settings.anthropic_api_key == "file-key"
    assert not hasattr(settings, "unknown_setting")


def test_environment_variable_wins_over_env_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("TOP_K=6\n", encoding="utf-8")
    monkeypatch.setenv("TOP_K", "8")

    assert Settings(_env_file=env_file).top_k == 8


def test_invalid_number_is_rejected(monkeypatch):
    monkeypatch.setenv("TOP_K", "many")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_resolve_relative_path_from_project_root():
    settings = Settings(_env_file=None)
    assert settings.resolve_path("knowledge/x.md") == PROJECT_ROOT / "knowledge" / "x.md"


def test_resolve_absolute_path_is_unchanged(tmp_path):
    settings = Settings(_env_file=None)
    assert settings.resolve_path(str(tmp_path)) == Path(tmp_path)


def test_resolved_paths_use_settings_values(tmp_path):
    settings = Settings(_env_file=None, knowledge_path="kb/a.md", chroma_path=str(tmp_path))

    assert settings.resolved_knowledge_path == PROJECT_ROOT / "kb" / "a.md"
    assert settings.resolved_chroma_path == Path(tmp_path)


def test_default_knowledge_file_exists():
    assert Settings(_env_file=None).resolved_knowledge_path.exists()


def test_get_settings_is_cached():
    assert get_settings() is get_settings()
