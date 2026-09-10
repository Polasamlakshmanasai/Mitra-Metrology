from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.database.connection import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    product_name = Column(String, nullable=True)

    category = Column(String, nullable=True)

    manufacturer = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)