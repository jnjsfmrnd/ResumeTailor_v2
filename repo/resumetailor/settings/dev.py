import os

from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
GITHUB_MODELS_ENABLE_DEV_FALLBACK = (
	os.getenv("GITHUB_MODELS_ENABLE_DEV_FALLBACK", "true").lower() == "true"
)