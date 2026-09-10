from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

from app.database.connection import Base


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=True)

    image_path = Column(String, nullable=True)

    status = Column(String, default="processing")

    score = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)