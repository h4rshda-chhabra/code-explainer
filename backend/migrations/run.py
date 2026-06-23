'''backend/migrations/run.py'''
"""Simple migration runner for CodeSense.
It reads all *.sql files in the migrations directory ordered by filename
(e.g., 001_initial_schema.sql, 002_add_stats.sql) and executes them
using the SQLAlchemy engine defined in backend.database.

Usage:
    python -m backend.migrations.run up   # apply all pending migrations
    python -m backend.migrations.run down # rollback last migration (not implemented)
"""
import os
import sys
from pathlib import Path
from importlib import import_module

# Import the SQLAlchemy engine
from ..database import engine

MIGRATIONS_DIR = Path(__file__).parent

def get_migration_files():
    return sorted([p for p in MIGRATIONS_DIR.glob("*.sql") if p.is_file()])

def apply_migration(sql_path: Path):
    print(f"Applying migration: {sql_path.name}")
    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()
    # Execute within a transaction
    with engine.begin() as conn:
        conn.execute(sql)

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m backend.migrations.run <up|down>")
        sys.exit(1)
    direction = sys.argv[1].lower()
    if direction != "up":
        print("Only 'up' direction is supported in this simple runner.")
        sys.exit(1)

    migrations = get_migration_files()
    for migration in migrations:
        apply_migration(migration)
    print("All migrations applied.")

if __name__ == "__main__":
    main()
