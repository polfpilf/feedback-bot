from dynaconf import Dynaconf, Validator


def _normalize_database_url(url: str) -> str:
    url = url.strip()

    deprecated_schema = "postgres://"
    new_schema = "postgresql://"

    if url.startswith(deprecated_schema):
        url = url.replace(deprecated_schema, new_schema, 1)
    
    return url


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
            cast=_normalize_database_url,
        ),
    ]
)

settings.validators.validate()
