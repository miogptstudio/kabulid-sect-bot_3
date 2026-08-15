"""سیستم چندزبانه ربات"""
from __future__ import annotations

# tg_id -> lang code (fallback قبل از دیتابیس)
_lang_cache: dict[int, str] = {}

LANGS = {
    "fa": "فارسی",
    "en": "English",
    "ar": "العربية",
    "zh": "中文",
    "ru": "Русский",
    "tr": "Türkçe",
}

# کلید → ترجمه
T: dict[str, dict[str, str]] = {
    "choose_lang": {
        "fa": "🌐 زبان را انتخاب کن:",
        "en": "🌐 Choose your language:",
        "ar": "🌐 اختر لغتك:",
        "zh": "🌐 请选择语言：",
        "ru": "🌐 Выберите язык:",
        "tr": "🌐 Dilini seç:",
    },
    "lang_set": {
        "fa": "✅ زبان تنظیم شد: {name}",
        "en": "✅ Language set: {name}",
        "ar": "✅ تم ضبط اللغة: {name}",
        "zh": "✅ 语言已设置为：{name}",
        "ru": "✅ Язык установлен: {name}",
        "tr": "✅ Dil ayarlandı: {name}",
    },
    "lang_invalid": {
        "fa": "زبان نامعتبر. /lang",
        "en": "Invalid language. /lang",
        "ar": "لغة غير صالحة. /lang",
        "zh": "无效语言。/lang",
        "ru": "Неверный язык. /lang",
        "tr": "Geçersiz dil. /lang",
    },
    "start": {
        "fa": "سلام {name}!\nبه دنیای فرقه خوش آمدی.\nنسخه: {ver}\n\n/help راهنما | /lang زبان",
        "en": "Hello {name}!\nWelcome to the Sect World.\nVersion: {ver}\n\n/help | /lang",
        "ar": "مرحباً {name}!\nأهلاً بك في عالم الطائفة.\nالإصدار: {ver}\n\n/help | /lang",
        "zh": "你好 {name}！\n欢迎来到宗门世界。\n版本：{ver}\n\n/help | /lang",
        "ru": "Привет, {name}!\nДобро пожаловать в мир сект.\nВерсия: {ver}\n\n/help | /lang",
        "tr": "Merhaba {name}!\nTarikat dünyasına hoş geldin.\nSürüm: {ver}\n\n/help | /lang",
    },
    "only_admin": {
        "fa": "⛔️ فقط ادمین.",
        "en": "⛔️ Admin only.",
        "ar": "⛔️ للمشرف فقط.",
        "zh": "⛔️ 仅管理员。",
        "ru": "⛔️ Только админ.",
        "tr": "⛔️ Sadece admin.",
    },
    "need_gender": {
        "fa": "اول /gender بزن.",
        "en": "Set gender first: /gender",
        "ar": "حدد الجنس أولاً: /gender",
        "zh": "请先设置性别：/gender",
        "ru": "Сначала /gender",
        "tr": "Önce /gender",
    },
    "cooldown": {
        "fa": "⏳ {m} دقیقه و {s} ثانیه صبر کن.",
        "en": "⏳ Wait {m}m {s}s.",
        "ar": "⏳ انتظر {m}د {s}ث.",
        "zh": "⏳ 请等待 {m}分{s}秒。",
        "ru": "⏳ Подожди {m}м {s}с.",
        "tr": "⏳ {m}dk {s}sn bekle.",
    },
    "profile_title": {
        "fa": "👤 پروفایل {name}",
        "en": "👤 Profile {name}",
        "ar": "👤 الملف {name}",
        "zh": "👤 资料 {name}",
        "ru": "👤 Профиль {name}",
        "tr": "👤 Profil {name}",
    },
    "rank": {
        "fa": "رتبه",
        "en": "Rank",
        "ar": "الرتبة",
        "zh": "等级",
        "ru": "Ранг",
        "tr": "Rütbe",
    },
    "power": {
        "fa": "قدرت",
        "en": "Power",
        "ar": "القوة",
        "zh": "战力",
        "ru": "Сила",
        "tr": "Güç",
    },
    "cultivation": {
        "fa": "تذهیب",
        "en": "Cultivation",
        "ar": "الزراعة الروحية",
        "zh": "修炼",
        "ru": "Культивация",
        "tr": "Kültivasyon",
    },
    "gather_ok": {
        "fa": "🧘 انرژی جمع شد.",
        "en": "🧘 Energy gathered.",
        "ar": "🧘 تم جمع الطاقة.",
        "zh": "🧘 已聚气。",
        "ru": "🧘 Энергия собрана.",
        "tr": "🧘 Enerji toplandı.",
    },
    "not_found": {
        "fa": "پیدا نشد.",
        "en": "Not found.",
        "ar": "غير موجود.",
        "zh": "未找到。",
        "ru": "Не найдено.",
        "tr": "Bulunamadı.",
    },
    "no_money": {
        "fa": "سکه / ارز کافی نیست.",
        "en": "Not enough currency.",
        "ar": "الرصيد غير كافٍ.",
        "zh": "货币不足。",
        "ru": "Недостаточно средств.",
        "tr": "Yetersiz bakiye.",
    },
    "help_hint": {
        "fa": "📖 /help راهنما | /commands دستورات | /lang زبان",
        "en": "📖 /help | /commands | /lang",
        "ar": "📖 /help | /commands | /lang",
        "zh": "📖 /help | /commands | /lang",
        "ru": "📖 /help | /commands | /lang",
        "tr": "📖 /help | /commands | /lang",
    },
    "kb_cult": {
        "fa": "تذهیب کردن",
        "en": "Cultivate",
        "ar": "تأمل",
        "zh": "修炼",
        "ru": "Культивировать",
        "tr": "Kültive et",
    },
    "kb_profile": {
        "fa": "پروفایل",
        "en": "Profile",
        "ar": "الملف",
        "zh": "资料",
        "ru": "Профиль",
        "tr": "Profil",
    },
    "kb_shop": {
        "fa": "فروشگاه",
        "en": "Shop",
        "ar": "المتجر",
        "zh": "商店",
        "ru": "Магазин",
        "tr": "Dükkan",
    },
    "kb_duel": {
        "fa": "دوئل",
        "en": "Duel",
        "ar": "مبارزة",
        "zh": "决斗",
        "ru": "Дуэль",
        "tr": "Düello",
    },
    "kb_tech": {
        "fa": "تکنیکها",
        "en": "Techniques",
        "ar": "التقنيات",
        "zh": "功法",
        "ru": "Техники",
        "tr": "Teknikler",
    },
    "kb_sect": {
        "fa": "فرقه",
        "en": "Sect",
        "ar": "الطائفة",
        "zh": "宗门",
        "ru": "Секта",
        "tr": "Tarikat",
    },
    "kb_arena": {
        "fa": "آرنا",
        "en": "Arena",
        "ar": "الحلبة",
        "zh": "竞技场",
        "ru": "Арена",
        "tr": "Arena",
    },
    "kb_help": {
        "fa": "راهنما",
        "en": "Help",
        "ar": "مساعدة",
        "zh": "帮助",
        "ru": "Справка",
        "tr": "Yardım",
    },
    "kb_qi": {
        "fa": "جمع آوری چی",
        "en": "Gather Qi",
        "ar": "جمع الطاقة",
        "zh": "聚气",
        "ru": "Собрать Ци",
        "tr": "Qi topla",
    },
    "unknown_cmd": {
        "fa": "دستور ناشناخته. /help",
        "en": "Unknown command. /help",
        "ar": "أمر غير معروف. /help",
        "zh": "未知指令。/help",
        "ru": "Неизвестная команда. /help",
        "tr": "Bilinmeyen komut. /help",
    },
    "games_menu": {
        "fa": "🎮 بازیها — محدودیت ۲ دقیقه بعد از شروع",
        "en": "🎮 Games — 2 min cooldown after play",
        "ar": "🎮 ألعاب — تبريد دقيقتان",
        "zh": "🎮 游戏 — 开始后冷却2分钟",
        "ru": "🎮 Игры — КД 2 мин",
        "tr": "🎮 Oyunlar — 2 dk bekleme",
    },
    "dead": {
        "fa": "تو مردهای.",
        "en": "You are dead.",
        "ar": "أنت ميت.",
        "zh": "你已死亡。",
        "ru": "Ты мёртв.",
        "tr": "Öldün.",
    },
    "prison": {
        "fa": "🔒 در زندانی.",
        "en": "🔒 You are in prison.",
        "ar": "🔒 أنت في السجن.",
        "zh": "🔒 你在监狱中。",
        "ru": "🔒 Ты в тюрьме.",
        "tr": "🔒 Hapistesin.",
    },
}


def normalize_lang(code: str | None) -> str:
    if not code:
        return "fa"
    code = code.lower().strip()
    aliases = {
        "fa": "fa", "farsi": "fa", "persian": "fa", "فارسی": "fa",
        "en": "en", "eng": "en", "english": "en", "انگلیسی": "en",
        "ar": "ar", "arabic": "ar", "عربی": "ar",
        "zh": "zh", "cn": "zh", "chinese": "zh", "中文": "zh", "چینی": "zh",
        "ru": "ru", "russian": "ru", "روسی": "ru",
        "tr": "tr", "turkish": "tr", "ترکی": "tr", "türkçe": "tr",
    }
    return aliases.get(code, code if code in LANGS else "fa")


def set_lang(tg_id: int, code: str) -> str:
    lang = normalize_lang(code)
    if lang not in LANGS:
        return lang  # caller checks
    _lang_cache[tg_id] = lang
    return lang


def get_lang(tg_id: int, user_lang: str | None = None) -> str:
    if tg_id in _lang_cache:
        return _lang_cache[tg_id]
    if user_lang:
        return normalize_lang(user_lang)
    return "fa"


def t(key: str, lang: str = "fa", **kwargs) -> str:
    """ترجمه کلید؛ اگر نبود فارسی، بعد انگلیسی، بعد خود کلید"""
    lang = normalize_lang(lang)
    block = T.get(key) or {}
    text = block.get(lang) or block.get("fa") or block.get("en") or key
    try:
        return text.format(**kwargs) if kwargs else text
    except Exception:
        return text


def t_user(tg_id: int, key: str, user_lang: str | None = None, **kwargs) -> str:
    return t(key, get_lang(tg_id, user_lang), **kwargs)


# --- بخشهای بیشتر ---
MORE = {
    "help_title": {
        "fa": "📖 راهنما — بخش را انتخاب کن",
        "en": "📖 Help — pick a section",
        "ar": "📖 المساعدة — اختر قسماً",
        "zh": "📖 帮助 — 选择分区",
        "ru": "📖 Справка — выбери раздел",
        "tr": "📖 Yardım — bölüm seç",
    },
    "help_btn_all": {
        "fa": "📋 همه دستورات",
        "en": "📋 All commands",
        "ar": "📋 كل الأوامر",
        "zh": "📋 全部指令",
        "ru": "📋 Все команды",
        "tr": "📋 Tüm komutlar",
    },
    "sec_start": {"fa": "شروع", "en": "Start", "ar": "بداية", "zh": "开始", "ru": "Старт", "tr": "Başlangıç"},
    "sec_cult": {"fa": "تذهیب", "en": "Cultivation", "ar": "تأمل", "zh": "修炼", "ru": "Культивация", "tr": "Kültivasyon"},
    "sec_combat": {"fa": "جنگ", "en": "Combat", "ar": "قتال", "zh": "战斗", "ru": "Бой", "tr": "Savaş"},
    "sec_sect": {"fa": "فرقه", "en": "Sect", "ar": "طائفة", "zh": "宗门", "ru": "Секта", "tr": "Tarikat"},
    "sec_shop": {"fa": "فروشگاه", "en": "Shop", "ar": "متجر", "zh": "商店", "ru": "Магазин", "tr": "Dükkan"},
    "sec_social": {"fa": "اجتماعی", "en": "Social", "ar": "اجتماعي", "zh": "社交", "ru": "Социальное", "tr": "Sosyal"},
    "sec_games": {"fa": "بازی", "en": "Games", "ar": "ألعاب", "zh": "游戏", "ru": "Игры", "tr": "Oyunlar"},
    "sec_admin": {"fa": "ادمین", "en": "Admin", "ar": "مشرف", "zh": "管理", "ru": "Админ", "tr": "Admin"},
    "gather_need_tech": {
        "fa": "اول تکنیک یاد بگیر: /learntech",
        "en": "Learn a technique first: /learntech",
        "ar": "تعلم تقنية أولاً: /learntech",
        "zh": "请先学习功法：/learntech",
        "ru": "Сначала выучи технику: /learntech",
        "tr": "Önce teknik öğren: /learntech",
    },
    "gather_ok": {
        "fa": "🧘 +{n} انرژی\nقلمرو: {realm} | مرحله: {stage}\nریشه: {root}",
        "en": "🧘 +{n} energy\nRealm: {realm} | Stage: {stage}\nRoot: {root}",
        "ar": "🧘 +{n} طاقة\nالمستوى: {realm} | المرحلة: {stage}\nالجذر: {root}",
        "zh": "🧘 +{n} 能量\n境界：{realm} | 层：{stage}\n灵根：{root}",
        "ru": "🧘 +{n} энергии\nМир: {realm} | Стадия: {stage}\nКорень: {root}",
        "tr": "🧘 +{n} enerji\nAlem: {realm} | Aşama: {stage}\nKök: {root}",
    },
    "cave_empty": {
        "fa": "🕳 غار خالی بود.",
        "en": "🕳 The cave was empty.",
        "ar": "🕳 الكهف فارغ.",
        "zh": "🕳 洞穴是空的。",
        "ru": "🕳 Пещера пуста.",
        "tr": "🕳 Mağara boştu.",
    },
    "cave_loot_coin": {
        "fa": "🕳 «{cave}» — +{n} سکه",
        "en": "🕳 «{cave}» — +{n} coins",
        "ar": "🕳 «{cave}» — +{n} عملات",
        "zh": "🕳 «{cave}» — +{n} 金币",
        "ru": "🕳 «{cave}» — +{n} монет",
        "tr": "🕳 «{cave}» — +{n} jeton",
    },
    "cave_loot_spirit": {
        "fa": "🕳 «{cave}» — +{n} سنگ روحی",
        "en": "🕳 «{cave}» — +{n} spirit stones",
        "ar": "🕳 «{cave}» — +{n} أحجار روح",
        "zh": "🕳 «{cave}» — +{n} 灵石",
        "ru": "🕳 «{cave}» — +{n} духовных камней",
        "tr": "🕳 «{cave}» — +{n} ruh taşı",
    },
    "cave_cd": {
        "fa": "⏳ تا غار بعدی حدود {m} دقیقه",
        "en": "⏳ Next cave in ~{m} min",
        "ar": "⏳ الكهف التالي بعد ~{m} د",
        "zh": "⏳ 约 {m} 分钟后可再探索",
        "ru": "⏳ След. пещера через ~{m} мин",
        "tr": "⏳ Sonraki mağara ~{m} dk",
    },
    "tribe_created": {
        "fa": "🏛 قبیله «{name}» تأسیس شد. تو بنیانگذار و بزرگ و جد هستی.",
        "en": "🏛 Tribe «{name}» founded. You are founder, chief & ancestor.",
        "ar": "🏛 تأسست قبيلة «{name}». أنت المؤسس والزعيم والجد.",
        "zh": "🏛 部落「{name}」已创建。你是创始人、族长与始祖。",
        "ru": "🏛 Племя «{name}» создано. Ты основатель, вождь и предок.",
        "tr": "🏛 «{name}» kabilesi kuruldu. Kurucu, reis ve atasin.",
    },
    "trade_created": {
        "fa": "🛒 گروه بازرگانی «{name}» ساخته شد.",
        "en": "🛒 Trade guild «{name}» created.",
        "ar": "🛒 أُنشئ اتحاد تجاري «{name}».",
        "zh": "🛒 商会「{name}」已创建。",
        "ru": "🛒 Гильдия «{name}» создана.",
        "tr": "🛒 «{name}» ticaret grubu kuruldu.",
    },
    "vein_list_title": {
        "fa": "🩸 رگ معنوی (حداکثر {max} همزمان)",
        "en": "🩸 Spiritual veins (max {max})",
        "ar": "🩸 الأوردة الروحية (حد أقصى {max})",
        "zh": "🩸 灵脉（最多 {max} 条）",
        "ru": "🩸 Духовные вены (макс. {max})",
        "tr": "🩸 Manevi damarlar (en fazla {max})",
    },
    "spirit_none": {
        "fa": "روح رزمی نداری. /awaken",
        "en": "No martial spirit. /awaken",
        "ar": "لا روح قتالية. /awaken",
        "zh": "没有武魂。/awaken",
        "ru": "Нет боевого духа. /awaken",
        "tr": "Savaş ruhun yok. /awaken",
    },
    "spirit_awaken_pick": {
        "fa": "👻 نوع روح رزمی را انتخاب کن:",
        "en": "👻 Choose martial spirit type:",
        "ar": "👻 اختر نوع الروح القتالية:",
        "zh": "👻 选择武魂类型：",
        "ru": "👻 Выбери тип боевого духа:",
        "tr": "👻 Savaş ruhu türünü seç:",
    },
    "core_find_cd": {
        "fa": "⏳ تا جستجوی هسته بعدی حدود {m} دقیقه",
        "en": "⏳ Next core search in ~{m} min",
        "ar": "⏳ البحث التالي بعد ~{m} د",
        "zh": "⏳ 约 {m} 分钟后可再寻核",
        "ru": "⏳ След. поиск через ~{m} мин",
        "tr": "⏳ Sonraki arama ~{m} dk",
    },
    "core_found": {
        "fa": "💎 هسته: {name}\nنژاد: {race}\n/usecore {name}",
        "en": "💎 Core: {name}\nRace: {race}\n/usecore {name}",
        "ar": "💎 النواة: {name}\nالعرق: {race}\n/usecore {name}",
        "zh": "💎 核心：{name}\n种族：{race}\n/usecore {name}",
        "ru": "💎 Ядро: {name}\nРаса: {race}\n/usecore {name}",
        "tr": "💎 Çekirdek: {name}\nIrk: {race}\n/usecore {name}",
    },
    "married_need": {
        "fa": "باید متاهل باشی. /marry",
        "en": "You must be married. /marry",
        "ar": "يجب أن تكون متزوجاً. /marry",
        "zh": "需要先结婚。/marry",
        "ru": "Нужно быть в браке. /marry",
        "tr": "Evli olmalısın. /marry",
    },
    "child_fail": {
        "fa": "این بار فرزندی نشد. شانس: {p}%",
        "en": "No child this time. Chance: {p}%",
        "ar": "لم يولد طفل. الاحتمال: {p}%",
        "zh": "这次没有孩子。几率：{p}%",
        "ru": "Ребёнок не родился. Шанс: {p}%",
        "tr": "Bu sefer çocuk olmadı. Şans: %{p}",
    },
    "child_ok": {
        "fa": "👶✨ فرزند: {name} ({g})",
        "en": "👶✨ Child: {name} ({g})",
        "ar": "👶✨ طفل: {name} ({g})",
        "zh": "👶✨ 孩子：{name}（{g}）",
        "ru": "👶✨ Ребёнок: {name} ({g})",
        "tr": "👶✨ Çocuk: {name} ({g})",
    },
    "duel_need_reply": {
        "fa": "روی حریف ریپلای کن یا تگ بزن و /duel",
        "en": "Reply to opponent or tag + /duel",
        "ar": "رد على الخصم أو أشر + /duel",
        "zh": "回复对手或标记 + /duel",
        "ru": "Ответь на сообщение соперника + /duel",
        "tr": "Rakibe yanıt veya etiket + /duel",
    },
    "shop_title": {
        "fa": "🏪 فروشگاه و ساختمانها",
        "en": "🏪 Shop & buildings",
        "ar": "🏪 المتجر والمباني",
        "zh": "🏪 商店与建筑",
        "ru": "🏪 Магазин и здания",
        "tr": "🏪 Dükkan ve binalar",
    },
    "wallet_title": {
        "fa": "💰 کیف پول",
        "en": "💰 Wallet",
        "ar": "💰 المحفظة",
        "zh": "💰 钱包",
        "ru": "💰 Кошелёк",
        "tr": "💰 Cüzdan",
    },
    "level": {"fa": "سطح", "en": "Level", "ar": "مستوى", "zh": "等级", "ru": "Уровень", "tr": "Seviye"},
    "xp": {"fa": "تجربه", "en": "XP", "ar": "خبرة", "zh": "经验", "ru": "Опыт", "tr": "XP"},
    "wins": {"fa": "برد", "en": "Wins", "ar": "فوز", "zh": "胜", "ru": "Победы", "tr": "Galibiyet"},
    "losses": {"fa": "باخت", "en": "Losses", "ar": "خسارة", "zh": "负", "ru": "Поражения", "tr": "Mağlubiyet"},
    "city": {"fa": "شهر", "en": "City", "ar": "مدينة", "zh": "城市", "ru": "Город", "tr": "Şehir"},
    "world": {"fa": "دنیا", "en": "World", "ar": "عالم", "zh": "世界", "ru": "Мир", "tr": "Dünya"},
    "race_label": {"fa": "نژاد", "en": "Race", "ar": "عرق", "zh": "种族", "ru": "Раса", "tr": "Irk"},
    "lifespan": {"fa": "عمر", "en": "Lifespan", "ar": "عمر", "zh": "寿命", "ru": "Срок жизни", "tr": "Ömür"},
    "gender": {"fa": "جنسیت", "en": "Gender", "ar": "جنس", "zh": "性别", "ru": "Пол", "tr": "Cinsiyet"},
    "status_alive": {"fa": "زنده", "en": "Alive", "ar": "حي", "zh": "存活", "ru": "Жив", "tr": "Canlı"},
    "status_dead": {"fa": "مرده", "en": "Dead", "ar": "ميت", "zh": "死亡", "ru": "Мёртв", "tr": "Ölü"},
    "btn_accept": {"fa": "قبول ✅", "en": "Accept ✅", "ar": "قبول ✅", "zh": "接受 ✅", "ru": "Принять ✅", "tr": "Kabul ✅"},
    "btn_reject": {"fa": "رد ❌", "en": "Reject ❌", "ar": "رفض ❌", "zh": "拒绝 ❌", "ru": "Отклонить ❌", "tr": "Reddet ❌"},
    "not_for_you": {
        "fa": "این دکمه برای تو نیست.",
        "en": "This button is not for you.",
        "ar": "هذا الزر ليس لك.",
        "zh": "这个按钮不是给你的。",
        "ru": "Эта кнопка не для тебя.",
        "tr": "Bu buton sana ait değil.",
    },
    "success": {"fa": "✅ انجام شد.", "en": "✅ Done.", "ar": "✅ تم.", "zh": "✅ 完成。", "ru": "✅ Готово.", "tr": "✅ Tamam."},
    "error": {"fa": "❌ خطا.", "en": "❌ Error.", "ar": "❌ خطأ.", "zh": "❌ 错误。", "ru": "❌ Ошибка.", "tr": "❌ Hata."},
    "need_reply": {
        "fa": "روی پیام کسی ریپلای کن.",
        "en": "Reply to someone's message.",
        "ar": "رد على رسالة شخص.",
        "zh": "请回复某人的消息。",
        "ru": "Ответь на сообщение.",
        "tr": "Birinin mesajına yanıt ver.",
    },
}

for _k, _v in MORE.items():
    if _k not in T:
        T[_k] = _v


def tu_msg(message, key: str, **kwargs) -> str:
    """ترجمه بر اساس زبان فرستنده پیام"""
    tg = message.from_user.id if message and message.from_user else 0
    lang = None
    return t_user(tg, key, lang, **kwargs)


async def load_user_lang(session, user) -> str:
    lang = getattr(user, "language", None) or "fa"
    if user and getattr(user, "telegram_id", None):
        set_lang(user.telegram_id, lang)
    return normalize_lang(lang)


CODEX_GAMES = {
    "codex_title": {
        "fa": "📚 دانشنامه کوتاه",
        "en": "📚 Short codex",
        "ar": "📚 الموسوعة المختصرة",
        "zh": "📚 简要百科",
        "ru": "📚 Краткий кодекс",
        "tr": "📚 Kısa ansiklopedi",
    },
    "codex_body": {
        "fa": "• تذهیب: جمع چی و بالا رفتن قلمرو\n• ریشه: نوع انرژی معنوی\n• رگ معنوی: ضریب تذهیب (تا ۵ رگ)\n• هسته: تغییر نژاد\n• روح رزمی: بونوس قدرت دوئل\n• فرقه / قبیله / بازرگانی: گروهی\n• غار: غنیمت در شهر\n• دوئل و آرنا: رقابت\n• خدمتکار و ازدواج: اجتماعی\n\n/commands — همه دستورات\n/itemlist — دانشنامه آیتم",
        "en": "• Cultivation: gather Qi and rise realms\n• Root: spiritual energy type\n• Veins: cultivation multiplier (up to 5)\n• Cores: change race\n• Martial spirit: duel power bonus\n• Sect / tribe / trade guild: groups\n• Cave: city loot\n• Duel & arena: combat\n• Servants & marriage: social\n\n/commands — all commands\n/itemlist — item codex",
        "ar": "• التأمل: جمع الطاقة ورفع المستوى\n• الجذر: نوع الطاقة\n• الأوردة: مضاعف (حتى 5)\n• النوى: تغيير العرق\n• الروح القتالية: قوة المبارزة\n• الطائفة / القبيلة / التجارة\n• الكهف: غنائم المدينة\n• المبارزة والحلبة\n• الخدم والزواج\n\n/commands — كل الأوامر\n/itemlist — موسوعة العناصر",
        "zh": "• 修炼：聚气提升境界\n• 灵根：灵力类型\n• 灵脉：修炼倍率（最多5）\n• 核心：转换种族\n• 武魂：决斗战力加成\n• 宗门/部落/商会\n• 洞穴：城市掉落\n• 决斗与竞技场\n• 仆从与婚姻\n\n/commands — 全部指令\n/itemlist — 物品百科",
        "ru": "• Культивация: ци и миры\n• Корень: тип энергии\n• Вены: множитель (до 5)\n• Ядра: смена расы\n• Боевой дух: бонус силы\n• Секта / племя / гильдия\n• Пещера: лут города\n• Дуэль и арена\n• Слуги и брак\n\n/commands — все команды\n/itemlist — кодекс предметов",
        "tr": "• Kültivasyon: Qi topla, alem yüksel\n• Kök: enerji türü\n• Damarlar: çarpan (en fazla 5)\n• Çekirdek: ırk değiştir\n• Savaş ruhu: düello gücü\n• Tarikat / kabile / ticaret\n• Mağara: şehir ganimeti\n• Düello ve arena\n• Hizmetçi ve evlilik\n\n/commands — tüm komutlar\n/itemlist — eşya ansiklopedisi",
    },
    "item_codex_title": {
        "fa": "📚 دانشنامه آیتمها — چطور به دست میآید:",
        "en": "📚 Item codex — how to get:",
        "ar": "📚 موسوعة العناصر — كيف تحصل:",
        "zh": "📚 物品百科 — 获取方式：",
        "ru": "📚 Кодекс предметов — как получить:",
        "tr": "📚 Eşya ansiklopedisi — nasıl alınır:",
    },
    "building_codex_title": {
        "fa": "🏛 ساختمان دانشنامه",
        "en": "🏛 Building codex",
        "ar": "🏛 موسوعة المباني",
        "zh": "🏛 建筑百科",
        "ru": "🏛 Кодекс зданий",
        "tr": "🏛 Bina ansiklopedisi",
    },
    "games_title": {
        "fa": "🎮 بازیها",
        "en": "🎮 Games",
        "ar": "🎮 الألعاب",
        "zh": "🎮 游戏",
        "ru": "🎮 Игры",
        "tr": "🎮 Oyunlar",
    },
    "games_body": {
        "fa": "محدودیت: ۲ دقیقه بعد از شروع هر بازی\nمنوی /games کولداون مصرف نمیکند.\n\n/rps — سنگ کاغذ قیچی\n/dice /nard — تاس و تختهنرد\n/chess — شطرنج\n/casino مبلغ — کازینو\n/hukum — حکم\n/puzzle /riddle /mathquiz /scramble /guess /coinflip\n\nوباپ: صفحه Games",
        "en": "Cooldown: 2 minutes after starting a game\n/games menu does not consume cooldown.\n\n/rps — rock paper scissors\n/dice /nard — dice & backgammon\n/chess — chess\n/casino amount — casino\n/hukum — hukum cards\n/puzzle /riddle /mathquiz /scramble /guess /coinflip\n\nWebApp: Games page",
        "ar": "التبريد: دقيقتان بعد بدء اللعبة\nقائمة /games لا تستهلك التبريد.\n\n/rps — حجر ورقة مقص\n/dice /nard — نرد\n/chess — شطرنج\n/casino مبلغ — كازينو\n/hukum — حكم\n/puzzle /riddle /mathquiz /scramble /guess /coinflip\n\nتطبيق الويب: الألعاب",
        "zh": "冷却：开始游戏后2分钟\n/games 菜单不消耗冷却。\n\n/rps — 石头剪刀布\n/dice /nard — 骰子与双陆\n/chess — 国际象棋\n/casino 金额 — 赌场\n/hukum — 卡牌\n/puzzle /riddle /mathquiz /scramble /guess /coinflip\n\n网页应用：游戏页",
        "ru": "КД: 2 минуты после старта игры\nМеню /games не тратит КД.\n\n/rps — камень-ножницы-бумага\n/dice /nard — кости и нарды\n/chess — шахматы\n/casino сумма — казино\n/hukum — карты\n/puzzle /riddle /mathquiz /scramble /guess /coinflip\n\nWebApp: страница Games",
        "tr": "Bekleme: oyun sonrası 2 dk\n/games menüsü bekleme harcamaz.\n\n/rps — taş kağıt makas\n/dice /nard — zar ve tavla\n/chess — satranç\n/casino miktar — casino\n/hukum — kart\n/puzzle /riddle /mathquiz /scramble /guess /coinflip\n\nWebApp: Games sayfası",
    },
    "games_cd": {
        "fa": "⏳ هنوز {s} ثانیه تا بازی بعدی",
        "en": "⏳ {s}s until next game",
        "ar": "⏳ {s} ث حتى اللعبة التالية",
        "zh": "⏳ 距下次游戏还有 {s} 秒",
        "ru": "⏳ {s}с до следующей игры",
        "tr": "⏳ Sonraki oyuna {s} sn",
    },
    "webapp_label": {
        "fa": "🌐 باز کردن وباپ",
        "en": "🌐 Open WebApp",
        "ar": "🌐 فتح التطبيق",
        "zh": "🌐 打开网页应用",
        "ru": "🌐 Открыть WebApp",
        "tr": "🌐 WebApp aç",
    },
}
for _k, _v in CODEX_GAMES.items():
    if _k not in T:
        T[_k] = _v


# نگاشت جملهٔ فارسی → ترجمهها (برای متنهای باقیمانده)
PHRASES: dict[str, dict[str, str]] = {
    'قبیله\u200cای نیست. /createtribe نام': {'en': 'No tribes. /createtribe name', 'ar': 'لا قبائل.', 'zh': '没有部落。', 'ru': 'Нет племён.', 'tr': 'Kabile yok.'},
    'گروهی نیست. /tradeguild نام': {'en': 'No guilds. /tradeguild name', 'ar': 'لا اتحادات.', 'zh': '没有商会。', 'ru': 'Нет гильдий.', 'tr': 'Lonca yok.'},
    'عضو گروه نیستی.': {'en': 'Not in a guild.', 'ar': 'لست في اتحاد.', 'zh': '不在商会中。', 'ru': 'Не в гильдии.', 'tr': 'Lonca üyesi değilsin.'},
    'فقط رهبر برداشت می\u200cکند.': {'en': 'Only leader can withdraw.', 'ar': 'فقط القائد يسحب.', 'zh': '仅会长可提取。', 'ru': 'Только лидер снимает.', 'tr': 'Sadece lider çeker.'},
    'موجودی کافی نیست.': {'en': 'Insufficient balance.', 'ar': 'رصيد غير كافٍ.', 'zh': '余额不足。', 'ru': 'Недостаточно средств.', 'tr': 'Yetersiz bakiye.'},
    'فروش عمومی شمشیر کوروش به پایان رسیده. فقط /adshop ادمین.': {'en': 'Cyrus sword public sale ended. Admin /adshop only.', 'ar': 'انتهى بيع سيف كورش العام.', 'zh': '居鲁士之剑公售已结束。', 'ru': 'Публичная продажа меча Кира окончена.', 'tr': 'Kiros kılıcı halka satışı bitti.'},

    'شغل نامعتبر. /jobs': {'en': 'Invalid job. /jobs', 'ar': 'مهنة غير صالحة. /jobs', 'zh': '无效职业。/jobs', 'ru': 'Неверная профессия. /jobs', 'tr': 'Geçersiz meslek. /jobs'},
    'هر ۲۴ ساعت یک\u200cبار می\u200cتوانی شغل عوض کنی.': {'en': 'You can change job once every 24 hours.', 'ar': 'يمكنك تغيير المهنة كل 24 ساعة.', 'zh': '每24小时只能换一次职业。', 'ru': 'Менять профессию можно раз в 24 часа.', 'tr': 'Mesleği 24 saatte bir değiştirebilirsin.'},
    'قبیله هدف پیدا نشد. /tribes': {'en': 'Target tribe not found. /tribes', 'ar': 'القبيلة غير موجودة. /tribes', 'zh': '未找到目标部落。/tribes', 'ru': 'Племя не найдено. /tribes', 'tr': 'Hedef kabile yok. /tribes'},
    'فقط بزرگ یا بنیانگذار می\u200cتواند جنگ اعلام کند.': {'en': 'Only chief or founder can declare war.', 'ar': 'فقط الزعيم أو المؤسس يعلن الحرب.', 'zh': '只有族长或创始人可宣战。', 'ru': 'Только вождь или основатель объявляет войну.', 'tr': 'Sadece reis veya kurucu savaş ilan eder.'},
    'اول عضو قبیله شو. /createtribe یا /jointribe': {'en': 'Join a tribe first. /createtribe or /jointribe', 'ar': 'انضم لقبيلة أولاً.', 'zh': '请先加入部落。', 'ru': 'Сначала вступи в племя.', 'tr': 'Önce kabileye katıl.'},
    'هر ۶ ساعت یک\u200cبار اعلام جنگ.': {'en': 'Declare war once every 6 hours.', 'ar': 'إعلان الحرب كل 6 ساعات.', 'zh': '每6小时只能宣战一次。', 'ru': 'Объявлять войну раз в 6 часов.', 'tr': '6 saatte bir savaş ilan.'},

    "فقط ادمین.": {
        "en": "Admin only.", "ar": "للمشرف فقط.", "zh": "仅管理员。", "ru": "Только админ.", "tr": "Sadece admin."
    },
    "پیدا نشد.": {
        "en": "Not found.", "ar": "غير موجود.", "zh": "未找到。", "ru": "Не найдено.", "tr": "Bulunamadı."
    },
    "اول /gender بزن.": {
        "en": "Set /gender first.", "ar": "حدد /gender أولاً.", "zh": "请先 /gender。", "ru": "Сначала /gender.", "tr": "Önce /gender."
    },
    "سکه کافی نیست.": {
        "en": "Not enough coins.", "ar": "عملات غير كافية.", "zh": "金币不足。", "ru": "Недостаточно монет.", "tr": "Yetersiz jeton."
    },
    "سنگ روحی کافی نیست.": {
        "en": "Not enough spirit stones.", "ar": "أحجار روح غير كافية.", "zh": "灵石不足。", "ru": "Недостаточно духовных камней.", "tr": "Yetersiz ruh taşı."
    },
    "روی پیام کسی ریپلای کن.": {
        "en": "Reply to someone's message.", "ar": "رد على رسالة شخص.", "zh": "请回复某人的消息。", "ru": "Ответь на сообщение.", "tr": "Birinin mesajına yanıt ver."
    },
    "این دکمه برای تو نیست.": {
        "en": "This button is not for you.", "ar": "هذا الزر ليس لك.", "zh": "这个按钮不是给你的。", "ru": "Эта кнопка не для тебя.", "tr": "Bu buton sana ait değil."
    },
    "✅ انجام شد.": {
        "en": "✅ Done.", "ar": "✅ تم.", "zh": "✅ 完成。", "ru": "✅ Готово.", "tr": "✅ Tamam."
    },
    "عضو قبیله نیستی.": {
        "en": "You are not in a tribe.", "ar": "لست في قبيلة.", "zh": "你不在部落中。", "ru": "Ты не в племени.", "tr": "Kabilede değilsin."
    },
    "جنگ فعالی نیست.": {
        "en": "No active war.", "ar": "لا حرب نشطة.", "zh": "没有进行中的战争。", "ru": "Нет активной войны.", "tr": "Aktif savaş yok."
    },
    "شغلی نداری. /jobs": {
        "en": "No job. /jobs", "ar": "لا مهنة. /jobs", "zh": "没有职业。/jobs", "ru": "Нет профессии. /jobs", "tr": "Mesleğin yok. /jobs"
    },
    "هستهای نداری. /findcore": {
        "en": "No cores. /findcore", "ar": "لا نوى. /findcore", "zh": "没有核心。/findcore", "ru": "Нет ядер. /findcore", "tr": "Çekirdeğin yok. /findcore"
    },
    "روح رزمی نداری. /awaken": {
        "en": "No martial spirit. /awaken", "ar": "لا روح قتالية. /awaken", "zh": "没有武魂。/awaken", "ru": "Нет боевого духа. /awaken", "tr": "Savaş ruhun yok. /awaken"
    },
    "باید متاهل باشی. /marry": {
        "en": "You must be married. /marry", "ar": "يجب أن تكون متزوجاً. /marry", "zh": "需要先结婚。/marry", "ru": "Нужно быть в браке. /marry", "tr": "Evli olmalısın. /marry"
    },
    "فروش تمام شده.": {
        "en": "Sale ended.", "ar": "انتهى البيع.", "zh": "特卖已结束。", "ru": "Распродажа окончена.", "tr": "Satış bitti."
    },
    "قبلاً خریدی (حداکثر ۱).": {
        "en": "Already bought (max 1).", "ar": "اشتريت مسبقاً (حد أقصى 1).", "zh": "已购买（限1）。", "ru": "Уже куплено (макс. 1).", "tr": "Zaten aldın (en fazla 1)."
    },
    "آیتم پیدا نشد. /adshop": {
        "en": "Item not found. /adshop", "ar": "العنصر غير موجود. /adshop", "zh": "未找到物品。/adshop", "ru": "Предмет не найден. /adshop", "tr": "Eşya bulunamadı. /adshop"
    },
    "نژاد خدایان فقط برای ادمین": {
        "en": "God race is admin-only", "ar": "عرق الآلهة للمشرف فقط", "zh": "神族仅管理员", "ru": "Раса богов только для админа", "tr": "Tanrı ırkı sadece admin"
    },
    "دستور ناشناخته. /help": {
        "en": "Unknown command. /help", "ar": "أمر غير معروف. /help", "zh": "未知指令。/help", "ru": "Неизвестная команда. /help", "tr": "Bilinmeyen komut. /help"
    },
    "تو مردهای.": {
        "en": "You are dead.", "ar": "أنت ميت.", "zh": "你已死亡。", "ru": "Ты мёртв.", "tr": "Öldün."
    },
    "🔒 در زندانی.": {
        "en": "🔒 You are in prison.", "ar": "🔒 أنت في السجن.", "zh": "🔒 你在监狱中。", "ru": "🔒 Ты в тюрьме.", "tr": "🔒 Hapistesin."
    },
    "pong ✅ ربات آنلاین است.": {
        "en": "pong ✅ Bot is online.", "ar": "pong ✅ البوت متصل.", "zh": "pong ✅ 机器人在线。", "ru": "pong ✅ Бот онлайн.", "tr": "pong ✅ Bot çevrimiçi."
    },
    "منو حذف شد. از /help استفاده کن.": {
        "en": "Menu removed. Use /help.", "ar": "تمت إزالة القائمة. استخدم /help.", "zh": "菜单已移除。请用 /help。", "ru": "Меню убрано. Используй /help.", "tr": "Menü kaldırıldı. /help kullan."
    },
    "کیبورد حذف شد. از /help برای دستورات استفاده کن.": {
        "en": "Keyboard removed. Use /help for commands.", "ar": "تمت إزالة لوحة المفاتيح. استخدم /help.", "zh": "键盘已移除。请用 /help。", "ru": "Клавиатура убрана. Используй /help.", "tr": "Klavye kaldırıldı. Komutlar için /help."
    },
}


def tr(tg_id: int, text: str, user_lang: str | None = None) -> str:
    """ترجمه متن فارسی ثابت؛ اگر نبود همان متن برمیگردد"""
    if not text:
        return text
    lang = get_lang(tg_id, user_lang)
    if lang == "fa":
        return text
    # کلید i18n؟
    if text in T:
        return t(text, lang)
    # جمله کامل
    block = PHRASES.get(text)
    if block:
        return block.get(lang) or block.get("en") or text
    # تطبیق جزئی: اگر متن با جملهٔ شناختهشده شروع شود
    for fa, trans in PHRASES.items():
        if text.startswith(fa) or fa in text:
            rep = trans.get(lang) or trans.get("en")
            if rep:
                return text.replace(fa, rep, 1)
    return text


def answer_tr(message, text: str, **kwargs):
    """برای استفاده: await answer_tr(message, \"فقط ادمین.\")"""
    # این فقط متن را برمیگرداند — await را خودت بزن
    return tr(message.from_user.id if message and message.from_user else 0, text)

