import importlib

MODULES = [
    "services.open_world",
    "bot.handlers.open_world",
    "bot.main",
]

for name in MODULES:
    importlib.import_module(name)
    print(f"IMPORT OK: {name}")
print("PREDEPLOY CHECK OK")
