"""Paper CRUD and search API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from daily_ai_papers.database import get_db
from daily_ai_papers.models.paper import Paper
from daily_ai_papers.schemas.paper import PaperDetail, PaperListItem

router = APIRouter()


@router.get("", response_model=list[PaperListItem])
async def list_papers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[Paper]:
    """List papers with pagination and optional filters."""
    stmt = select(Paper).options(selectinload(Paper.authors))

    if category:
        stmt = stmt.where(Paper.categories.any(category))
    if status:
        stmt = stmt.where(Paper.status == status)

    stmt = stmt.order_by(Paper.published_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{paper_id}", response_model=PaperDetail)
async def get_paper(paper_id: int, db: AsyncSession = Depends(get_db)) -> Paper:
    """Get full paper details by ID."""
    stmt = select(Paper).options(selectinload(Paper.authors)).where(Paper.id == paper_id)
    result = await db.execute(stmt)
    paper = result.scalar_one()
    return paper
