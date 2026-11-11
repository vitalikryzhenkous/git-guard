"""Исключённые репо: ~/.config/git-guard/exclude-repos.txt (по пути на строку, # — комментарий)."""
import os

FILE = os.path.expanduser("~/.config/git-guard/exclude-repos.txt")


def _norm(p):
    return os.path.realpath(os.path.expanduser(p.strip()))


def load(path=None):
    path = path or os.environ.get("GUARD_EXCLUDE_FILE") or FILE
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        return {_norm(l) for l in f if l.strip() and not l.lstrip().startswith("#")}


def is_excluded(repo, excluded=None):
    return _norm(repo) in (load() if excluded is None else excluded)
