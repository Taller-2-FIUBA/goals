"""Application configuration."""
from environ import config, var, group


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
        host = var("goals_db")
        port = var(5432, converter=int)
        database = var("postgres")
        create_structures = var(False, converter=bool)

    db = group(DB)  # type: ignore
