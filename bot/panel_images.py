from pathlib import Path
ASSET_DIR = Path(__file__).resolve().parent.parent / "assets" / "panels"
PANEL_IMAGES = {
    "help": ASSET_DIR/"help.jpg", "duel": ASSET_DIR/"duel.jpg",
    "cultivation": ASSET_DIR/"cultivation.jpg", "servants": ASSET_DIR/"servants.jpg",
    "marriage": ASSET_DIR/"marriage.jpg", "sect": ASSET_DIR/"sect.jpg",
    "kingdom": ASSET_DIR/"kingdom.jpg", "arena": ASSET_DIR/"arena.jpg",
    "ranking": ASSET_DIR/"ranking.jpg", "market": ASSET_DIR/"market.jpg",
    "shop": ASSET_DIR/"shop.jpg", "jobs": ASSET_DIR/"jobs.jpg",
    "bloodline": ASSET_DIR/"bloodline.jpg", "settings": ASSET_DIR/"settings.jpg",
    "commands": ASSET_DIR/"commands.jpg",
    "profile": {"male": ASSET_DIR/"profile_male.jpg", "female": ASSET_DIR/"profile_female.jpg", "default": ASSET_DIR/"profile_male.jpg"},
}
def get_panel_image(panel, gender=None):
    v = PANEL_IMAGES.get(panel)
    if not isinstance(v, dict):
        return v
    g = (gender or "").strip().lower()
    if g in ("female", "زن", "woman", "f"):
        key = "female"
    elif g in ("male", "مرد", "man", "m"):
        key = "male"
    else:
        key = "default"
    return v.get(key, v.get("default"))
