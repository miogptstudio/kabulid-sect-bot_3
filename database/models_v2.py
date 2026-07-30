"""
مدل‌های نسخه ۲ - سیستم فرقه‌ها، تذهیب، استاد-شاگردی، آرنا و چندحسابه
"""

from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, JSON, BigInteger, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from database.models import Base, User


# ==================== فرقه‌ها ====================

SECT_TYPES = ["ارتدوکس", "بی‌طرف", "شیطانی"]

SECT_STATUS = [
    "عضو دسته‌های پایین‌تر",
    "عضو بیرونی فرقه",
    "عضو داخلی فرقه",
]


class Sect(Base):
    __tablename__ = "sects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    sect_type: Mapped[str] = mapped_column(String(32))  # ارتدوکس / بی‌طرف / شیطانی
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    total_points: Mapped[int] = mapped_column(Integer, default=0)
    member_count: Mapped[int] = mapped_column(Integer, default=0)
    
    leader_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    members: Mapped[list["SectMember"]] = relationship(back_populates="sect")


class SectMember(Base):
    __tablename__ = "sect_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    sect_id: Mapped[int] = mapped_column(ForeignKey("sects.id"))
    
    status: Mapped[str] = mapped_column(String(32), default="عضو دسته‌های پایین‌تر")
    contribution_points: Mapped[int] = mapped_column(Integer, default=0)
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    sect: Mapped["Sect"] = relationship(back_populates="members")


# ==================== سیستم تذهیب ====================

CULTIVATION_REALMS = ["پایه", "متوسط", "بالا", "پیشرفته", "خدا"]


class Cultivation(Base):
    __tablename__ = "cultivations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    
    realm: Mapped[str] = mapped_column(String(32), default="پایه")
    stage: Mapped[int] = mapped_column(Integer, default=1)  # ۱ تا ۳
    energy: Mapped[int] = mapped_column(Integer, default=0)
    
    talent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    spiritual_root: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


# ==================== استاد - شاگردی ====================

class MasterDisciple(Base):
    __tablename__ = "master_disciples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    master_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    disciple_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    master_share: Mapped[float] = mapped_column(Float, default=0.1)
    disciple_share: Mapped[float] = mapped_column(Float, default=0.05)
    
    status: Mapped[str] = mapped_column(String(32), default="active")
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


# ==================== آرنا ====================

ARENA_TIERS = ["برنز", "نقره", "طلا"]


class ArenaProfile(Base):
    __tablename__ = "arena_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    
    tier: Mapped[str] = mapped_column(String(16), default="برنز")
    points: Mapped[int] = mapped_column(Integer, default=0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    season_points: Mapped[int] = mapped_column(Integer, default=0)


class ArenaMatch(Base):
    __tablename__ = "arena_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player1_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    player2_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    winner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    tier: Mapped[str] = mapped_column(String(16))
    is_sect_war: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


# ==================== چندحسابه کامل ====================

class GameAccount(Base):
    __tablename__ = "game_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    
    account_name: Mapped[str] = mapped_column(String(64))
    password_hash: Mapped[str] = mapped_column(String(128))
    
    linked_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    is_main: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
