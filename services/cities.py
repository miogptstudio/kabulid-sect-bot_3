"""شهرها، کشورها و مرحله خاص هر شهر"""
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User

# ۲۰ کشور — برای هر کشور چند شهر با مرحله خاص
CITIES = [
    # ایران — از هر استان نمونه‌های مهم (۳تایی)
    {"id": "tehran", "name": "تهران", "country": "ایران", "province": "تهران", "stage": "مرکز قدرت", "bonus": "xp", "desc": "پایتخت — +۵٪ XP دوئل"},
    {"id": "ray", "name": "ری", "country": "ایران", "province": "تهران", "stage": "کهن‌شهر", "bonus": "cult", "desc": "تذهیب کهن"},
    {"id": "shahrerey", "name": "شهریار", "country": "ایران", "province": "تهران", "stage": "حومه", "bonus": "coin", "desc": "سکه روزانه بیشتر"},
    {"id": "mashhad", "name": "مشهد", "country": "ایران", "province": "خراسان رضوی", "stage": "زیارت", "bonus": "lifespan", "desc": "+عمر خفیف"},
    {"id": "neyshabur", "name": "نیشابور", "country": "ایران", "province": "خراسان رضوی", "stage": "شعر", "bonus": "cult", "desc": "تذهیب ادبی"},
    {"id": "sabzevar", "name": "سبزوار", "country": "ایران", "province": "خراسان رضوی", "stage": "مرز شرق", "bonus": "power", "desc": "قدرت رزمی"},
    {"id": "isfahan", "name": "اصفهان", "country": "ایران", "province": "اصفهان", "stage": "هنر و طلسم", "bonus": "craft", "desc": "ساخت طلسم بهتر"},
    {"id": "kashan", "name": "کاشان", "country": "ایران", "province": "اصفهان", "stage": "کویر گل", "bonus": "herb", "desc": "گیاه معنوی"},
    {"id": "najafabad", "name": "نجف‌آباد", "country": "ایران", "province": "اصفهان", "stage": "صنعت", "bonus": "coin", "desc": "سکه"},
    {"id": "shiraz", "name": "شیراز", "country": "ایران", "province": "فارس", "stage": "ادبیات", "bonus": "cult", "desc": "تذهیب شعر"},
    {"id": "marvdasht", "name": "مرودشت", "country": "ایران", "province": "فارس", "stage": "تخت‌جمشید", "bonus": "power", "desc": "قدرت باستانی"},
    {"id": "lar", "name": "لار", "country": "ایران", "province": "فارس", "stage": "جنوب", "bonus": "trade", "desc": "تجارت"},
    {"id": "bandarabbas", "name": "بندرعباس", "country": "ایران", "province": "هرمزگان", "stage": "بندر بزرگ", "bonus": "trade", "desc": "تجارت دریایی"},
    {"id": "khamir", "name": "خمیر", "country": "ایران", "province": "هرمزگان", "stage": "ساحل آرام", "bonus": "cult", "desc": "تذهیب ساحلی"},
    {"id": "lengeh", "name": "بندر لنگه", "country": "ایران", "province": "هرمزگان", "stage": "مروارید", "bonus": "coin", "desc": "سکه دریایی"},
    {"id": "tabriz", "name": "تبریز", "country": "ایران", "province": "آذربایجان شرقی", "stage": "بازار بزرگ", "bonus": "trade", "desc": "تجارت"},
    {"id": "maragheh", "name": "مراغه", "country": "ایران", "province": "آذربایجان شرقی", "stage": "رصدخانه", "bonus": "cult", "desc": "دانش"},
    {"id": "marand", "name": "مرند", "country": "ایران", "province": "آذربایجان شرقی", "stage": "شمال‌غرب", "bonus": "power", "desc": "قدرت"},
    {"id": "urmia", "name": "ارومیه", "country": "ایران", "province": "آذربایجان غربی", "stage": "دریاچه", "bonus": "lifespan", "desc": "عمر"},
    {"id": "khoy", "name": "خوی", "country": "ایران", "province": "آذربایجان غربی", "stage": "مرز", "bonus": "power", "desc": "مرزبانی"},
    {"id": "mahabad", "name": "مهاباد", "country": "ایران", "province": "آذربایجان غربی", "stage": "کوهستان", "bonus": "hunt", "desc": "شکار بهتر"},
    {"id": "rasht", "name": "رشت", "country": "ایران", "province": "گیلان", "stage": "باران", "bonus": "herb", "desc": "گیاه"},
    {"id": "bandaranzali", "name": "بندر انزلی", "country": "ایران", "province": "گیلان", "stage": "کاسپین", "bonus": "trade", "desc": "بندر شمال"},
    {"id": "lahijan", "name": "لاهیجان", "country": "ایران", "province": "گیلان", "stage": "چای", "bonus": "coin", "desc": "سکه"},
    {"id": "sari", "name": "ساری", "country": "ایران", "province": "مازندران", "stage": "جنگل", "bonus": "hunt", "desc": "شکار"},
    {"id": "babol", "name": "بابل", "country": "ایران", "province": "مازندران", "stage": "مرکز شمال", "bonus": "cult", "desc": "تذهیب"},
    {"id": "amol", "name": "آمل", "country": "ایران", "province": "مازندران", "stage": "دماوندپایه", "bonus": "power", "desc": "قدرت کوه"},
    {"id": "ahvaz", "name": "اهواز", "country": "ایران", "province": "خوزستان", "stage": "نفت و رود", "bonus": "coin", "desc": "ثروت"},
    {"id": "abadan", "name": "آبادان", "country": "ایران", "province": "خوزستان", "stage": "پالایش", "bonus": "craft", "desc": "صنعت"},
    {"id": "dezful", "name": "دزفول", "country": "ایران", "province": "خوزستان", "stage": "پل کهن", "bonus": "power", "desc": "قدرت"},
    {"id": "kerman", "name": "کرمان", "country": "ایران", "province": "کرمان", "stage": "کویر", "bonus": "hunt", "desc": "شکار کویر"},
    {"id": "bam", "name": "بم", "country": "ایران", "province": "کرمان", "stage": "ارگ", "bonus": "power", "desc": "استحکام"},
    {"id": "rafsanjan", "name": "رفسنجان", "country": "ایران", "province": "کرمان", "stage": "پسته", "bonus": "coin", "desc": "سکه"},
    {"id": "yazd", "name": "یزد", "country": "ایران", "province": "یزد", "stage": "بادگیر", "bonus": "cult", "desc": "تذهیب خشک"},
    {"id": "ardakan", "name": "اردکان", "country": "ایران", "province": "یزد", "stage": "زرتشت", "bonus": "root", "desc": "ریشه معنوی"},
    {"id": "meybod", "name": "میبد", "country": "ایران", "province": "یزد", "stage": "سرامیک", "bonus": "craft", "desc": "ساخت"},
    {"id": "qom", "name": "قم", "country": "ایران", "province": "قم", "stage": "علم دین", "bonus": "cult", "desc": "تذهیب"},
    {"id": "kashan2", "name": "جعفریه", "country": "ایران", "province": "قم", "stage": "حومه قم", "bonus": "coin", "desc": "سکه"},
    {"id": "salafchegan", "name": "سلفچگان", "country": "ایران", "province": "قم", "stage": "جاده", "bonus": "travel", "desc": "سفر ارزان"},
    {"id": "hamedan", "name": "همدان", "country": "ایران", "province": "همدان", "stage": "گنجنامه", "bonus": "cult", "desc": "کهن"},
    {"id": "malayer", "name": "ملایر", "country": "ایران", "province": "همدان", "stage": "انگور", "bonus": "coin", "desc": "سکه"},
    {"id": "nahavand", "name": "نهاوند", "country": "ایران", "province": "همدان", "stage": "تاریخ", "bonus": "power", "desc": "قدرت"},
    {"id": "kermanshah", "name": "کرمانشاه", "country": "ایران", "province": "کرمانشاه", "stage": "بیستون", "bonus": "power", "desc": "سنگ و قدرت"},
    {"id": "paveh", "name": "پاوه", "country": "ایران", "province": "کرمانشاه", "stage": "اورامان", "bonus": "cult", "desc": "تذهیب کوه"},
    {"id": "islamabad", "name": "اسلام‌آباد غرب", "country": "ایران", "province": "کرمانشاه", "stage": "مرز غرب", "bonus": "hunt", "desc": "شکار"},
    {"id": "sanandaj", "name": "سنندج", "country": "ایران", "province": "کردستان", "stage": "کوهستان", "bonus": "power", "desc": "قدرت"},
    {"id": "marivan", "name": "مریوان", "country": "ایران", "province": "کردستان", "stage": "دریاچه زریوار", "bonus": "lifespan", "desc": "عمر"},
    {"id": "baneh", "name": "بانه", "country": "ایران", "province": "کردستان", "stage": "بازار مرز", "bonus": "trade", "desc": "تجارت"},
    {"id": "zahedan", "name": "زاهدان", "country": "ایران", "province": "سیستان و بلوچستان", "stage": "مرز شرق", "bonus": "hunt", "desc": "شکار سخت"},
    {"id": "chabahar", "name": "چابهار", "country": "ایران", "province": "سیستان و بلوچستان", "stage": "اقیانوس", "bonus": "trade", "desc": "بندر اقیانوسی"},
    {"id": "zabol", "name": "زابل", "country": "ایران", "province": "سیستان و بلوچستان", "stage": "هامون", "bonus": "cult", "desc": "تذهیب"},
    {"id": "bushehr", "name": "بوشهر", "country": "ایران", "province": "بوشهر", "stage": "خلیج", "bonus": "trade", "desc": "بندر"},
    {"id": "asalooyeh", "name": "عسلویه", "country": "ایران", "province": "بوشهر", "stage": "انرژی", "bonus": "coin", "desc": "ثروت"},
    {"id": "kangaan", "name": "کنگان", "country": "ایران", "province": "بوشهر", "stage": "گاز", "bonus": "craft", "desc": "صنعت"},
    {"id": "ardabil", "name": "اردبیل", "country": "ایران", "province": "اردبیل", "stage": "سبلان", "bonus": "cult", "desc": "کوه مقدس"},
    {"id": "khalkhal", "name": "خلخال", "country": "ایران", "province": "اردبیل", "stage": "سردسیر", "bonus": "power", "desc": "قدرت"},
    {"id": "meshginshahr", "name": "مشگین‌شهر", "country": "ایران", "province": "اردبیل", "stage": "چشمه", "bonus": "lifespan", "desc": "عمر"},
    {"id": "gorgan", "name": "گرگان", "country": "ایران", "province": "گلستان", "stage": "جنگل ابر", "bonus": "herb", "desc": "گیاه"},
    {"id": "gonbad", "name": "گنبد کاووس", "country": "ایران", "province": "گلستان", "stage": "برج", "bonus": "power", "desc": "قدرت"},
    {"id": "bandartorkman", "name": "بندر ترکمن", "country": "ایران", "province": "گلستان", "stage": "ساحل", "bonus": "trade", "desc": "تجارت"},
    {"id": "zanjan", "name": "زنجان", "country": "ایران", "province": "زنجان", "stage": "چاقو", "bonus": "power", "desc": "سلاح"},
    {"id": "abhar", "name": "ابهر", "country": "ایران", "province": "زنجان", "stage": "جاده ابریشم", "bonus": "trade", "desc": "تجارت"},
    {"id": "khorramdareh", "name": "خرمدره", "country": "ایران", "province": "زنجان", "stage": "باغ", "bonus": "herb", "desc": "گیاه"},
    {"id": "qazvin", "name": "قزوین", "country": "ایران", "province": "قزوین", "stage": "پایتخت صفوی", "bonus": "cult", "desc": "تذهیب"},
    {"id": "takestan", "name": "تاکستان", "country": "ایران", "province": "قزوین", "stage": "انگور", "bonus": "coin", "desc": "سکه"},
    {"id": "abyek", "name": "آبیک", "country": "ایران", "province": "قزوین", "stage": "جاده", "bonus": "travel", "desc": "سفر"},
    {"id": "semnan", "name": "سمنان", "country": "ایران", "province": "سمنان", "stage": "کویر راه", "bonus": "cult", "desc": "تذهیب"},
    {"id": "shahrood", "name": "شاهرود", "country": "ایران", "province": "سمنان", "stage": "جنگل ابر", "bonus": "herb", "desc": "گیاه"},
    {"id": "damghan", "name": "دامغان", "country": "ایران", "province": "سمنان", "stage": "تاریخ", "bonus": "power", "desc": "قدرت"},
    {"id": "birjand", "name": "بیرجند", "country": "ایران", "province": "خراسان جنوبی", "stage": "مرز کویر", "bonus": "hunt", "desc": "شکار"},
    {"id": "qaen", "name": "قاین", "country": "ایران", "province": "خراسان جنوبی", "stage": "زعفران", "bonus": "coin", "desc": "سکه"},
    {"id": "ferdows", "name": "فردوس", "country": "ایران", "province": "خراسان جنوبی", "stage": "قنات", "bonus": "cult", "desc": "تذهیب"},
    {"id": "bojnurd", "name": "بجنورد", "country": "ایران", "province": "خراسان شمالی", "stage": "شمال شرق", "bonus": "power", "desc": "قدرت"},
    {"id": "shirvan", "name": "شیروان", "country": "ایران", "province": "خراسان شمالی", "stage": "دشت", "bonus": "coin", "desc": "سکه"},
    {"id": "esfarayen", "name": "اسفراین", "country": "ایران", "province": "خراسان شمالی", "stage": "کوه", "bonus": "hunt", "desc": "شکار"},
    {"id": "yasuj", "name": "یاسوج", "country": "ایران", "province": "کهگیلویه و بویراحمد", "stage": "زاگرس", "bonus": "cult", "desc": "تذهیب کوه"},
    {"id": "dehdasht", "name": "دهدشت", "country": "ایران", "province": "کهگیلویه و بویراحمد", "stage": "تاریخی", "bonus": "power", "desc": "قدرت"},
    {"id": "gachsaran", "name": "گچساران", "country": "ایران", "province": "کهگیلویه و بویراحمد", "stage": "نفت", "bonus": "coin", "desc": "ثروت"},
    {"id": "khorramabad", "name": "خرم‌آباد", "country": "ایران", "province": "لرستان", "stage": "فلک‌الافلاک", "bonus": "power", "desc": "قلعه"},
    {"id": "borujerd", "name": "بروجرد", "country": "ایران", "province": "لرستان", "stage": "دشت", "bonus": "coin", "desc": "سکه"},
    {"id": "dorud", "name": "دورود", "country": "ایران", "province": "لرستان", "stage": "آبشار", "bonus": "lifespan", "desc": "عمر"},
    {"id": "shahrkord", "name": "شهرکرد", "country": "ایران", "province": "چهارمحال و بختیاری", "stage": "بام ایران", "bonus": "cult", "desc": "تذهیب ارتفاع"},
    {"id": "borujen", "name": "بروجن", "country": "ایران", "province": "چهارمحال و بختیاری", "stage": "سرد", "bonus": "power", "desc": "قدرت"},
    {"id": "lordegan", "name": "لردگان", "country": "ایران", "province": "چهارمحال و بختیاری", "stage": "جنگل", "bonus": "hunt", "desc": "شکار"},
    {"id": "ilam", "name": "ایلام", "country": "ایران", "province": "ایلام", "stage": "مرز غرب", "bonus": "power", "desc": "مرز"},
    {"id": "dehloran", "name": "دهلران", "country": "ایران", "province": "ایلام", "stage": "نفت مرز", "bonus": "coin", "desc": "سکه"},
    {"id": "mehran", "name": "مهران", "country": "ایران", "province": "ایلام", "stage": "گذرگاه", "bonus": "travel", "desc": "سفر"},
    {"id": "arak", "name": "اراک", "country": "ایران", "province": "مرکزی", "stage": "صنعت", "bonus": "craft", "desc": "ساخت"},
    {"id": "saveh", "name": "ساوه", "country": "ایران", "province": "مرکزی", "stage": "انار", "bonus": "coin", "desc": "سکه"},
    {"id": "khomein", "name": "خمین", "country": "ایران", "province": "مرکزی", "stage": "مرکز", "bonus": "cult", "desc": "تذهیب"},
    {"id": "golestan_ali", "name": "علی‌آباد", "country": "ایران", "province": "گلستان", "stage": "جنگل", "bonus": "herb", "desc": "گیاه"},
    # ۲۰ کشور همسایه و منطقه
    {"id": "kabul", "name": "کابل", "country": "افغانستان", "province": "کابل", "stage": "مرکز فرقه‌ها", "bonus": "power", "desc": "قدرت فرقه"},
    {"id": "herat", "name": "هرات", "country": "افغانستان", "province": "هرات", "stage": "هنر", "bonus": "craft", "desc": "طلسم"},
    {"id": "balkh", "name": "بلخ", "country": "افغانستان", "province": "بلخ", "stage": "تذهیب کهن", "bonus": "cult", "desc": "تذهیب"},
    {"id": "baghdad", "name": "بغداد", "country": "عراق", "province": "بغداد", "stage": "دانش", "bonus": "cult", "desc": "علم"},
    {"id": "basra", "name": "بصره", "country": "عراق", "province": "بصره", "stage": "بندر", "bonus": "trade", "desc": "تجارت"},
    {"id": "najaf", "name": "نجف", "country": "عراق", "province": "نجف", "stage": "زیارت", "bonus": "lifespan", "desc": "عمر"},
    {"id": "damascus", "name": "دمشق", "country": "سوریه", "province": "دمشق", "stage": "بازار کهن", "bonus": "trade", "desc": "بازار"},
    {"id": "aleppo", "name": "حلب", "country": "سوریه", "province": "حلب", "stage": "قلعه", "bonus": "power", "desc": "قدرت"},
    {"id": "istanbul", "name": "استانبول", "country": "ترکیه", "province": "استانبول", "stage": "دو قاره", "bonus": "trade", "desc": "تجارت بزرگ"},
    {"id": "ankara", "name": "آنکارا", "country": "ترکیه", "province": "آنکارا", "stage": "سیاست", "bonus": "xp", "desc": "XP"},
    {"id": "konya", "name": "قونیه", "country": "ترکیه", "province": "قونیه", "stage": "مولوی", "bonus": "cult", "desc": "تذهیب"},
    {"id": "samarkand", "name": "سمرقند", "country": "ازبکستان", "province": "سمرقند", "stage": "جاده‌ابریشم", "bonus": "trade", "desc": "تجارت"},
    {"id": "bukhara", "name": "بخارا", "country": "ازبکستان", "province": "بخارا", "stage": "علم", "bonus": "cult", "desc": "دانش"},
    {"id": "tashkent", "name": "تاشکند", "country": "ازبکستان", "province": "تاشکند", "stage": "پایتخت", "bonus": "coin", "desc": "سکه"},
    {"id": "delhi", "name": "دهلی", "country": "هند", "province": "دهلی", "stage": "بازار شرق", "bonus": "trade", "desc": "بازار"},
    {"id": "mumbai", "name": "بمبئی", "country": "هند", "province": "ماهاراشترا", "stage": "بندر بزرگ", "bonus": "coin", "desc": "ثروت"},
    {"id": "varanasi", "name": "وارانسی", "country": "هند", "province": "اوتار پرادش", "stage": "مقدس", "bonus": "cult", "desc": "تذهیب"},
    {"id": "beijing", "name": "پکن", "country": "چین", "province": "پکن", "stage": "امپراتوری", "bonus": "power", "desc": "قدرت"},
    {"id": "shanghai", "name": "شانگهای", "country": "چین", "province": "شانگهای", "stage": "بندر شرق", "bonus": "trade", "desc": "تجارت"},
    {"id": "xian", "name": "شی‌آن", "country": "چین", "province": "شاآنشی", "stage": "جاده‌ابریشم", "bonus": "cult", "desc": "تذهیب"},
    {"id": "moscow", "name": "مسکو", "country": "روسیه", "province": "مسکو", "stage": "شمال سرد", "bonus": "power", "desc": "قدرت"},
    {"id": "dubai", "name": "دبی", "country": "امارات", "province": "دبی", "stage": "ثروت", "bonus": "coin", "desc": "سکه زیاد"},
    {"id": "riyadh", "name": "ریاض", "country": "عربستان", "province": "ریاض", "stage": "صحرا", "bonus": "cult", "desc": "تذهیب خشک"},
    {"id": "cairo", "name": "قاهره", "country": "مصر", "province": "قاهره", "stage": "اهرام", "bonus": "power", "desc": "قدرت باستانی"},
    {"id": "islamabad_pk", "name": "اسلام‌آباد", "country": "پاکستان", "province": "اسلام‌آباد", "stage": "پایتخت", "bonus": "xp", "desc": "XP"},
    {"id": "lahore", "name": "لاهور", "country": "پاکستان", "province": "پنجاب", "stage": "فرهنگ", "bonus": "cult", "desc": "تذهیب"},
    {"id": "karachi", "name": "کراچی", "country": "پاکستان", "province": "سند", "stage": "بندر", "bonus": "trade", "desc": "تجارت"},
    {"id": "dushanbe", "name": "دوشنبه", "country": "تاجیکستان", "province": "دوشنبه", "stage": "پامیر", "bonus": "cult", "desc": "تذهیب کوه"},
    {"id": "bishkek", "name": "بیشکک", "country": "قرقیزستان", "province": "بیشکک", "stage": "استپ", "bonus": "hunt", "desc": "شکار"},
    {"id": "ashgabat", "name": "عشق‌آباد", "country": "ترکمنستان", "province": "عشق‌آباد", "stage": "صحرا", "bonus": "coin", "desc": "سکه"},
    {"id": "baku", "name": "باکو", "country": "آذربایجان", "province": "باکو", "stage": "نفت خزر", "bonus": "coin", "desc": "ثروت"},
    {"id": "yerevan", "name": "ایروان", "country": "ارمنستان", "province": "ایروان", "stage": "کوهستان", "bonus": "cult", "desc": "تذهیب"},
    {"id": "tbilisi", "name": "تفلیس", "country": "گرجستان", "province": "تفلیس", "stage": "قفقاز", "bonus": "power", "desc": "قدرت"},
    {"id": "almaty", "name": "آلماتی", "country": "قزاقستان", "province": "آلماتی", "stage": "استپ بزرگ", "bonus": "hunt", "desc": "شکار"},
    {"id": "seoul", "name": "سئول", "country": "کره جنوبی", "province": "سئول", "stage": "فناوری", "bonus": "craft", "desc": "ساخت"},
    {"id": "tokyo", "name": "توکیو", "country": "ژاپن", "province": "توکیو", "stage": "شرق دور", "bonus": "power", "desc": "قدرت"},
]

NAME_TO_ID = {}
for c in CITIES:
    NAME_TO_ID[c["name"]] = c["id"]
    NAME_TO_ID[c["id"]] = c["id"]


async def ensure_user_city(session: AsyncSession, user: User) -> str:
    if not getattr(user, "city", None):
        user.city = "tehran"
        await session.commit()
    return user.city or "tehran"


def get_city(city_id: str) -> dict:
    for c in CITIES:
        if c["id"] == city_id:
            return c
    return CITIES[0]


def list_cities_text(current_id: str, limit_per_country: int = 6) -> str:
    by_country = {}
    for c in CITIES:
        by_country.setdefault(c["country"], []).append(c)
    lines = ["🏙️ <b>کشورها و شهرها</b>\n(هر شهر مرحله خاص دارد)\n"]
    for country, cities in by_country.items():
        lines.append(f"\n🏳️ <b>{country}</b>")
        for c in cities[:limit_per_country]:
            mark = " ✅" if c["id"] == current_id else ""
            lines.append(f"• {c['name']}{mark} — مرحله: {c['stage']}")
        if len(cities) > limit_per_country:
            lines.append(f"  … و {len(cities) - limit_per_country} شهر دیگر")
    lines.append("\nسفر: /travel نام‌شهر\nجزئیات شهر فعلی: /mycity")
    return "\n".join(lines)


def city_detail_text(city: dict) -> str:
    return (
        f"🏙️ <b>{city['name']}</b>\n"
        f"کشور: {city['country']}\n"
        f"استان/منطقه: {city.get('province', '—')}\n"
        f"مرحله خاص: <b>{city['stage']}</b>\n"
        f"بونوس: {city.get('bonus', '—')}\n"
        f"{city.get('desc', '')}"
    )
