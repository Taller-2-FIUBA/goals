# pylint: disable= missing-module-docstring, missing-function-docstring
from os import environ
from unittest.mock import patch
from environ import to_config
from goals.config import AppConfig


@patch.dict(environ, {}, clear=True)
def test_when_environment_is_empty_expect_9001_prometheus_port():
    cnf = to_config(AppConfig)
    assert cnf.prometheus_port == 9001


@patch.dict(environ, {}, clear=True)
def test_when_environment_is_empty_expect_warning_log_level():
    cnf = to_config(AppConfig)
    assert cnf.log_level == "WARNING"


@patch.dict(environ, {"GOALS_PROMETHEUS_PORT": "9004"}, clear=True)
def test_when_environment_has_prometheus_port_9004_expect_9004():
    cnf = to_config(AppConfig)
    assert cnf.prometheus_port == 9004


@patch.dict(environ, {"GOALS_LOG_LEVEL": "DEBUG"}, clear=True)
def test_when_environment_debug_log_level_expect_debug():
    cnf = to_config(AppConfig)
    assert cnf.log_level == "DEBUG"


@patch.dict(environ, {}, clear=True)
def test_when_environment_sentry_enabled_is_not_set_expect_false():
    cnf = to_config(AppConfig)
    assert not cnf.sentry.enabled


@patch.dict(
    environ, {"GOALS_SENTRY_ENABLED": "true"}, clear=True
)
def test_when_environment_sentry_enabled_is_true_expect_true():
    cnf = to_config(AppConfig)
    assert cnf.sentry.enabled


@patch.dict(environ, {}, clear=True)
def test_when_sentry_dsn_is_empty_expect_localhost():
    cnf = to_config(AppConfig)
    assert cnf.sentry.dsn == "https://token@sentry.ingest.localhost"


@patch.dict(
    environ,
    {"GOALS_SENTRY_DSN": "https://wf313c@24t2tg2g.ingest.sentry.io/33433"},
    clear=True
)
def test_when_sentry_dsn_has_sentry_url_expect_it():
    cnf = to_config(AppConfig)
    assert cnf.sentry.dsn == "https://wf313c@24t2tg2g.ingest.sentry.io/33433"
