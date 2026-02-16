from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class FileMeta(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    size: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)

    scan_status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)  # PENDING/CLEAN/INFECTED
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="files")
