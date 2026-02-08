"""Tests for dashboard configuration defaults."""

from core.config import ConfigurationManager, Environment


def test_dashboard_disabled_by_default_in_development(monkeypatch, tmp_path):
    """Dashboard should default to disabled in development when not configured."""
    monkeypatch.delenv("DASHBOARD__ENABLED", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.chdir(tmp_path)

    config_manager = ConfigurationManager(base_path=tmp_path)
    config = config_manager.load_config(env=Environment.DEVELOPMENT)

    assert config.dashboard.enabled is False


def test_dashboard_respects_explicit_enable(monkeypatch, tmp_path):
    """Explicitly enabling the dashboard should be honored."""
    monkeypatch.setenv("DASHBOARD__ENABLED", "true")
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.chdir(tmp_path)

    config_manager = ConfigurationManager(base_path=tmp_path)
    config = config_manager.load_config(env=Environment.DEVELOPMENT)

    assert config.dashboard.enabled is True
