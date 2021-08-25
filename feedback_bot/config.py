from dynaconf import Dynaconf, Validator


settings = Dynaconf(
    settings_files=["settings.toml", ".secrets.toml"],
    envvar_prefix="",
    validators=[
        Validator("TELEGRAM_BOT_TOKEN", must_exist=True, is_type_of=str, len_min=1),
        Validator(
            "TELEGRAM_WEBHOOK_PATH",
            must_exist=True,
            is_type_of=str,
            len_min=1,
            condition=lambda x: x.startswith("/"),
        ),
        Validator("TELEGRAM_WEBHOOK_HOST", must_exist=True, is_type_of=str, len_min=1),
        Validator("HOST", must_exist=True, is_type_of=str, len_min=1),
        Validator("PORT", must_exist=True, is_type_of=int, gt=1024, lt=65535),
        Validator("ADMIN_TOKEN", must_exist=True, is_type_of=str, len_min=8),
        Validator("DATABASE_URL", must_exist=True, is_type_of=str),
    ]
)

settings.validators.validate()
