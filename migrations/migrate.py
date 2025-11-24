#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# Добавляем корень проекта в Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.repositories.pg_repo import PostgresRepository

class Migrator:
    def __init__(self):
        self.repo = PostgresRepository()

    def ensure_migrations_table(self):
        """Создает таблицу для отслеживания миграций"""
        self.repo.execute_query('''
            CREATE TABLE IF NOT EXISTS migrations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                applied_at TIMESTAMPTZ DEFAULT now()
            )
        ''', commit=True)

    def get_applied_migrations(self):
        """Возвращает список примененных миграций"""
        result = self.repo.execute_query('SELECT name FROM migrations ORDER BY name')
        return {row['name'] for row in result} if result else set()

    def apply_migration(self, filename, sql_content):
        """Применяет одну миграцию"""
        try:
            print(f"🔄 Applying {filename}...")
            self.repo.execute_query(sql_content, commit=True)
            self.repo.execute_query(
                'INSERT INTO migrations (name) VALUES (%s)',
                (filename,),
                commit=True
            )
            print(f"✅ {filename} applied successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to apply {filename}: {e}")
            return False

    def run_migrations(self):
        """Запускает все непримененные миграции"""
        print("🚀 Starting database migrations...")

        self.ensure_migrations_table()
        applied_migrations = self.get_applied_migrations()

        migrations_dir = Path(__file__).parent / 'sql'
        migration_files = sorted([
            f for f in os.listdir(migrations_dir)
            if f.endswith('.sql') and f not in applied_migrations
        ])

        if not migration_files:
            print("✅ No new migrations to apply")
            return

        print(f"📦 Found {len(migration_files)} new migration(s)")

        for filename in migration_files:
            filepath = migrations_dir / filename
            with open(filepath, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            if not self.apply_migration(filename, sql_content):
                print("💥 Migration failed, stopping...")
                return False

        print("🎉 All migrations completed successfully!")
        return True

if __name__ == '__main__':
    migrator = Migrator()
    migrator.run_migrations()
