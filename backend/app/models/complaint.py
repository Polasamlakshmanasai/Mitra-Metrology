from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime

from app.database.connection import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)

    scan_id = Column(Integer, nullable=True)

    user_id = Column(Integer, nullable=True)

    product_name = Column(String, nullable=True)

    manufacturer = Column(String, nullable=True)

    violation_type = Column(String, nullable=True)

    description = Column(Text, nullable=False)

    status = Column(String, default="PENDING")  # PENDING, INVESTIGATING, RESOLVED, DISMISSED

    created_at = Column(DateTime, default=datetime.utcnow)
