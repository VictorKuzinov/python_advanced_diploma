from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Подсказка Alembic’у:
target_metadata = Base.metadata
