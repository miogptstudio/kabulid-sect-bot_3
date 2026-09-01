# اتصال به Neon و ریستور داده

## ۱. متغیر محیطی
در Render → Environment:

```
DATABASE_URL=postgresql://neondb_owner:npg_sc7vYuxXBQ3A@ep-flat-unit-a50sk1hv-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require
```

(بدون channel_binding)

## ۲. ریستور بک‌آپ قدیمی
اگر فایل `2026-08-30T21_26Z.dir.tar.gz` را داری:

```bash
tar -xzf 2026-08-30T21_26Z.dir.tar.gz
export DATABASE_URL='postgresql://neondb_owner:PASSWORD@ep-....neon.tech/neondb?sslmode=require'
bash scripts_restore_neon.sh ./2026-08-30T21:26Z/kabulid_sect
```

نیاز به `postgresql-client` (دستور pg_restore) دارد.

## ۳. بعد از ریستور
ربات را Redeploy / Restart کن تا `migrate_schema` و `load_from_db` اجرا شوند.

## باگ‌های رفع‌شده در این پکیج
- import شدن `WORLD_NAME` و `START_CITY` در `bot/handlers/open_world.py` (باعث NameError در /worldpanel می‌شد)
- حذف `channel_binding=require` از URL برای سازگاری با asyncpg
- README حذف شد
