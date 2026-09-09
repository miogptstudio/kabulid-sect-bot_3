# v57 — محتوای بیشتر + رفع باگ

## باگ‌فیکس
- `safe_edit_text` / `safe_callback_answer` برای جلوگیری از `TelegramBadRequest: no text in the message to edit`
- استفاده در `advanced_systems` و `arena`
- پیش‌فرض شهر/دنیا در `world.py`: `start` / `جهان رزمی` (دیگر tehran/فانی)
- مهاجرت شهرهای قدیمی در `ensure_user_city` و `migrate_player_position`

## سیستم‌های جدید
- **مأموریت روزانه** `/quests` `/claimquest` — ۳ مأموریت تصادفی هر روز (دوئل، حرکت، خرید، تذهیب، آرش، ...)
- **القاب** `/titles` `/settitle` — نوآموز دشت، جنگجوی دره، وارث آرش، افسانه جهان رزمی و ...
- روح‌های رزمی بیشتر: کمان آرش، تیغ جهان رزمی، پنجه پوچی، سپر مهر، نفس اژدهای سرخ

## هوک‌ها
- پیشرفت مأموریت از دوئل، حرکت جهان، مشاهده /arash

## دستورات جدید
/quests /claimquest /titles /settitle
