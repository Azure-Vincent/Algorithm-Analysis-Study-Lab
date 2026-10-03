"""Application configuration (local use).

APP_ENV selects the profile: development (default) or testing. Settings can come from environment
variables or a local .env file (see .env.example). The secret key that signs Flask's session cookie
is generated once into instance/secret_key when SECRET_KEY isn't set.
"""
from __future__ import annotations

import os
import secrets
from datetime import timedelta

try:                                     # optional convenience
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:                      # pragma: no cover
    pass


class ConfigError(RuntimeError):
    pass


class BaseConfig:
    DEBUG = False
    TESTING = False
    JSON_AS_ASCII = False
    SESSION_COOKIE_NAME = "bigo_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Strict"
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    MAX_CONTENT_LENGTH = 256 * 1024          # request bodies (answers, code) are small

    def __init__(self):
        self.SECRET_KEY = os.environ.get("SECRET_KEY", "")
        self.BIGO_DB = os.environ.get("BIGO_DB", "")


class DevelopmentConfig(BaseConfig):
    pass


class TestingConfig(BaseConfig):
    TESTING = True

    def __init__(self):
        super().__init__()
        self.SECRET_KEY = self.SECRET_KEY or secrets.token_hex(32)


PROFILES = {"development": DevelopmentConfig, "testing": TestingConfig}


def load(env_name=None):
    name = (env_name or os.environ.get("APP_ENV") or "development").strip().lower()
    if name not in PROFILES:
        raise ConfigError(f"Unknown APP_ENV '{name}' (use development or testing).")
    cfg = PROFILES[name]()
    cfg.ENV_NAME = name
    return cfg
