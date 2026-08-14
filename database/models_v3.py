"""
مدل‌های نسخه ۳ - کیمیاگری، طلسم، تکنیک، مهر، ساختمون و آیتم
"""

from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, JSON, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from database.models import Base


# ==================== ساختمون‌ها ====================

BUILDING_TYPES = ["داروخانه", "کیمیاگری", "طلسم‌خانه", "آهنگری", "کتابخانه"]


class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    building_type: Mapped[str] = mapped_column(String(32))  # داروخانه، کیمیاگری و...
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ShopItem(Base):
    __tablename__ = "shop_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    building_id: Mapped[int] = mapped_column(ForeignKey("buildings.id"))
    
    name: Mapped[str] = mapped_column(String(64))
    item_type: Mapped[str] = mapped_column(String(32))  # pill, talisman, technique, material, ...
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    price: Mapped[int] = mapped_column(BigInteger, default=0)  # قیمت؛ برای مقادیر بسیار بزرگ
    effect: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # {"xp": 50, "energy": 30, ...}
    
    stock: Mapped[int] = mapped_column(Integer, default=-1)  # -1 = نامحدود
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class UserInventory(Base):
    __tablename__ = "user_inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("shop_items.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    acquired_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ==================== کیمیاگری و ساخت ====================

class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    recipe_type: Mapped[str] = mapped_column(String(32))  # alchemy, talisman, seal, technique
    
    # مواد لازم (JSON ساده)
    required_materials: Mapped[dict] = mapped_column(JSON)  # {"herb": 2, "stone": 1}
    result_item_name: Mapped[str] = mapped_column(String(64))
    result_effect: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    min_cultivation_realm: Mapped[str] = mapped_column(String(32), default="پایه")
    success_rate: Mapped[int] = mapped_column(Integer, default=70)  # درصد موفقیت
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# ==================== مهارت‌های ساخت ====================

class CraftingSkill(Base):
    __tablename__ = "crafting_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    skill_type: Mapped[str] = mapped_column(String(32))  # alchemy, talisman, seal, technique
    level: Mapped[int] = mapped_column(Integer, default=1)
    exp: Mapped[int] = mapped_column(Integer, default=0)


# ==================== تکنیک تذهیب و ریشه معنوی ====================

SPIRITUAL_ROOTS = [
    "بدون ریشه",
    "ریشه پنج‌عنصر",
    "ریشه آتش",
    "ریشه آب",
    "ریشه چوب",
    "ریشه فلز",
    "ریشه خاک",
    "ریشه دوگانه",
    "ریشه تک‌عنصر خالص",
]


class CultivationTechnique(Base):
    """تکنیک / کتاب تذهیب"""
    __tablename__ = "cultivation_techniques"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # سطح تکنیک
    grade: Mapped[str] = mapped_column(String(32), default="پایه")  # پایه، متوسط، بالا، افسانه‌ای
    
    # انرژی بیشتر در هر جمع‌آوری
    energy_bonus: Mapped[int] = mapped_column(Integer, default=0)
    
    # ریشه مورد نیاز (اختیاری)
    required_root: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    is_starter: Mapped[bool] = mapped_column(Boolean, default=False)  # تکنیک شروع رایگان
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class UserTechnique(Base):
    """تکنیک‌هایی که کاربر بلده / داره"""
    __tablename__ = "user_techniques"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    technique_id: Mapped[int] = mapped_column(ForeignKey("cultivation_techniques.id"))
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)  # تکنیک فعال فعلی
    learned_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    learned_from: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)  # از کی یاد گرفته


# ==================== جنسیت و تذهیب دوگانه ====================

GENDERS = ["مرد", "زن", "نامشخص"]


class DualCultivation(Base):
    """جلسه تذهیب دوگانه بین دو نفر"""
    __tablename__ = "dual_cultivations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user1_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user2_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending, active, finished
    energy_shared: Mapped[int] = mapped_column(Integer, default=0)
    
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


# ==================== ازدواج و چندهمسری ====================

class Marriage(Base):
    __tablename__ = "marriages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    husband_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    wife_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # pending = درخواست | engaged = نامزدی | married | divorced | expired
    status: Mapped[str] = mapped_column(String(32), default="pending")
    invited_guests: Mapped[list | None] = mapped_column(JSON, nullable=True)
    
    level_warning: Mapped[bool] = mapped_column(Boolean, default=False)  # اختلاف سطح >= 2
    cross_sect_warning: Mapped[bool] = mapped_column(Boolean, default=False)
    
    proposed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    engage_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # مهلت نامزدی
    married_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    divorced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


# ==================== قلمرو، چالش رهبری، خیانت ====================

class Territory(Base):
    __tablename__ = "territories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_sect_id: Mapped[int | None] = mapped_column(ForeignKey("sects.id"), nullable=True)
    defense_points: Mapped[int] = mapped_column(Integer, default=100)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class LeadershipChallenge(Base):
    __tablename__ = "leadership_challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sect_id: Mapped[int] = mapped_column(ForeignKey("sects.id"))
    challenger_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    leader_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending, won, lost, expired
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class BetrayalLog(Base):
    __tablename__ = "betrayal_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    from_sect_id: Mapped[int] = mapped_column(ForeignKey("sects.id"))
    reason: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ==================== حیوانات و اقتصاد ====================

class Pet(Base):
    __tablename__ = "pets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    pet_type: Mapped[str] = mapped_column(String(32))  # domestic / wild
    species: Mapped[str] = mapped_column(String(64))  # گرگ، گربه، اژدهای کوچک...
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # آمار
    attack: Mapped[int] = mapped_column(Integer, default=5)
    defense: Mapped[int] = mapped_column(Integer, default=5)
    loyalty: Mapped[int] = mapped_column(Integer, default=50)  # 0-100
    
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    is_wild: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class UserWallet(Base):
    __tablename__ = "user_wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    
    coins: Mapped[int] = mapped_column(Integer, default=0)           # سکه
    spirit_stones: Mapped[int] = mapped_column(Integer, default=0)  # سنگ روحی
    last_daily_coin: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    heavenly_stones: Mapped[int] = mapped_column(Integer, default=0)  # سنگ بهشتی
    celestial_stones: Mapped[int] = mapped_column(Integer, default=0)  # سنگ آسمانی
    god_stones: Mapped[int] = mapped_column(Integer, default=0)  # سنگ خدا
    chaos_stones: Mapped[int] = mapped_column(Integer, default=0)  # سنگ هرج‌ومرج
    void_stones: Mapped[int] = mapped_column(Integer, default=0)  # سنگ پوچی
    origin_stones: Mapped[int] = mapped_column(Integer, default=0)  # سنگ ازلی
    karma_points: Mapped[int] = mapped_column(Integer, default=0)  # کارما
    destiny_stones: Mapped[int] = mapped_column(Integer, default=0)  # سنگ تقدیر
    immortal_stones: Mapped[int] = mapped_column(Integer, default=0)  # سنگ جاودان
    creation_stones: Mapped[int] = mapped_column(Integer, default=0)  # سنگ خلقت
    absolute_stones: Mapped[int] = mapped_column(Integer, default=0)  # سنگ مطلق
    faith_stones: Mapped[int] = mapped_column(Integer, default=0)  # سنگ ایمان
    dragon_coins: Mapped[int] = mapped_column(Integer, default=0)  # سکه اژدها
    
    # نرخ: ۱۰۰۰ سکه = ۱ سنگ روحی


# ==================== بُعد گروه و روح انتقام‌جو ====================

class GroupDimension(Base):
    __tablename__ = "group_dimensions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True)  # آیدی گروه تلگرام
    name: Mapped[str] = mapped_column(String(64), default="بُعد ناشناس")
    dimension_type: Mapped[str] = mapped_column(String(32), default="فانی")  # فانی/بهشتی/زیرین
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class VengefulSpirit(Base):
    __tablename__ = "vengeful_spirits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    target_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    power: Mapped[int] = mapped_column(Integer, default=30)
    reason: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class GardenPlot(Base):
    __tablename__ = "garden_plots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    plant_name: Mapped[str] = mapped_column(String(64), default="بذر معمولی")
    stage: Mapped[int] = mapped_column(Integer, default=0)  # 0 بذر .. 3 رسیده
    planted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    ready_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
