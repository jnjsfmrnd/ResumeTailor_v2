import os

from apps.common.logging import build_logging_config

from .base import *  # noqa: F403

DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

USE_LOCAL_FILE_STORAGE = False
GITHUB_MODELS_ENABLE_DEV_FALLBACK = False
AZURE_STORAGE_CONTAINER = os.getenv(
    "AZURE_STORAGE_CONTAINER_NAME",
    os.getenv("AZURE_STORAGE_CONTAINER", "resumetailor-artifacts"),
)
AZURE_STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY", "")
AZURE_STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "")
AZURE_BLOB_ENDPOINT = os.getenv(
    "AZURE_BLOB_ENDPOINT",
    f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
)

if not AZURE_STORAGE_ACCOUNT_NAME:
    raise RuntimeError("AZURE_STORAGE_ACCOUNT_NAME must be set in production")

website_hostname = os.getenv("WEBSITE_HOSTNAME", "")
if website_hostname and website_hostname not in ALLOWED_HOSTS:  # noqa: F405
    ALLOWED_HOSTS.append(website_hostname)  # noqa: F405

LOGGING = build_logging_config(production=True)