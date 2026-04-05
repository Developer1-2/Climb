from sqlalchemy import Column, Integer, Float, DateTime, String, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class ExchangeRate(Base):
    """Model to store USD to UGX exchange rates"""
    __tablename__ = "exchange_rates"

    id = Column(Integer, primary_key=True, index=True)
    rate = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ExchangeRate(id={self.id}, rate={self.rate}, timestamp={self.timestamp})>"


class User(Base):
    """Model to store Telegram users for alert subscriptions"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(BigInteger, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, chat_id={self.chat_id}, created_at={self.created_at})>"
