from datetime import datetime
from sqlalchemy import (
    String, Integer, Boolean, DateTime, ForeignKey, Text, JSON, BigInteger
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


# ==================== نقش‌ها ====================
# رهبر > معاون رهبر > ارجمند > ارشد > بقیه

ROLE_LEADER = "رهبر"
ROLE_DEPUTY = "معاون رهبر"
ROLE_ARJOMAND = "ارجمند"
ROLE_SENIOR = "ارشد"
ROLE_MEMBER = "عضو"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(128))
    gender: Mapped[str] = mapped_column(String(16), default="نامشخص")
    yang: Mapped[int] = mapped_column(Integer, default=100)  # یانگ بدن (مرد) 0-100
    yin: Mapped[int] = mapped_column(Integer, default=0)     # یین بدن (زن) 0-100
    is_virgin: Mapped[bool] = mapped_column(Boolean, default=True)
    is_dead: Mapped[bool] = mapped_column(Boolean, default=False)
    is_spirit_raiser: Mapped[bool] = mapped_column(Boolean, default=False)  # پرورش‌دهنده روح بعد از مرگ

    # Rank system
    rank: Mapped[str] = mapped_column(String(32), default="عضو دسته‌های پایین‌تر")
    level: Mapped[int] = mapped_column(Integer, default=1)
    xp: Mapped[int] = mapped_column(Integer, default=0)

    # Role system (بالاتر از رتبه)
    role: Mapped[str] = mapped_column(String(32), default=ROLE_MEMBER)

    # Stats
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    total_duels: Mapped[int] = mapped_column(Integer, default=0)
    win_streak: Mapped[int] = mapped_column(Integer, default=0)
    loss_streak: Mapped[int] = mapped_column(Integer, default=0)
    same_rank_wins: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)

    # محدودیت موقت (mute)
    restricted_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    restriction_reason: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # Timestamps
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_active: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    last_duel_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relations
    medals: Mapped[list["Medal"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    achievements: Mapped[list["UserAchievement"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    accounts: Mapped[list["Account"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    missions_progress: Mapped[list["UserMission"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def win_rate(self) -> float:
        if self.total_duels == 0:
            return 0.0
        return round((self.wins / self.total_duels) * 100, 1)

    @property
    def is_restricted(self) -> bool:
        if self.restricted_until is None:
            return False
        return datetime.utcnow() < self.restricted_until

    @property
    def is_staff(self) -> bool:
        return self.role in (ROLE_LEADER, ROLE_DEPUTY, ROLE_ARJOMAND, ROLE_SENIOR)


class Account(Base):
    """سیستم چندحسابه - هر کاربر می‌تونه چند اکانت با رمز داشته باشه"""
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))  # صاحب اصلی (تلگرام)
    account_name: Mapped[str] = mapped_column(String(64))  # نام نمایشی اکانت
    password_hash: Mapped[str] = mapped_column(String(128))  # هش رمز
    linked_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)  # یوزر مرتبط
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    owner: Mapped["User"] = relationship(back_populates="accounts", foreign_keys=[owner_id])


class Medal(Base):
    __tablename__ = "medals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    earned_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="medals")


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    title: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(String(256))
    icon: Mapped[str] = mapped_column(String(16), default="🏆")


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    achievement_id: Mapped[int] = mapped_column(ForeignKey("achievements.id"))
    earned_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="achievements")
    achievement: Mapped["Achievement"] = relationship()


class Duel(Base):
    __tablename__ = "duels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    challenger_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    opponent_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    winner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    status: Mapped[str] = mapped_column(String(32), default="pending")
    is_guardian: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    start_date: Mapped[datetime] = mapped_column(DateTime)
    end_date: Mapped[datetime] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    top_players: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(32))
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    question_text: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON)
    correct_answer: Mapped[int] = mapped_column(Integer)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)


# ==================== سیستم مأموریت ====================

class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text)
    
    # نوع مأموریت: global / section / level
    mission_type: Mapped[str] = mapped_column(String(32))  # global, section, level
    
    # برای مأموریت بخش (بر اساس رتبه)
    target_rank: Mapped[str | None] = mapped_column(String(32), nullable=True)
    
    # برای مأموریت سطح
    min_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # هدف مأموریت
    target_type: Mapped[str] = mapped_column(String(32))  # wins, duels, guardian_wins, streak, ...
    target_value: Mapped[int] = mapped_column(Integer)  # مثلاً ۱۰ برد
    
    # جایزه (توسط رهبر تنظیم می‌شه)
    reward_xp: Mapped[int] = mapped_column(Integer, default=0)
    reward_medal: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reward_description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    progresses: Mapped[list["UserMission"]] = relationship(back_populates="mission", cascade="all, delete-orphan")


class UserMission(Base):
    __tablename__ = "user_missions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    mission_id: Mapped[int] = mapped_column(ForeignKey("missions.id"))
    
    progress: Mapped[int] = mapped_column(Integer, default=0)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reward_claimed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="missions_progress")
    mission: Mapped["Mission"] = relationship(back_populates="progresses")
