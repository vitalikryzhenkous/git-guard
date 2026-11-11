"""Конфиг: простое подмножество YAML (скаляры и списки '- x'), stdlib."""
import os

DEFAULT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "default.yaml")


def _parse(path):
    out, key = {}, None
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.split(" #")[0].rstrip() if not raw.lstrip().startswith("#") else ""
            if not line.strip():
                continue
            s = line.strip()
            if s.startswith("- ") and key:
                out[key].append(s[2:].strip().strip("'\""))
            elif ":" in s and not line.startswith(" "):
                k, v = s.split(":", 1)
                key, v = k.strip(), v.strip().strip("'\"")
                if v == "":
                    out[key] = []
                else:
                    out[key] = int(v) if v.isdigit() else v
    return out


def load(repo):
    cfg = _parse(DEFAULT)
    local = os.path.join(repo, ".git-guard.yaml")
    if os.path.exists(local):
        for k, v in _parse(local).items():
            if isinstance(v, list):
                cfg[k] = list(cfg.get(k, [])) + v
            else:
                cfg[k] = v
    return cfg
