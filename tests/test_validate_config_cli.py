"""Tests for the `validate_config` CLI entry point."""

import pytest

from doip_server import validate_config


@pytest.mark.unit
def test_main_succeeds_for_valid_config(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["validate_config"])

    with pytest.raises(SystemExit) as exc:
        validate_config.main()
    assert exc.value.code == 0

    captured = capsys.readouterr()
    assert "All configuration files are valid." in captured.out
    assert "OK    config/gateway1.yaml" in captured.out


@pytest.mark.unit
def test_main_fails_for_invalid_config(tmp_path, capsys, monkeypatch):
    bad_gateway = tmp_path / "bad_gateway.yaml"
    bad_gateway.write_text("gateway:\n  network:\n    host: '0.0.0.0'\n")

    monkeypatch.setattr(
        "sys.argv", ["validate_config", "--gateway-config", str(bad_gateway)]
    )

    with pytest.raises(SystemExit) as exc:
        validate_config.main()
    assert exc.value.code == 1

    captured = capsys.readouterr()
    assert "FAIL" in captured.out
    assert "Configuration validation failed." in captured.out
