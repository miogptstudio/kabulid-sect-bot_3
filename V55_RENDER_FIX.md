# v55 Render startup fix

The Render traceback came from an older GitHub commit that still contained:
`@router.message(Command("weeklystory", ...))` inside `services/open_world.py`.

In v55, `services/open_world.py` contains only service functions; Telegram routers live in `bot/handlers/open_world.py`.

Also fixed an orphan text-movement decorator that was attached to `cmd_world_panel` instead of `text_move`.

Before deploying, run:
`python -m compileall -q .`
`python predeploy_check.py`

Important: Render deploys from GitHub. Upload/push this v55 source to the repository/branch used by Render; uploading the ZIP somewhere else does not change the GitHub commit Render checks out.
