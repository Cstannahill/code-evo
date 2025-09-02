"""Simple helper to copy SQLite tables to Postgres for small datasets.

Usage: python migrate_sqlite_to_postgres.py --sqlite ./code_evolution.db --postgres-postgres://user:pass@host:5432/dbname

This is a best-effort tool for small projects. For production data use pgloader or proper ETL.
"""

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.engine import Engine
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrate")


def copy(sqlite_url: str, postgres_url: str):
    s_engine: Engine = create_engine(sqlite_url)
    p_engine: Engine = create_engine(postgres_url)

    s_meta = MetaData()
    s_meta.reflect(bind=s_engine)

    p_meta = MetaData()
    p_meta.reflect(bind=p_engine)

    for table_name, table in s_meta.tables.items():
        logger.info(f"Migrating table: {table_name}")
        # create table in Postgres if not exists
        if table_name not in p_meta.tables:
            table.metadata = p_meta
            table.to_metadata(p_meta)
            p_meta.create_all(bind=p_engine, tables=[table])
        # copy rows
        with s_engine.connect() as s_conn, p_engine.connect() as p_conn:
            rows = s_conn.execute(table.select()).fetchall()
            if rows:
                p_conn.execute(table.insert(), [dict(r) for r in rows])
                logger.info(f"Inserted {len(rows)} rows into {table_name}")
            else:
                logger.info(f"No rows to migrate for {table_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sqlite",
        required=True,
        help="Path to sqlite file (e.g. sqlite:///./code_evolution.db)",
    )
    parser.add_argument(
        "--postgres",
        required=True,
        help="Postgres DATABASE_URL (e.g. postgresql://user:pass@host:5432/db)",
    )
    args = parser.parse_args()

    copy(args.sqlite, args.postgres)
    logger.info("Migration complete")
