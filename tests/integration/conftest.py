from pathlib import PurePath
from urllib.parse import urlencode

import asyncpg
import psycopg2
import pytest
from alembic.command import upgrade as alembic_upgrade
from alembic.config import Config as AlembicConfig
from psycopg2.extensions import parse_dsn, ISOLATION_LEVEL_AUTOCOMMIT


def _build_psql_url(conn_params: dict) -> str:
    userspec = conn_params.pop("user", "")
    password = conn_params.pop("password", None)
    if password:
        userspec += f":{password}"
    if userspec:
        userspec += "@"
    
    hostspec = conn_params.pop("host", "")
    port = conn_params.pop("port", None)
    if port:
        hostspec += f":{port}"

    dbname = conn_params.pop("dbname", "")
    if dbname:
        dbname = f"/{dbname}"

    paramspec = urlencode(conn_params)
    if paramspec:
        paramspec = f"?{paramspec}"

    return f"postgresql://{userspec}{hostspec}{dbname}{paramspec}"


_ALEMBIC_INI_PATH = PurePath(__file__).parents[2] / "alembic.ini"


@pytest.fixture(scope="session")
def create_test_db(container):
    conn_params = parse_dsn(container.config.DATABASE_URL())
    original_db_name = conn_params.pop("dbname")
    test_db_name = f"{original_db_name}_test"

    conn = psycopg2.connect(**conn_params)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    cur = conn.cursor()
    cur.execute(f"CREATE DATABASE {test_db_name}")

    test_db_params = {**conn_params, "dbname": test_db_name}
    test_db_url = _build_psql_url(test_db_params)

    alembic_cfg = AlembicConfig(_ALEMBIC_INI_PATH)
    alembic_cfg.set_main_option("sqlalchemy.url", test_db_url)
    alembic_upgrade(alembic_cfg, "head")

    try:
        with container.config.DATABASE_URL.override(test_db_url):
            yield
    finally:
        cur.execute(f"DROP DATABASE {test_db_name}")
        cur.close()
        conn.close()


@pytest.fixture(scope="session")
async def base_connection(container, create_test_db):
    conn = await asyncpg.connect(dsn=container.config.DATABASE_URL())
    try:
        yield conn
    finally:
        await conn.close()


@pytest.fixture(scope="function")
async def db_connection(base_connection):
    transaction = base_connection.transaction()
    await transaction.start()

    try:
        yield base_connection
    finally:
        await transaction.rollback()
