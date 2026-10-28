from pathlib import Path

import pytest

from patent_intelligence import settings


def test_development_overrides_the_data_folder(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(settings.DATA_FOLDER_VARIABLE, str(tmp_path))
    assert settings.data_folder() == tmp_path


def test_production_uses_application_support(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(settings.DATA_FOLDER_VARIABLE, raising=False)
    assert settings.data_folder() == (
        Path.home() / "Library" / "Application Support" / settings.APP_NAME
    )
