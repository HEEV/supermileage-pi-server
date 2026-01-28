import os

import pytest


@pytest.fixture
def default_env(monkeypatch):
    """fixture providing basic environment for testing"""
    monkeypatch.setenv("DISABLE_REMOTE", "False")
    monkeypatch.setenv("DISABLE_LOCAL", "False")
    monkeypatch.setenv("DISABLE_DISPLAY", "False")
    monkeypatch.setenv("TESTING", "True")
    test_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(test_dir, "testfiles", "car_config.json")
    monkeypatch.setenv("CONFIG_FILE_PATH", config_path)
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASSWORD", "password")
    monkeypatch.setenv("DB_PORT", "27017")
    monkeypatch.setenv("DB", "database")
    yield
