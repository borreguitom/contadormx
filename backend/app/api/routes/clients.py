from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db, Cliente
from app.core.deps import get_current_user, check_cliente_limit, User

router = APIRouter()


class ClienteCreate(BaseModel):
    rfc: str
    razon_social: str
    regimen_fiscal: Optional[str] = None
    actividad: Optional[str] = None
    correo: Optional[str] = None
    telefono: Optional[str] = None


class ClienteResponse(BaseModel):
    id: int
    rfc: str
    razon_social: str
    regimen_fiscal: Optional[str]
    actividad: Optional[str]
    correo: Optional[str]

    class Config:
        from_attributes = True


@router.post("", response_model=ClienteResponse)
async def create_cliente(
    data: ClienteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count_result = await db.execute(
        select(func.count()).select_from(Cliente).where(Cliente.user_id == current_user.id)
    )
    current_count = count_result.scalar_one()
    allowed, msg = check_cliente_limit(current_user, current_count)
    if not allowed:
        raise HTTPException(status_code=402, detail=msg)

    cliente = Cliente(**data.model_dump(), user_id=current_user.id)
    db.add(cliente)
    await db.commit()
    await db.refresh(cliente)
    return cliente


@router.get("", response_model=list[ClienteResponse])
async def list_clientes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Cliente)
        .where(Cliente.user_id == current_user.id)
        .order_by(Cliente.razon_social)
    )
    return result.scalars().all()


@router.get("/{cliente_id}", response_model=ClienteResponse)
async def get_cliente(
    cliente_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Cliente).where(
            Cliente.id == cliente_id,
            Cliente.user_id == current_user.id,
        )
    )
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente
