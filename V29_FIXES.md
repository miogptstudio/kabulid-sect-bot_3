# V29 — Hunt & Stability Fixes

- Fixed missing `tr` import in `bot/handlers/pets.py`.
- Added text navigation for `شکار`, `🐾 شکار`, and `حیوانات و شکار` so users can enter the hunt section without `/hunt`.
- Fixed missing `tr` imports in `games.py` and `society_extra.py`, which could cause runtime NameError when those paths were used.
- Improved hunt spawn error message to include a short useful exception detail.
- Verified all Python files compile successfully with `python -m compileall`.
- No database reset or destructive migration was added.
