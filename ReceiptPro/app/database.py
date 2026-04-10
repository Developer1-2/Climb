from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./receiptpro.db"

# Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db():
    """
    Get database session.
    Yields a database session for use in request handlers.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
