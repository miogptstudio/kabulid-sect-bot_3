from database.models import User
from bot.config import XP_PER_WIN, XP_PER_LOSS, XP_PER_GUARDIAN_WIN, XP_NEEDED_PER_LEVEL
from services.ranking import promote, can_promote


def add_xp(user: User, amount: int) -> dict:
    """
    اضافه کردن XP و چک کردن ارتقای سطح / رتبه
    """
    result = {
        "leveled_up": False,
        "rank_up": False,
        "new_level": user.level,
        "new_rank": user.rank,
        "messages": []
    }

    user.xp += amount

    # چک کردن ارتقای سطح
    while user.xp >= XP_NEEDED_PER_LEVEL:
        user.xp -= XP_NEEDED_PER_LEVEL
        user.level += 1
        result["leveled_up"] = True
        result["new_level"] = user.level
        result["messages"].append(f"⬆️ {user.full_name} به سطح {user.level} رسید!")

        # هر ۳ سطح یک بار شانس ارتقای رتبه (یا می‌تونی قانون دیگه‌ای بذاری)
        # فعلاً فقط با قوانین اصلی رتبه ارتقا می‌دهیم

    return result


def process_xp_for_duel(winner: User, loser: User, is_guardian: bool = False) -> list[str]:
    messages = []

    if is_guardian:
        res = add_xp(winner, XP_PER_GUARDIAN_WIN)
        messages.extend(res["messages"])
        # بازنده XP نمی‌گیره یا کمی منفی (فعلاً صفر)
    else:
        res_win = add_xp(winner, XP_PER_WIN)
        res_lose = add_xp(loser, XP_PER_LOSS)  # حتی بازنده کمی XP می‌گیره
        messages.extend(res_win["messages"])
        messages.extend(res_lose["messages"])

    return messages
