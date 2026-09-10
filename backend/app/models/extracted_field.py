from sqlalchemy import Column, Integer, String, Float

from app.database.connection import Base


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id = Column(Integer, primary_key=True, index=True)

    scan_id = Column(Integer, nullable=False)

    field_name = Column(String, nullable=False)

    field_value = Column(String, nullable=True)

    confidence = Column(Float, nullable=True)

    bounding_box = Column(String, nullable=True)