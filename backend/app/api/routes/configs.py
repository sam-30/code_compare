from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.config import ComparisonConfig
from app.schemas.config import ConfigCreate, ConfigOut, ConfigUpdate

router = APIRouter(prefix="/configs", tags=["configs"])


@router.get("", response_model=list[ConfigOut])
async def list_configs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ComparisonConfig).order_by(ComparisonConfig.id))
    return result.scalars().all()


@router.post("", response_model=ConfigOut, status_code=201)
async def create_config(payload: ConfigCreate, db: AsyncSession = Depends(get_db)):
    if payload.is_default:
        await _clear_default(db)

    config = ComparisonConfig(
        name=payload.name,
        description=payload.description,
        method_weights=payload.method_weights,
        is_default=payload.is_default,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


@router.get("/{config_id}", response_model=ConfigOut)
async def get_config(config_id: int, db: AsyncSession = Depends(get_db)):
    config = await db.get(ComparisonConfig, config_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Config not found")
    return config


@router.put("/{config_id}", response_model=ConfigOut)
async def update_config(
    config_id: int, payload: ConfigUpdate, db: AsyncSession = Depends(get_db)
):
    config = await db.get(ComparisonConfig, config_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Config not found")

    if payload.name is not None:
        config.name = payload.name
    if payload.description is not None:
        config.description = payload.description
    if payload.method_weights is not None:
        config.method_weights = payload.method_weights
    if payload.is_default is not None:
        if payload.is_default:
            await _clear_default(db)
        config.is_default = payload.is_default

    await db.commit()
    await db.refresh(config)
    return config


@router.delete("/{config_id}", status_code=204)
async def delete_config(config_id: int, db: AsyncSession = Depends(get_db)):
    config = await db.get(ComparisonConfig, config_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Config not found")
    await db.delete(config)
    await db.commit()


async def _clear_default(db: AsyncSession) -> None:
    result = await db.execute(
        select(ComparisonConfig).where(ComparisonConfig.is_default.is_(True))
    )
    for c in result.scalars().all():
        c.is_default = False
    await db.flush()
