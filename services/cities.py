"""شهرها، کشورها و مرحله خاص هر شهر"""
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User

# ۲۰ کشور — برای هر کشور چند شهر با مرحله خاص
CITIES = [
    # ایران — از هر استان نمونههای مهم (۳تایی)
    {"id": "tehran", "name": "تهران", "country": "ایران", "province": "تهران", "stage": "مرکز قدرت", "bonus": "xp", "desc": "پایتخت — +۵٪ XP دوئل"},
    {"id": "ray", "name": "ری", "country": "ایران", "province": "تهران", "stage": "کهنشهر", "bonus": "cult", "desc": "تذهیب کهن"},
    {"id": "shahrerey", "name": "شهریار", "country": "ایران", "province": "تهران", "stage": "حومه", "bonus": "coin", "desc": "سکه روزانه بیشتر"},
    {"id": "mashhad", "name": "مشهد", "country": "ایران", "province": "خراسان رضوی", "stage": "زیارت", "bonus": "lifespan", "desc": "+عمر خفیف"},
    {"id": "neyshabur", "name": "نیشابور", "country": "ایران", "province": "خراسان رضوی", "stage": "شعر", "bonus": "cult", "desc": "تذهیب ادبی"},
    {"id": "sabzevar", "name": "سبزوار", "country": "ایران", "province": "خراسان رضوی", "stage": "مرز شرق", "bonus": "power", "desc": "قدرت رزمی"},
    {"id": "isfahan", "name": "اصفهان", "country": "ایران", "province": "اصفهان", "stage": "هنر و طلسم", "bonus": "craft", "desc": "ساخت طلسم بهتر"},
    {"id": "kashan", "name": "کاشان", "country": "ایران", "province": "اصفهان", "stage": "کویر گل", "bonus": "herb", "desc": "گیاه معنوی"},
    {"id": "najafabad", "name": "نجفآباد", "country": "ایران", "province": "اصفهان", "stage": "صنعت", "bonus": "coin", "desc": "سکه"},
    {"id": "shiraz", "name": "شیراز", "country": "ایران", "province": "فارس", "stage": "ادبیات", "bonus": "cult", "desc": "تذهیب شعر"},
    {"id": "marvdasht", "name": "مرودشت", "country": "ایران", "province": "فارس", "stage": "تختجمشید", "bonus": "power", "desc": "قدرت باستانی"},
    {"id": "lar", "name": "لار", "country": "ایران", "province": "فارس", "stage": "جنوب", "bonus": "trade", "desc": "تجارت"},
    {"id": "bandarabbas", "name": "بندرعباس", "country": "ایران", "province": "هرمزگان", "stage": "بندر بزرگ", "bonus": "trade", "desc": "تجارت دریایی"},
    {"id": "khamir", "name": "خمیر", "country": "ایران", "province": "هرمزگان", "stage": "ساحل آرام", "bonus": "cult", "desc": "تذهیب ساحلی"},
    {"id": "lengeh", "name": "بندر لنگه", "country": "ایران", "province": "هرمزگان", "stage": "مروارید", "bonus": "coin", "desc": "سکه دریایی"},
    {"id": "tabriz", "name": "تبریز", "country": "ایران", "province": "آذربایجان شرقی", "stage": "بازار بزرگ", "bonus": "trade", "desc": "تجارت"},
    {"id": "maragheh", "name": "مراغه", "country": "ایران", "province": "آذربایجان شرقی", "stage": "رصدخانه", "bonus": "cult", "desc": "دانش"},
    {"id": "marand", "name": "مرند", "country": "ایران", "province": "آذربایجان شرقی", "stage": "شمالغرب", "bonus": "power", "desc": "قدرت"},
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
    {"id": "islamabad", "name": "اسلامآباد غرب", "country": "ایران", "province": "کرمانشاه", "stage": "مرز غرب", "bonus": "hunt", "desc": "شکار"},
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
    {"id": "meshginshahr", "name": "مشگینشهر", "country": "ایران", "province": "اردبیل", "stage": "چشمه", "bonus": "lifespan", "desc": "عمر"},
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
    {"id": "khorramabad", "name": "خرمآباد", "country": "ایران", "province": "لرستان", "stage": "فلکالافلاک", "bonus": "power", "desc": "قلعه"},
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
    {"id": "golestan_ali", "name": "علیآباد", "country": "ایران", "province": "گلستان", "stage": "جنگل", "bonus": "herb", "desc": "گیاه"},
    # ۲۰ کشور همسایه و منطقه
    {"id": "kabul", "name": "کابل", "country": "افغانستان", "province": "کابل", "stage": "مرکز فرقهها", "bonus": "power", "desc": "قدرت فرقه"},
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
    {"id": "samarkand", "name": "سمرقند", "country": "ازبکستان", "province": "سمرقند", "stage": "جادهابریشم", "bonus": "trade", "desc": "تجارت"},
    {"id": "bukhara", "name": "بخارا", "country": "ازبکستان", "province": "بخارا", "stage": "علم", "bonus": "cult", "desc": "دانش"},
    {"id": "tashkent", "name": "تاشکند", "country": "ازبکستان", "province": "تاشکند", "stage": "پایتخت", "bonus": "coin", "desc": "سکه"},
    {"id": "delhi", "name": "دهلی", "country": "هند", "province": "دهلی", "stage": "بازار شرق", "bonus": "trade", "desc": "بازار"},
    {"id": "mumbai", "name": "بمبئی", "country": "هند", "province": "ماهاراشترا", "stage": "بندر بزرگ", "bonus": "coin", "desc": "ثروت"},
    {"id": "varanasi", "name": "وارانسی", "country": "هند", "province": "اوتار پرادش", "stage": "مقدس", "bonus": "cult", "desc": "تذهیب"},
    {"id": "beijing", "name": "پکن", "country": "چین", "province": "پکن", "stage": "امپراتوری", "bonus": "power", "desc": "قدرت"},
    {"id": "shanghai", "name": "شانگهای", "country": "چین", "province": "شانگهای", "stage": "بندر شرق", "bonus": "trade", "desc": "تجارت"},
    {"id": "xian", "name": "شیآن", "country": "چین", "province": "شاآنشی", "stage": "جادهابریشم", "bonus": "cult", "desc": "تذهیب"},
    {"id": "moscow", "name": "مسکو", "country": "روسیه", "province": "مسکو", "stage": "شمال سرد", "bonus": "power", "desc": "قدرت"},
    {"id": "dubai", "name": "دبی", "country": "امارات", "province": "دبی", "stage": "ثروت", "bonus": "coin", "desc": "سکه زیاد"},
    {"id": "riyadh", "name": "ریاض", "country": "عربستان", "province": "ریاض", "stage": "صحرا", "bonus": "cult", "desc": "تذهیب خشک"},
    {"id": "cairo", "name": "قاهره", "country": "مصر", "province": "قاهره", "stage": "اهرام", "bonus": "power", "desc": "قدرت باستانی"},
    {"id": "islamabad_pk", "name": "اسلامآباد", "country": "پاکستان", "province": "اسلامآباد", "stage": "پایتخت", "bonus": "xp", "desc": "XP"},
    {"id": "lahore", "name": "لاهور", "country": "پاکستان", "province": "پنجاب", "stage": "فرهنگ", "bonus": "cult", "desc": "تذهیب"},
    {"id": "karachi", "name": "کراچی", "country": "پاکستان", "province": "سند", "stage": "بندر", "bonus": "trade", "desc": "تجارت"},
    {"id": "dushanbe", "name": "دوشنبه", "country": "تاجیکستان", "province": "دوشنبه", "stage": "پامیر", "bonus": "cult", "desc": "تذهیب کوه"},
    {"id": "bishkek", "name": "بیشکک", "country": "قرقیزستان", "province": "بیشکک", "stage": "استپ", "bonus": "hunt", "desc": "شکار"},
    {"id": "ashgabat", "name": "عشقآباد", "country": "ترکمنستان", "province": "عشقآباد", "stage": "صحرا", "bonus": "coin", "desc": "سکه"},
    {"id": "baku", "name": "باکو", "country": "آذربایجان", "province": "باکو", "stage": "نفت خزر", "bonus": "coin", "desc": "ثروت"},
    {"id": "yerevan", "name": "ایروان", "country": "ارمنستان", "province": "ایروان", "stage": "کوهستان", "bonus": "cult", "desc": "تذهیب"},
    {"id": "tbilisi", "name": "تفلیس", "country": "گرجستان", "province": "تفلیس", "stage": "قفقاز", "bonus": "power", "desc": "قدرت"},
    {"id": "almaty", "name": "آلماتی", "country": "قزاقستان", "province": "آلماتی", "stage": "استپ بزرگ", "bonus": "hunt", "desc": "شکار"},
    {"id": "seoul", "name": "سئول", "country": "کره جنوبی", "province": "سئول", "stage": "فناوری", "bonus": "craft", "desc": "ساخت"},
    {"id": "tokyo", "name": "توکیو", "country": "ژاپن", "province": "توکیو", "stage": "شرق دور", "bonus": "power", "desc": "قدرت"},

    # ===== اروپا =====
    {"id": "london", "name": "لندن", "country": "انگلستان", "province": "انگلستان", "stage": "مه و تاج", "bonus": "trade", "desc": "تجارت جهانی"},
    {"id": "paris", "name": "پاریس", "country": "فرانسه", "province": "ایلدوفرانس", "stage": "هنر", "bonus": "cult", "desc": "تذهیب هنری"},
    {"id": "berlin", "name": "برلین", "country": "آلمان", "province": "برلین", "stage": "صنعت", "bonus": "craft", "desc": "ساخت"},
    {"id": "rome", "name": "رم", "country": "ایتالیا", "province": "لاتزیو", "stage": "امپراتوری", "bonus": "power", "desc": "قدرت باستانی"},
    {"id": "madrid", "name": "مادرید", "country": "اسپانیا", "province": "مادرید", "stage": "آفتاب", "bonus": "coin", "desc": "سکه"},
    {"id": "athens", "name": "آتن", "country": "یونان", "province": "آتیک", "stage": "اساطیر", "bonus": "cult", "desc": "تذهیب کهن"},
    {"id": "vienna", "name": "وین", "country": "اتریش", "province": "وین", "stage": "موسیقی", "bonus": "cult", "desc": "تذهیب"},
    {"id": "stockholm", "name": "استکهلم", "country": "سوئد", "province": "استکهلم", "stage": "شمال سرد", "bonus": "power", "desc": "قدرت"},
    {"id": "warsaw", "name": "ورشو", "country": "لهستان", "province": "مازوویه", "stage": "اروپای شرقی", "bonus": "xp", "desc": "XP"},
    {"id": "lisbon", "name": "لیسبون", "country": "پرتغال", "province": "لیسبون", "stage": "اقیانوس", "bonus": "trade", "desc": "بندر"},
    # ===== آفریقا =====
    {"id": "cairo2", "name": "اسکندریه", "country": "مصر", "province": "اسکندریه", "stage": "کتابخانه کهن", "bonus": "cult", "desc": "دانش"},
    {"id": "lagos", "name": "لاگوس", "country": "نیجریه", "province": "لاگوس", "stage": "آفریقای غرب", "bonus": "coin", "desc": "ثروت"},
    {"id": "nairobi", "name": "نایروبی", "country": "کنیا", "province": "نایروبی", "stage": "ساوانا", "bonus": "hunt", "desc": "شکار"},
    {"id": "cape_town", "name": "کیپتاون", "country": "آفریقای جنوبی", "province": "کیپ غربی", "stage": "دماغه", "bonus": "trade", "desc": "بندر"},
    {"id": "casablanca", "name": "کازابلانکا", "country": "مراکش", "province": "کازابلانکا", "stage": "مغرب", "bonus": "trade", "desc": "تجارت"},
    {"id": "addis", "name": "آدیسآبابا", "country": "اتیوپی", "province": "آدیس", "stage": "بلندای آفریقا", "bonus": "cult", "desc": "تذهیب"},
    {"id": "accra", "name": "آکرا", "country": "غنا", "province": "آکرا", "stage": "طلای غرب", "bonus": "coin", "desc": "سکه"},
    {"id": "tunis", "name": "تونس", "country": "تونس", "province": "تونس", "stage": "مدیترانه", "bonus": "trade", "desc": "بندر"},
    # ===== آمریکای شمالی =====
    {"id": "newyork", "name": "نیویورک", "country": "آمریکا", "province": "نیویورک", "stage": "ابرشهر", "bonus": "trade", "desc": "تجارت بزرگ"},
    {"id": "losangeles", "name": "لسآنجلس", "country": "آمریکا", "province": "کالیفرنیا", "stage": "غرب", "bonus": "coin", "desc": "سکه"},
    {"id": "chicago", "name": "شیکاگو", "country": "آمریکا", "province": "ایلینوی", "stage": "بادها", "bonus": "power", "desc": "قدرت"},
    {"id": "toronto", "name": "تورنتو", "country": "کانادا", "province": "انتاریو", "stage": "شمال", "bonus": "xp", "desc": "XP"},
    {"id": "vancouver", "name": "ونکوور", "country": "کانادا", "province": "بریتیش کلمبیا", "stage": "اقیانوس آرام", "bonus": "trade", "desc": "بندر"},
    {"id": "mexico_city", "name": "مکزیکوسیتی", "country": "مکزیک", "province": "مکزیکو", "stage": "آزتک", "bonus": "power", "desc": "قدرت باستانی"},
    {"id": "havana", "name": "هاوانا", "country": "کوبا", "province": "هاوانا", "stage": "کارائیب", "bonus": "coin", "desc": "سکه"},
    # ===== آمریکای جنوبی =====
    {"id": "saopaulo", "name": "سائوپائولو", "country": "برزیل", "province": "سائوپائولو", "stage": "جنوب بزرگ", "bonus": "coin", "desc": "ثروت"},
    {"id": "riodejaneiro", "name": "ریودوژانیرو", "country": "برزیل", "province": "ریو", "stage": "ساحل طلایی", "bonus": "cult", "desc": "تذهیب"},
    {"id": "buenosaires", "name": "بوئنوسآیرس", "country": "آرژانتین", "province": "بوئنوسآیرس", "stage": "پامپا", "bonus": "trade", "desc": "تجارت"},
    {"id": "lima", "name": "لیما", "country": "پرو", "province": "لیما", "stage": "اینکا", "bonus": "power", "desc": "قدرت کهن"},
    {"id": "bogota", "name": "بوگوتا", "country": "کلمبیا", "province": "بوگوتا", "stage": "آند", "bonus": "cult", "desc": "تذهیب ارتفاع"},
    {"id": "santiago", "name": "سانتیاگو", "country": "شیلی", "province": "سانتیاگو", "stage": "رشتهکوه", "bonus": "power", "desc": "قدرت"},
    # ===== اقیانوسیه =====
    {"id": "sydney", "name": "سیدنی", "country": "استرالیا", "province": "نیوساوتولز", "stage": "اپرا و بندر", "bonus": "trade", "desc": "بندر"},
    {"id": "melbourne", "name": "ملبورن", "country": "استرالیا", "province": "ویکتوریا", "stage": "فرهنگ", "bonus": "cult", "desc": "تذهیب"},
    {"id": "auckland", "name": "اوکلند", "country": "نیوزیلند", "province": "اوکلند", "stage": "جزایر", "bonus": "lifespan", "desc": "عمر"},
    {"id": "wellington", "name": "ولینگتون", "country": "نیوزیلند", "province": "ولینگتون", "stage": "پایتخت باد", "bonus": "power", "desc": "قدرت"},
    {"id": "suva", "name": "سووا", "country": "فیجی", "province": "سووا", "stage": "اقیانوس آرام", "bonus": "herb", "desc": "گیاه"},
    # ===== آسیای شرق و جنوبشرق =====
    {"id": "bangkok", "name": "بانکوک", "country": "تایلند", "province": "بانکوک", "stage": "معابد", "bonus": "cult", "desc": "تذهیب"},
    {"id": "jakarta", "name": "جاکارتا", "country": "اندونزی", "province": "جاکارتا", "stage": " مجمعالجزایر", "bonus": "trade", "desc": "تجارت"},
    {"id": "manila", "name": "مانیل", "country": "فیلیپین", "province": "مانیل", "stage": "جزایر", "bonus": "coin", "desc": "سکه"},
    {"id": "hanoi", "name": "هانوی", "country": "ویتنام", "province": "هانوی", "stage": "شرقهندوچین", "bonus": "cult", "desc": "تذهیب"},
    {"id": "singapore", "name": "سنگاپور", "country": "سنگاپور", "province": "سنگاپور", "stage": "بندر جهانی", "bonus": "trade", "desc": "تجارت بزرگ"},
    {"id": "kualalumpur", "name": "کوالالامپور", "country": "مالزی", "province": "کوالالامپور", "stage": "برجها", "bonus": "coin", "desc": "ثروت"},
    # ===== آسیای مرکزی و قفقاز بیشتر =====
    {"id": "ulaanbaatar", "name": "اولانباتور", "country": "مغولستان", "province": "اولانباتور", "stage": "استپ مغول", "bonus": "hunt", "desc": "شکار"},
    {"id": "colombo", "name": "کلمبو", "country": "سریلانکا", "province": "کلمبو", "stage": "جزیره چای", "bonus": "herb", "desc": "گیاه"},
    {"id": "kathmandu", "name": "کاتماندو", "country": "نپال", "province": "کاتماندو", "stage": "هیمالیا", "bonus": "cult", "desc": "تذهیب کوه"},
    {"id": "dhaka", "name": "داکا", "country": "بنگلادش", "province": "داکا", "stage": "دلتا", "bonus": "coin", "desc": "سکه"},

]


# دنیای بهشتی — ۵۰ شهر
HEAVEN_CITIES = [
    {"id": "heaven_1", "name": "قصر نور", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-1", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_2", "name": "باغ جاویدان", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-2", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_3", "name": "قله فرشتگان", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-3", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_4", "name": "دریاچه بلور", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-4", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_5", "name": "شهر طلای سپید", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-5", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_6", "name": "دروازه رحمت", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-6", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_7", "name": "کاخ ستارگان", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-7", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_8", "name": "جزیره ابر", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-8", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_9", "name": "معبد آفتاب", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-9", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_10", "name": "رودخانه شهد", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-10", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_11", "name": "کوه زمرد", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-11", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_12", "name": "دشت نیلوفر", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-12", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_13", "name": "برج عروج", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-13", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_14", "name": "چشمه حیات", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-14", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_15", "name": "بازار نورانی", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-15", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_16", "name": "قلعه سپیده", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-16", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_17", "name": "جنگل کریستال", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-17", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_18", "name": "دره زمزم", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-18", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_19", "name": "شهر همهمه", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-19", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_20", "name": "صومعه سپید", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-20", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_21", "name": "آسمانآباد", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-21", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_22", "name": "فردوس کوچک", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-22", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_23", "name": "گلدسته اعلی", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-23", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_24", "name": "کوی فرشته", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-24", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_25", "name": "بندر مهتاب", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-25", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_26", "name": "تپه یاقوت", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-26", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_27", "name": "وادی سلام", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-27", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_28", "name": "کاخ عدن", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-28", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_29", "name": "شهر نغمه", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-29", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_30", "name": "پالیز بهشت", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-30", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_31", "name": "مناره نور", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-31", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_32", "name": "دریاچه آینه", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-32", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_33", "name": "قله همای", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-33", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_34", "name": "دژ نورانی", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-34", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_35", "name": "باغ سیب طلا", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-35", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_36", "name": "چشمه زمزم بهشتی", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-36", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_37", "name": "سرای فرزانگان", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-37", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_38", "name": "برج بلورین", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-38", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_39", "name": "جزیره ققنوس", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-39", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_40", "name": "شهر سروش", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-40", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_41", "name": "کوی رضوان", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-41", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_42", "name": "دشت ابریشم", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-42", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_43", "name": "معبد آرامش", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-43", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_44", "name": "قلعه سپهر", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-44", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_45", "name": "رودخانه نور", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-45", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_46", "name": "کاخ هشتبهشت", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-46", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_47", "name": "شهر صفا", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-47", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_48", "name": "تپه نقره", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-48", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_49", "name": "بندر فردوس", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-49", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
    {"id": "heaven_50", "name": "آرامگاه قدیسان", "country": "دنیای بهشتی", "province": "آسمان", "stage": "بهشتی-50", "bonus": "cult", "desc": "شهر بهشتی", "world": "بهشتی"},
]

# دنیای زیرین — ۵۰ شهر
UNDER_CITIES = [
    {"id": "under_1", "name": "گورستان خاکستر", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-1", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_2", "name": "دره شیاطین", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-2", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_3", "name": "قلعه استخوان", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-3", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_4", "name": "رودخانه خون", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-4", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_5", "name": "شهر سایه", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-5", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_6", "name": "مغاک اژدها", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-6", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_7", "name": "بازار ارواح", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-7", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_8", "name": "دژ نفرین", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-8", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_9", "name": "چاه پوچی", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-9", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_10", "name": "جنگل مرده", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-10", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_11", "name": "کوه گدازه", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-11", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_12", "name": "زندان ابدی", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-12", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_13", "name": "معبد اهریمن", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-13", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_14", "name": "باتلاق زهر", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-14", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_15", "name": "شهر نفرینشده", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-15", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_16", "name": "قصر تاریکی", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-16", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_17", "name": "غار خونآشام", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-17", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_18", "name": "دشت اسکلت", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-18", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_19", "name": "برج عذاب", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-19", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_20", "name": "بندر دوزخ", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-20", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_21", "name": "وادی ناله", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-21", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_22", "name": "کوره جهنم", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-22", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_23", "name": "جزیره مار", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-23", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_24", "name": "تپه جمجمه", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-24", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_25", "name": "سرای شیاطین", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-25", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_26", "name": "دریاچه اسید", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-26", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_27", "name": "قلعه سایه", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-27", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_28", "name": "معبد خون", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-28", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_29", "name": "گودال فراموشی", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-29", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_30", "name": "شهر بینام", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-30", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_31", "name": "دروازه دوزخ", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-31", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_32", "name": "کاخ اهریمن", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-32", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_33", "name": "رودخانه آتش", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-33", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_34", "name": "دژ زامبی", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-34", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_35", "name": "جنگل خار", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-35", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_36", "name": "مغاک ابدی", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-36", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_37", "name": "بازار نفرین", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-37", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_38", "name": "چشمه زهر", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-38", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_39", "name": "قله شیطان", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-39", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_40", "name": "آرامگاه ملعون", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-40", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_41", "name": "شهر خاکستر", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-41", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_42", "name": "بندر نفرین", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-42", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_43", "name": "تپه مردگان", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-43", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_44", "name": "صومعه تاریک", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-44", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_45", "name": "کوی شیاطین", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-45", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_46", "name": "دشت نفرین", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-46", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_47", "name": "برج خون", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-47", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_48", "name": "غار پوچی", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-48", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_49", "name": "جزیره نفرین", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-49", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
    {"id": "under_50", "name": "سرای عذاب", "country": "دنیای زیرین", "province": "مغاک", "stage": "زیرین-50", "bonus": "hunt", "desc": "شهر زیرین", "world": "زیرین"},
]


# ——— دنیاهای بیشتر (هر کدام ۱۵ شهر) ———
def _gen_world_cities(prefix: str, world: str, country: str, province: str, names: list, bonus: str):
    out = []
    for i, name in enumerate(names, 1):
        out.append({
            "id": f"{prefix}_{i}",
            "name": name,
            "country": country,
            "province": province,
            "stage": f"{world}-{i}",
            "bonus": bonus,
            "desc": f"شهر دنیای {world}",
            "world": world,
        })
    return out

DEMON_CITIES = _gen_world_cities("demon", "شیطانی", "دنیای شیطانی", "جهنم", [
    "قلعه ابلیس", "دره آتش", "شهر شاخ", "باتلاق خون", "برج گناه",
    "معبد تاریک", "رود گوگرد", "غار اهریمن", "دشت نفرین", "کاخ شیطان",
    "جزیره دوزخ", "بازار روح", "چاه عذاب", "کوه آتشفشان", "سرای وسوسه",
], "power")

SKY_CITIES = _gen_world_cities("sky", "آسمانی", "دنیای آسمانی", "افلاک", [
    "قصر رعد", "شهر باد", "جزیره ابر زرین", "معبد ستاره", "دریاچه آسمان",
    "برج صاعقه", "دشت ابر", "کاخ ماه", "دروازه افلاک", "باغ باد",
    "رود نور", "قلعه عقاب", "سرای رعد", "کوه آسمان", "بندر ابر",
], "cult")

SPIRIT_CITIES = _gen_world_cities("spirit", "روحی", "دنیای روحی", "عالم ارواح", [
    "شهر شبح", "دره ارواح", "معبد روح", "دریاچه مه", "قصر شفاف",
    "غار یادبود", "دشت خاموش", "برج روح", "جزیره رویا", "سرای اجداد",
    "چشمه روح", "کوی مردگان آرام", "بازار خاطره", "کوه مه", "آرامگاه نور",
], "cult")

ICE_CITIES = _gen_world_cities("ice", "یخی", "دنیای یخی", "قطب", [
    "قلعه یخ", "شهر برف", "غار یخبندان", "دریاچه منجمد", "دشت سپید",
    "برج بلور یخ", "بندر شمال", "معبد سرما", "کوه یخچال", "سرای قطبی",
    "جزیره منجمد", "رود یخ", "کاخ ملکه برف", "دره کولاک", "چشمه یخ",
], "power")

FIRE_CITIES = _gen_world_cities("fire", "آتشین", "دنیای آتشین", "ماگما", [
    "شهر گدازه", "قلعه آتش", "دهانه آتشفشان", "رود ماگما", "دشت خاکستر",
    "معبد شعله", "برج آتش", "غار گدازه", "جزیره سوزان", "سرای آذر",
    "بازار زغال", "کوه دود", "چشمه جوشان", "کاخ شعلهور", "دره آتش",
], "power")

VOID_CITIES = _gen_world_cities("void", "پوچی", "دنیای پوچی", "خلا", [
    "شهر هیچ", "دروازه پوچی", "دشت خاموش مطلق", "برج خلأ", "غار عدم",
    "جزیره محو", "سرای نیستی", "رود ناپیدا", "معبد خالی", "کوه سایه",
    "بازار فراموشی", "قصر بیشکل", "چاه پوچی", "کوی محو", "آرامگاه خلأ",
], "cult")

ETHEREAL_CITIES = _gen_world_cities("eth", "ایتری", "دنیای ایتری", "اتر", [
    "شهر اتر", "قصر شفاف", "دریاچه نور رقیق", "برج ایتری", "دشت مه نور",
    "معبد اتر", "غار بلور اتر", "جزیره شناور", "سرای رقیق", "رود اتر",
    "کوه مهتاب", "بازار انرژی", "چشمه اتر", "کاخ شناور", "دروازه ایتری",
], "cult")

FOREST_CITIES = _gen_world_cities("forest", "جنگلی", "دنیای جنگلی", "بیشه", [
    "شهر درخت", "قلعه ریشه", "دهکده برگ", "دریاچه سبز", "دشت گل وحشی",
    "معبد درخت کهن", "غار خزهای", "جزیره بیشه", "سرای دروید", "رود جنگل",
    "کوه سبز", "بازار گیاه", "چشمه حیات سبز", "کاخ شاخه", "دره مه جنگل",
], "herb")

STAR_CITIES = _gen_world_cities("star", "ستارهای", "دنیای ستارهای", "کهکشان", [
    "شهر ستاره", "قلعه کهکشان", "بندر شهاب", "دریاچه کیهان", "دشت شهاببار",
    "معبد صورتفلکی", "غار شهاب", "جزیره نپتون", "سرای کیهان", "رود کهکشان",
    "کوه ستاره", "بازار شهاب", "چشمه نور ستاره", "کاخ اوریون", "دروازه کهکشان",
], "xp")

DRAGON_CITIES = _gen_world_cities("dragon", "اژدهایی", "دنیای اژدها", "درهاژدها", [
    "لانه اژدها", "شهر فلس", "قلعه بال", "دریاچه آتشدم", "دشت اژدها",
    "معبد اژدهای کهن", "غار گنج اژدها", "جزیره بال", "سرای اژدهاشاه", "رود طلا",
    "کوه اژدها", "بازار فلس", "چشمه خون اژدها", "کاخ بالزرین", "دره غرش",
], "power")

EXTRA_WORLD_CITIES = (
    DEMON_CITIES + SKY_CITIES + SPIRIT_CITIES + ICE_CITIES + FIRE_CITIES
    + VOID_CITIES + ETHEREAL_CITIES + FOREST_CITIES + STAR_CITIES + DRAGON_CITIES
)

WORLD_DEFAULT_CITY = {
    "فانی": "tehran",
    "بهشتی": "heaven_1",
    "زیرین": "under_1",
    "شیطانی": "demon_1",
    "آسمانی": "sky_1",
    "روحی": "spirit_1",
    "یخی": "ice_1",
    "آتشین": "fire_1",
    "پوچی": "void_1",
    "ایتری": "eth_1",
    "جنگلی": "forest_1",
    "ستارهای": "star_1",
    "اژدهایی": "dragon_1",
}

ALL_WORLDS = list(WORLD_DEFAULT_CITY.keys())


ALL_CITIES = CITIES + HEAVEN_CITIES + UNDER_CITIES + EXTRA_WORLD_CITIES

# سلاح مخفی اولین بازدید (id شهر → نام، قدرت)
CITY_HIDDEN_WEAPONS = {
    "tehran": ("کلت پنهان", 25),
    "mashhad": ("تفنگ شکاری", 30),
    "isfahan": ("تپانچه قدیمی", 22),
    "shiraz": ("اسلحه قاچاق", 28),
    "tabriz": ("تفنگ کوهستان", 27),
    "bandarabbas": ("تفنگ ساحلی", 26),
    "ahvaz": ("تپانچه نفتی", 24),
    "kerman": ("تفنگ کویر", 23),
    "rasht": ("تفنگ جنگلی", 21),
    "newyork": ("برتا", 35),
    "moscow": ("کلاشنیکف کهنه", 40),
    "heaven_1": ("نیزه نور", 45),
    "heaven_5": ("کمان فرشته", 42),
    "heaven_10": ("شمشیر سپید", 50),
    "heaven_20": ("تیر بلورین", 48),
    "heaven_30": ("سپر نورانی", 40),
    "under_1": ("خنجر استخوان", 38),
    "under_5": ("تیر زهرآگین", 40),
    "under_10": ("شمشیر خون", 52),
    "under_20": ("تبر شیطان", 55),
    "under_30": ("داس مرگ", 60),
}

# بازسازی نقشه نام
NAME_TO_ID = {}
for c in ALL_CITIES:
    NAME_TO_ID[c["name"]] = c["id"]
    NAME_TO_ID[c["id"]] = c["id"]

async def ensure_user_city(session: AsyncSession, user: User) -> str:
    if not getattr(user, "city", None):
        user.city = "tehran"
        await session.commit()
    return user.city or "tehran"


def get_city(city_id: str) -> dict:
    for c in ALL_CITIES:
        if c["id"] == city_id:
            return c
    return ALL_CITIES[0]


def cities_for_world(world: str) -> list:
    w = world or "فانی"
    if w == "بهشتی":
        return HEAVEN_CITIES
    if w == "زیرین":
        return UNDER_CITIES
    if w == "شیطانی":
        return DEMON_CITIES
    if w == "آسمانی":
        return SKY_CITIES
    if w == "روحی":
        return SPIRIT_CITIES
    if w == "یخی":
        return ICE_CITIES
    if w == "آتشین":
        return FIRE_CITIES
    if w == "پوچی":
        return VOID_CITIES
    if w == "ایتری":
        return ETHEREAL_CITIES
    if w == "جنگلی":
        return FOREST_CITIES
    if w == "ستارهای":
        return STAR_CITIES
    if w == "اژدهایی":
        return DRAGON_CITIES
    return CITIES


def list_cities_text(current_id: str, limit_per_country: int = 6, world: str = "فانی") -> str:
    pool = cities_for_world(world)
    by_country = {}
    for c in pool:
        by_country.setdefault(c["country"], []).append(c)
    lines = ["🏙️ <b>کشورها و شهرها</b>\n(هر شهر مرحله خاص دارد)\n"]
    for country, cities in by_country.items():
        lines.append(f"\n🏳️ <b>{country}</b>")
        for c in cities[:limit_per_country]:
            mark = " ✅" if c["id"] == current_id else ""
            lines.append(f"• {c['name']}{mark} — مرحله: {c['stage']}")
        if len(cities) > limit_per_country:
            lines.append(f"  … و {len(cities) - limit_per_country} شهر دیگر")
    lines.append("\nسفر: /travel نامشهر | کاوش: /explorecity | شهر من: /mycity")
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
