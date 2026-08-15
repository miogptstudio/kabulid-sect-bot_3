# Rank Duel Bot - ربات رتبه‌بندی و دوئل تلگرام

نسخه ۱.۰ | ربات: [@KabulidSectBot](https://t.me/KabulidSectBot)

## ویژگی‌ها

- سیستم رتبه ۵ سطحی (عضو دسته‌های پایین‌تر → ارجمند)
- سیستم XP و سطح داخل هر رتبه
- دوئل عادی (ریپلای و تگ)
- حالت نگهبان با سوالات
- جدول رتبه‌ها
- پنل مدیر
- فصل‌ها و دستاوردها (در حال توسعه)

## نصب محلی

```bash
git clone <آدرس-ریپو>
cd rank-duel-bot
python -m venv venv
source venv/bin/activate   # ویندوز: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# توکن و آیدی ادمین را در .env قرار دهید
python run.py
```

## استقرار روی Render (۲۴ ساعته)

### ۱. ساخت ریپو در GitHub
- یک ریپو جدید بساز
- فایل‌های پروژه را آپلود کن (بدون فایل `.env`)

### ۲. ساخت سرویس در Render
1. برو به [render.com](https://render.com) و ثبت‌نام کن
2. New → **Background Worker**
3. اتصال به ریپوی GitHub
4. تنظیمات:
   - **Name**: rank-duel-bot
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python run.py`

### ۳. متغیرهای محیطی (Environment Variables)
در بخش Environment این دو تا را اضافه کن:

| Key           | Value                          |
|---------------|--------------------------------|
| BOT_TOKEN     | توکن رباتت                     |
| ADMIN_IDS     | 6227792513                     |
| DATABASE_URL  | sqlite+aiosqlite:///./bot.db   |

(اگر بعداً PostgreSQL خواستی می‌تونی از Render Database استفاده کنی)

### ۴. Deploy
دکمه Deploy را بزن. بعد از چند دقیقه ربات آنلاین می‌شود.

---

**نکته مهم:**  
روی پلن رایگان Render، سرویس بعد از ۱۵ دقیقه عدم فعالیت ممکن است Sleep برود. برای ۲۴ ساعته واقعی بهتر است پلن پرداختی بگیری یا از سرویس‌های دیگر (مثل Railway یا VPS) استفاده کنی.

## مینی‌اپ وب (Telegram Mini App)

پوشه `webapp/` شامل رابط وب است.

پس از Deploy روی Koyeb (یا هر هاست):

1. آدرس مینی‌اپ مثلاً: `https://YOUR-APP.koyeb.app/webapp/`
2. در BotFather:
   - `/mybots` → ربات → **Bot Settings** → **Menu Button**
   - URL را روی همان آدرس مینی‌اپ بگذار
3. APIهای آماده:
   - `GET /api/profile?tg_id=...`
   - `GET /api/ranking`
   - `GET /api/sects`
   - `GET /health`

مینی‌اپ را حتماً از داخل تلگرام باز کنید تا شناسه کاربر در دسترس باشد.

## حافظه پایدار (خیلی مهم روی Render)

فایل SQLite با هر Deploy پاک می‌شود. برای نگه‌داشتن اطلاعات:

### روش پیشنهادی: PostgreSQL رایگان Render
1. در Render: New → PostgreSQL
2. External Database URL را کپی کن
3. در Web Service → Environment:
   - `DATABASE_URL` = همان URL (ربات خودش به asyncpg تبدیل می‌کند)

### روش جایگزین: Persistent Disk
1. Disk به سرویس وصل کن روی مسیر `/var/data`
2. Environment: `DATA_DIR=/var/data`

بدون یکی از این دو، با هر آپدیت پیشرفت کاربران از بین می‌رود.


## 📖 راهنمای کامل
راهنمای فارسی و توضیح سیستم‌ها در `GUIDE_FA.md` قرار دارد.


## Realm Progression
`bot/realm_progression.py` derives power, speed, lifespan, remaining life, recovery and perception from cultivation realm/stage.


## اصلاحات V27
- خریدهای سکه‌ای می‌توانند با ارزهای بالاتر نیز پرداخت شوند؛ کمبود سکه دیگر صرفاً به‌خاطر داشتن سنگ خدا/ارز بالاتر خطا نمی‌دهد.
- خرید متنی و خرید دکمه‌ای از یک منطق پرداخت مشترک استفاده می‌کنند.
- ارتقای ساختمان تذهیب با امضای درست تابع و پرداخت امن اصلاح شد.
- ارتقای ساختمان‌های فرقه نام‌های فارسی «برج»، «کتابخانه» و «آهنگری» را هم می‌پذیرد.
- در پرداخت با ارز خیلی بالاتر، سیستم یک واحد را به ارز پایین‌تر می‌شکند تا مابه‌التفاوت به‌صورت منطقی محاسبه شود.
- هیچ دستور حذف دادهٔ بازیکن در این نسخه اضافه نشده و مهاجرت دیتابیس فقط ستون/جدول لازم را ایجاد یا اصلاح می‌کند.


## V37 — دوئل‌های تخصصی
- `/servantduel` و `/acceptservduel`: دوئل مستقیم بین دو خدمتکار انتخاب‌شده.
- `/charduel` و `/acceptcharduel`: دوئل مستقل بین دو کاراکتر.
- دوئل خدمتکار بر اساس آمار خود خدمتکار محاسبه می‌شود و قدرت صاحب را جایگزین قدرت خدمتکار نمی‌کند.
- درخواست دوئل خدمتکار در فضای پایدار `servant_duel_pending` نگهداری می‌شود تا ری‌استارت باعث گم‌شدن درخواست نشود.
- قبل از نتیجه، بررسی می‌شود که هر دو خدمتکار هنوز در اختیار صاحبانشان باشند.
