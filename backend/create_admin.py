"""
Crea (o actualiza) un usuario admin con plan=agencia.
Uso: python create_admin.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from passlib.context import CryptContext
from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal, User

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

EMAIL    = "admin@contadormx.mx"
PASSWORD = "Admin2025!"
NOMBRE   = "Administrador"


async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == EMAIL))
        user = result.scalar_one_or_none()

        if user:
            user.hashed_password = pwd_ctx.hash(PASSWORD)
            user.plan = "agencia"
            user.is_active = True
            user.nombre = NOMBRE
            await db.commit()
            print(f"[OK] Usuario actualizado: {EMAIL}")
        else:
            nuevo = User(
                email=EMAIL,
                hashed_password=pwd_ctx.hash(PASSWORD),
                nombre=NOMBRE,
                is_active=True,
                plan="agencia",
                queries_this_month=0,
            )
            db.add(nuevo)
            await db.commit()
            print(f"[OK] Usuario creado: {EMAIL}")

        print(f"     Email:      {EMAIL}")
        print(f"     Password:   {PASSWORD}")
        print(f"     Plan:       agencia (ilimitado)")


if __name__ == "__main__":
    asyncio.run(main())
