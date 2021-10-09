from dynaconf import Dynaconf, LazySettings, Validator


def _normalize_database_url(settings: LazySettings, validator: Validator):
    url: str = settings.DATABASE_URL

    deprecated_schema = "postgres://"
    new_schema = "postgresql://"

    if url.startswith(deprecated_schema):
        url = url.replace(deprecated_schema, new_schema, 1)
    
    settings.DATABASE_URL = url


def _normalize_webhook_path(settings: LazySettings, validator: Validator):
    webhook_path: str = settings.TELEGRAM_WEBHOOK_PATH
    
    if not webhook_path.startswith("/"):
        webhook_path = "/" + webhook_path

    settings.TELEGRAM_WEBHOOK_PATH = webhook_path


settings = Dynaconf(
    settings_files=["settings.toml", ".secrets.toml"],
    envvar_prefix=False,
    validators=[
        Validator("TELEGRAM_BOT_TOKEN", must_exist=True, is_type_of=str, len_min=1),
        Validator("TELEGRAM_WEBHOOK_PATH", must_exist=True, is_type_of=str, len_min=1),
        Validator("TELEGRAM_WEBHOOK_HOST", must_exist=True, is_type_of=str, len_min=1),
        Validator("HOST", must_exist=True, is_type_of=str, len_min=1),
        Validator("PORT", must_exist=True, is_type_of=int, gt=1024, lt=65535),
        Validator("ADMIN_TOKEN", must_exist=True, is_type_of=str, len_min=8),
        Validator(
            "DATABASE_URL",
            must_exist=True,
            is_type_of=str,
            len_min=1,
            default=_normalize_database_url,
        ),
    ],
)

settings.validators.validate()
