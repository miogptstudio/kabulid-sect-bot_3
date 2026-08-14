from database.models import User
from bot.config import (
    WINS_FOR_SAME_RANK_PROMOTE,
    CONSECUTIVE_LOSSES_FOR_DEMOTE,
    GUARDIAN_WIN_PROMOTE,
    GUARDIAN_LOSS_DEMOTE
)

# ترتیب رتبه‌ها از پایین به بالا
RANKS = [
    "عضو دسته‌های پایین‌تر",
    "عضو بیرونی",
    "عضو داخلی",
    "ارشد",
    "ارجمند"
]


def get_rank_index(rank: str) -> int:
    try:
        return RANKS.index(rank)
    except ValueError:
        return 0


def can_promote(user: User) -> bool:
    return get_rank_index(user.rank) < len(RANKS) - 1


def can_demote(user: User) -> bool:
    return get_rank_index(user.rank) > 0


def promote(user: User) -> str | None:
    """ارتقا رتبه و برگرداندن رتبه جدید"""
    idx = get_rank_index(user.rank)
    if idx < len(RANKS) - 1:
        user.rank = RANKS[idx + 1]
        user.level = 1
        user.xp = 0
        user.same_rank_wins = 0
        return user.rank
    return None


def demote(user: User) -> str | None:
    """تنزل رتبه و برگرداندن رتبه جدید"""
    idx = get_rank_index(user.rank)
    if idx > 0:
        user.rank = RANKS[idx - 1]
        user.level = 1
        user.xp = 0
        user.same_rank_wins = 0
        return user.rank
    return None


def process_duel_result(winner: User, loser: User, is_guardian: bool = False) -> dict:
    """
    پردازش نتیجه دوئل و اعمال تغییرات رتبه.
    برمی‌گرداند: {"winner_promoted": bool, "loser_demoted": bool, "messages": list}
    """
    result = {
        "winner_promoted": False,
        "loser_demoted": False,
        "messages": []
    }

    if is_guardian:
        # حالت نگهبان
        if can_promote(winner):
            new_rank = promote(winner)
            result["winner_promoted"] = True
            result["messages"].append(f"🎉 {winner.full_name} به خاطر برد در حالت نگهبان به رتبه «{new_rank}» ارتقا یافت!")
        
        if can_demote(loser):
            # در نگهبان -۲ رتبه (دو بار demote)
            for _ in range(GUARDIAN_LOSS_DEMOTE):
                if can_demote(loser):
                    new_rank = demote(loser)
            result["loser_demoted"] = True
            result["messages"].append(f"📉 {loser.full_name} به خاطر باخت در حالت نگهبان به رتبه «{loser.rank}» تنزل یافت.")
    
    else:
        # دوئل عادی
        winner_idx = get_rank_index(winner.rank)
        loser_idx = get_rank_index(loser.rank)

        # برد مقابل رتبه بالاتر
        if loser_idx > winner_idx:
            if can_promote(winner):
                new_rank = promote(winner)
                result["winner_promoted"] = True
                result["messages"].append(f"🎉 {winner.full_name} با شکست دادن رتبه بالاتر به «{new_rank}» ارتقا یافت!")
        
        # برد مقابل هم‌رتبه
        elif loser_idx == winner_idx:
            winner.same_rank_wins += 1
            if winner.same_rank_wins >= WINS_FOR_SAME_RANK_PROMOTE:
                if can_promote(winner):
                    new_rank = promote(winner)
                    result["winner_promoted"] = True
                    result["messages"].append(f"🎉 {winner.full_name} با {WINS_FOR_SAME_RANK_PROMOTE} برد هم‌رتبه به «{new_rank}» ارتقا یافت!")
        
        # ۳ باخت متوالی
        if loser.loss_streak >= CONSECUTIVE_LOSSES_FOR_DEMOTE:
            if can_demote(loser):
                new_rank = demote(loser)
                result["loser_demoted"] = True
                result["messages"].append(f"📉 {loser.full_name} به خاطر {CONSECUTIVE_LOSSES_FOR_DEMOTE} باخت متوالی به «{new_rank}» تنزل یافت.")

    return result
