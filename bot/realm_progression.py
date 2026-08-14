
"""Realm progression: derived stats from cultivation realm/level."""
from dataclasses import dataclass

@dataclass(frozen=True)
class RealmBonus:
    speed_mult: float
    power_mult: float
    lifespan_years: int
    recovery_mult: float
    perception_mult: float

# Generic progression table; projects can extend/override this mapping.
REALM_BONUSES = {
    1: RealmBonus(1.00, 1.00, 80, 1.00, 1.00),
    2: RealmBonus(1.15, 1.25, 150, 1.10, 1.10),
    3: RealmBonus(1.35, 1.60, 300, 1.25, 1.25),
    4: RealmBonus(1.60, 2.10, 600, 1.45, 1.45),
    5: RealmBonus(2.00, 2.80, 1200, 1.70, 1.70),
    6: RealmBonus(2.60, 3.80, 2500, 2.00, 2.00),
    7: RealmBonus(3.40, 5.20, 5000, 2.40, 2.40),
    8: RealmBonus(4.50, 7.20, 10000, 2.90, 2.90),
    9: RealmBonus(6.00, 10.0, 25000, 3.50, 3.50),
    10: RealmBonus(8.00, 14.0, 60000, 4.20, 4.20),
    11: RealmBonus(11.0, 20.0, 150000, 5.00, 5.00),
    12: RealmBonus(15.0, 30.0, 400000, 6.00, 6.00),
    13: RealmBonus(22.0, 45.0, 1000000, 7.50, 7.50),
    14: RealmBonus(35.0, 70.0, 3000000, 9.00, 9.00),
    15: RealmBonus(60.0, 120.0, 10000000, 12.0, 12.0),
}

def realm_index(realm: int, stage: int = 1) -> int:
    # Supports very high realms without crashing; each 15-stage realm is a tier.
    realm = max(1, int(realm))
    stage = max(1, int(stage))
    return min(15, 1 + (realm - 1) % 15)

def get_realm_bonus(realm: int, stage: int = 1) -> RealmBonus:
    idx = realm_index(realm, stage)
    base = REALM_BONUSES[idx]
    # Stages progressively improve derived stats inside a realm.
    s = min(15, max(1, int(stage)))
    factor = 1.0 + (s - 1) * 0.035
    return RealmBonus(
        base.speed_mult * factor,
        base.power_mult * factor,
        int(base.lifespan_years * factor),
        base.recovery_mult * factor,
        base.perception_mult * factor,
    )

def derived_stats(base_power: int, base_speed: int, realm: int, stage: int = 1,
                  current_age: int = 0) -> dict:
    b = get_realm_bonus(realm, stage)
    return {
        "power": int(max(0, base_power) * b.power_mult),
        "speed": int(max(0, base_speed) * b.speed_mult),
        "lifespan": b.lifespan_years,
        "remaining_life": max(0, b.lifespan_years - max(0, int(current_age))),
        "recovery": b.recovery_mult,
        "perception": b.perception_mult,
    }
