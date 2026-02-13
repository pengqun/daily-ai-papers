"""Paper and Author ORM models."""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Paper(Base):
    __tablename__ = "papers"
    __table_args__ = (UniqueConstraint("source", "source_id", name="uq_paper_source"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # "arxiv", "semantic_scholar"
    source_id: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[str | None] = mapped_column(Text)
    pdf_url: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    categories: Mapped[list[str] | None] = mapped_column(ARRAY(String))

    # Extracted / analyzed fields
    full_text: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    summary_zh: Mapped[str | None] = mapped_column(Text)
    contributions: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    keywords: Mapped[list[str] | None] = mapped_column(ARRAY(String))

    # Processing status
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    authors: Mapped[list["Author"]] = relationship(
        secondary="paper_authors", back_populates="papers"
    )


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    affiliation: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    papers: Mapped[list["Paper"]] = relationship(
        secondary="paper_authors", back_populates="authors"
    )


class PaperAuthor(Base):
    __tablename__ = "paper_authors"

    paper_id: Mapped[int] = mapped_column(ForeignKey("papers.id"), primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
