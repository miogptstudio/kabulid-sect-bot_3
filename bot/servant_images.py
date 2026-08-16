from pathlib import Path

SERVANT_IMAGE_DIR = Path(__file__).resolve().parent.parent / "assets" / "servants"

# نگاشت یک‌به‌یک: خدمتکار شماره N همیشه فایل N.jpg را می‌گیرد.
# نگاشت قبلی درهم بود و باعث می‌شد عکس بعضی خدمتکارها اشتباه نشان داده شود.
SERVANT_IMAGE_BY_ID = {i: i for i in range(1, 37)}

SERVANT_IMAGES = {
    i: SERVANT_IMAGE_DIR / f"{i:02d}.jpg" for i in range(1, 37)
}


def get_servant_image_by_id(base_id: int):
    try:
        return SERVANT_IMAGES.get(int(base_id))
    except (TypeError, ValueError):
        return None


def get_servant_image(servant_key):
    try:
        return get_servant_image_by_id(int(servant_key))
    except (TypeError, ValueError):
        return None
