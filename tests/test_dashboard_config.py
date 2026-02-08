"""Tests for dashboard configuration defaults."""

from core.config import ConfigurationManager, Environment


def test_dashboard_enabled_by_default_in_development(monkeypatch, tmp_path):
    """Dashboard should default to enabled in development when not configured."""
    monkeypatch.delenv("DASHBOARD__ENABLED", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.chdir(tmp_path)

    config_manager = ConfigurationManager(base_path=tmp_path)
    config = config_manager.load_config(env=Environment.DEVELOPMENT)

    assert config.dashboard.enabled is True


def test_dashboard_respects_explicit_disable(monkeypatch, tmp_path):
    """Explicitly disabling the dashboard should be honored."""
    monkeypatch.setenv("DASHBOARD__ENABLED", "false")
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.chdir(tmp_path)

    config_manager = ConfigurationManager(base_path=tmp_path)
    config = config_manager.load_config(env=Environment.DEVELOPMENT)

    assert config.dashboard.enabled is False
