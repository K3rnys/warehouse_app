import sys
import os
from alembic import context
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool

# Импортируем приложение
sys.path.insert(0, os.path.abspath(os.getcwd()))

from app import create_app
from models import db

# Создаем app и пушим контекст, чтобы SQLAlchemy был инициализирован
app = create_app()
app.app_context().push()

# Импортируем все модели ПОСЛЕ создания app context
# Это гарантирует, что модели будут зарегистрированы в метаданных
from models import Supplier, Product, Stock, Operation

config = context.config
fileConfig(config.config_file_name)

# Переопределяем sqlalchemy.url из конфигурации Flask приложения
config.set_main_option('sqlalchemy.url', app.config['SQLALCHEMY_DATABASE_URI'])

# SQLAlchemy metadata — для автогенерации миграций
# Метаданные собираются после импорта всех моделей
# Убеждаемся, что все таблицы зарегистрированы
target_metadata = db.Model.metadata

# Отладочная информация (можно закомментировать после проверки)
if target_metadata.tables:
    print(f"Обнаружено таблиц в метаданных: {len(target_metadata.tables)}")
    for table_name in target_metadata.tables.keys():
        print(f"  - {table_name}")
else:
    print("ВНИМАНИЕ: В метаданных не найдено таблиц!")


def include_object(object, name, type_, reflected, compare_to):
    """Функция для фильтрации объектов при автогенерации миграций"""
    # Исключаем таблицу alembic_version из сравнения
    if type_ == "table" and name == "alembic_version":
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_object=include_object
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_object=include_object
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
