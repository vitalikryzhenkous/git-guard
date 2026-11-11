"""Конфиг: строгое подмножество YAML (скаляры и списки '- x'), stdlib.
Всё остальное — ConfigError (и блок коммита), а не молчаливый пропуск."""
import os, re

DEFAULT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "default.yaml")
KEY = re.compile(r"([A-Za-z_][A-Za-z0-9_-]*):(?:\s+(\S.*))?")


class ConfigError(Exception):
    pass


def _parse(path, known=None):
    out, key = {}, None
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    for n, raw in enumerate(lines, 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        def err(why):
            raise ConfigError(f"{os.path.basename(path)}: строка {n}: {why}")
        if "\t" in raw:
            err("табуляция")
        body = raw.split(" #")[0].rstrip()
        s = body.strip()
        if s.startswith("- "):
            if key is None or not isinstance(out[key], list):
                err("элемент списка вне списка")
            item = s[2:].strip().strip("'\"")
            if not item:
                err("пустой элемент списка")
            out[key].append(item)
            continue
        m = KEY.fullmatch(body)
        if not m or raw[0].isspace():
            err("неподдерживаемый синтаксис (вложенность, flow-списки, якоря)")
        k, v = m.group(1), m.group(2)
        if known is not None and k not in known:
            err("неизвестный ключ")
        if k in out:
            err("повтор ключа")
        key = k
        if v is None:
            out[k] = []
        elif v[0] in "[{&*|>!%@`":
            err("неподдерживаемый синтаксис (flow-списки, якоря, блоки)")
        else:
            v = v.strip("'\"")
            out[k] = int(v) if v.isdigit() else v
    return out


def _typecheck(cfg, default, name):
    for k, v in cfg.items():
        if type(v) is not type(default[k]):
            raise ConfigError(f"{name}: ключ {k}: ожидался {type(default[k]).__name__}")


def allow_terms(cfg):
    res = []
    for e in cfg.get("allow_terms", []):
        glob, sep, reason = e.partition(" | ")
        if not sep or not glob.strip() or not reason.strip():
            raise ConfigError("allow_terms: нужен формат '- путь | причина'")
        res.append((glob.strip(), reason.strip()))
    return res


def load(repo):
    cfg = _parse(DEFAULT)
    local = os.path.join(repo, ".git-guard.yaml")
    if os.path.exists(local):
        loc = _parse(local, known=set(cfg))
        _typecheck(loc, cfg, ".git-guard.yaml")
        for k, v in loc.items():
            cfg[k] = list(cfg[k]) + v if isinstance(v, list) else v
    allow_terms(cfg)
    return cfg
