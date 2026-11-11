"""Сбор приватных терминов. Значения не печатаются, только счётчики."""
import csv, os, re, sys

TERMS = os.path.expanduser("~/.config/git-guard/terms.txt")
PIPELINE = os.path.expanduser("~/apps/job-radar/pipeline.yaml")
INDEX = os.path.expanduser("~/apps/job-radar/index.csv")
MIN_LEN = 3
TOP_KEY = re.compile(r"""^(?!\s|#|-)(?:"([^"]+)"|'([^']+)'|([^:#]+?))\s*:(?:\s|$)""")


def yaml_top_keys(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = TOP_KEY.match(line)
            if m:
                yield next(g for g in m.groups() if g).strip()


def csv_company(path):
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            v = (row.get("company") or "").strip()
            if v:
                yield v


def load(path=None):
    path = path or os.environ.get("GUARD_TERMS_FILE") or TERMS
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]


def sync(path=TERMS, pipeline=PIPELINE, index=INDEX):
    existing = load(path)
    seen = {t.lower() for t in existing}
    added = short = 0
    new = []
    for t in [*yaml_top_keys(pipeline), *csv_company(index)]:
        if len(t) < MIN_LEN:
            short += 1
            continue
        if t.lower() not in seen:
            seen.add(t.lower())
            new.append(t)
            added += 1
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as f:
        f.writelines(t + "\n" for t in new)
    return added, short


def pattern(terms):
    ts = [t for t in terms if len(t) >= MIN_LEN]
    if not ts:
        return None
    alt = "|".join(re.escape(t) for t in sorted(ts, key=len, reverse=True))
    return re.compile(rf"(?<!\w)(?:{alt})(?!\w)", re.IGNORECASE)


if __name__ == "__main__":
    a, s = sync()
    print(f"добавлено {a}, пропущено коротких {s}")
