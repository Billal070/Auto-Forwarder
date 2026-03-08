import json
import os

CONFIG_FILE = "data/config.json"

DEFAULT_CONFIG = {
    "sources": [],
    "destination": None,
    "is_forwarding": False
}


def load_config() -> dict:
    os.makedirs("data", exist_ok=True)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    cfg = DEFAULT_CONFIG.copy()
    save_config(cfg)
    return cfg


def save_config(config: dict):
    os.makedirs("data", exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def add_source(link: str) -> bool:
    config = load_config()
    link = link.strip()
    if link not in config["sources"]:
        config["sources"].append(link)
        save_config(config)
        return True
    return False


def remove_source(link: str) -> bool:
    config = load_config()
    link = link.strip()
    if link in config["sources"]:
        config["sources"].remove(link)
        save_config(config)
        return True
    return False


def set_destination(link: str):
    config = load_config()
    config["destination"] = link.strip()
    save_config(config)


def set_forwarding(status: bool):
    config = load_config()
    config["is_forwarding"] = status
    save_config(config)
