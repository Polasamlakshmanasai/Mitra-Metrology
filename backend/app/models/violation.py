from sqlalchemy import Column, Integer, String

from app.database.connection import Base


class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)

    scan_id = Column(Integer, nullable=False)

    field = Column(String, nullable=True)

    description = Column(String, nullable=False)

    severity = Column(String, default="medium")

    evidence_path = Column(String, nullable=True)