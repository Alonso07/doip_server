"""Tests for web dashboard CLI startup defaults."""

import os
import sys
from importlib import import_module

import pytest


@pytest.mark.unit
def test_web_app_run_server_defaults_to_loopback(monkeypatch):
    import web.app as web_app

    calls = {}

    def fake_run(target, **kwargs):
        calls["target"] = target
        calls.update(kwargs)

    monkeypatch.setattr(sys, "argv", ["doip_web"])
    monkeypatch.setattr(web_app.uvicorn, "run", fake_run)

    web_app.run_server()

    assert calls["target"] == "web.app:app"
    assert calls["host"] == "127.0.0.1"
    assert os.environ["DOIP_GATEWAY_CONFIG"] == "config/gateway1.yaml"


@pytest.mark.unit
def test_main_web_mode_defaults_to_loopback(monkeypatch):
    import uvicorn

    server_main = import_module("doip_server.main")
    calls = {}

    def fake_run(app, **kwargs):
        calls["app"] = app
        calls.update(kwargs)

    monkeypatch.setattr(sys, "argv", ["doip_server", "--web"])
    monkeypatch.setattr(uvicorn, "run", fake_run)

    server_main.main()

    assert calls["host"] == "127.0.0.1"
    assert calls["port"] == 8080
