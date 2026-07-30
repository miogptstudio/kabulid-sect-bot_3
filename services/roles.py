from database.models import (
    User, ROLE_LEADER, ROLE_DEPUTY, ROLE_ARJOMAND, ROLE_SENIOR, ROLE_MEMBER
)

# سطح دسترسی نقش‌ها (عدد بالاتر = قدرت بیشتر)
ROLE_POWER = {
    ROLE_LEADER: 100,
    ROLE_DEPUTY: 80,
    ROLE_ARJOMAND: 60,
    ROLE_SENIOR: 40,
    ROLE_MEMBER: 10,
}


def get_power(user: User) -> int:
    return ROLE_POWER.get(user.role, 10)


def can_manage(actor: User, target: User) -> bool:
    """آیا actor می‌تونه روی target عمل مدیریتی انجام بده؟"""
    if actor.role == ROLE_LEADER:
        return True
    return get_power(actor) > get_power(target)


def can_restrict(actor: User) -> bool:
    return actor.role in (ROLE_LEADER, ROLE_DEPUTY, ROLE_ARJOMAND, ROLE_SENIOR)


def can_promote_demote(actor: User) -> bool:
    return actor.role in (ROLE_LEADER, ROLE_DEPUTY)


def can_manage_missions(actor: User) -> bool:
    return actor.role in (ROLE_LEADER, ROLE_DEPUTY, ROLE_ARJOMAND)


def can_set_deputy(actor: User) -> bool:
    return actor.role == ROLE_LEADER


def can_ban(actor: User) -> bool:
    return actor.role in (ROLE_LEADER, ROLE_DEPUTY)
