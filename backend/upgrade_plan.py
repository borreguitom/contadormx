"""
Sube el plan de un usuario existente a 'agencia' (acceso total).
Uso: python upgrade_plan.py tu@email.com
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, User


async def main(email: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            print(f"[ERR] No existe un usuario con email: {email}")
            return

        user.plan = "agencia"
        user.queries_this_month = 0
        await db.commit()
        print(f"[OK] {email} → plan agencia (ilimitado)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python upgrade_plan.py tu@email.com")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
