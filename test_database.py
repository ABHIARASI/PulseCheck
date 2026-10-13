
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://postgres:122004@localhost:5432/pulsecheck_test",
)

test_engine = create_engine(TEST_DATABASE_URL)

TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


def create_test_tables():
    import models

    Base.metadata.create_all(bind=test_engine)
