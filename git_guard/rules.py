"""Правила путей. Конфиг — config.load(repo)."""
import re


def denied_path(path, cfg):
    parts = path.split("/")
    base = parts[-1]
    if base in cfg.get("env_allow", []):
        return None
    if base in cfg.get("deny_names", []) or base.startswith(cfg.get("env_prefix", ".env")):
        return "denylist"
    if any(p in cfg.get("deny_dirs", []) for p in parts[:-1]):
        return "denylist"
    if any(re.search(rx, path) for rx in cfg.get("path_patterns", [])):
        return "path"
    return None

