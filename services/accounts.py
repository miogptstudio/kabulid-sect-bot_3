import hashlib
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models_v2 import GameAccount
from database.models import User


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


async def create_account(
    session: AsyncSession,
    owner_telegram_id: int,
    account_name: str,
    password: str,
    linked_user_id: int | None = None,
    is_main: bool = False
) -> GameAccount:
    acc = GameAccount(
        owner_telegram_id=owner_telegram_id,
        account_name=account_name,
        password_hash=hash_password(password),
        linked_user_id=linked_user_id,
        is_main=is_main
    )
    session.add(acc)
    await session.commit()
    await session.refresh(acc)
    return acc


async def login_account(
    session: AsyncSession,
    owner_telegram_id: int,
    account_name: str,
    password: str
) -> GameAccount | None:
    result = await session.execute(
        select(GameAccount).where(
            GameAccount.owner_telegram_id == owner_telegram_id,
            GameAccount.account_name == account_name
        )
    )
    acc = result.scalar_one_or_none()
    if not acc:
        return None
    if acc.password_hash != hash_password(password):
        return None
    return acc


async def get_user_accounts(session: AsyncSession, owner_telegram_id: int) -> list:
    result = await session.execute(
        select(GameAccount).where(GameAccount.owner_telegram_id == owner_telegram_id)
    )
    return result.scalars().all()
