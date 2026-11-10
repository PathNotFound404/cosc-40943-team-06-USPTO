from pathlib import Path

import pytest

from patent_intelligence import settings


def test_development_overrides_the_data_folder(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(settings.DATA_FOLDER_VARIABLE, str(tmp_path))
    assert settings.data_folder() == tmp_path


def test_production_on_macos_uses_application_support(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(settings.DATA_FOLDER_VARIABLE, raising=False)
    monkeypatch.setattr(settings.sys, "platform", "darwin")
    assert settings.data_folder() == (
        Path.home() / "Library" / "Application Support" / settings.APP_NAME
    )


def test_production_on_windows_uses_local_app_data(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv(settings.DATA_FOLDER_VARIABLE, raising=False)
    monkeypatch.setattr(settings.sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert settings.data_folder() == tmp_path / settings.APP_NAME
