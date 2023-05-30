"""Application configuration."""

from environ import config, var, group, bool_var


@config(prefix="GOALS")
class AppConfig:
    """Application configuration values from environment."""

    log_level = var("WARNING")
    prometheus_port = var(9001, converter=int)

    @config
    class DB:
        """Database configuration."""

        driver = var("postgresql")
        password = var("postgres")
        user = var("postgres")
        host = var("user_db")
        port = var(5432, converter=int)
        database = var("postgres")
        create_structures = var(False, converter=bool)

    @config
    class AUTH:
        """Authentication service configuration."""

        host = var("auth-svc")

    @config
    class TEST:
        """Test configurations."""

        is_testing = var(False, converter=bool)
        id = var(1, converter=int)
        role = var("admin")

    @config(prefix="SENTRY")
    class Sentry:
        """Sentry configuration."""

        enabled = bool_var(False)
        dsn = var("https://token@sentry.ingest.localhost")

    db = group(DB)  # type: ignore
    auth = group(AUTH)  # type: ignore
    test = group(TEST)  # type: ignore
    sentry = group(Sentry)
