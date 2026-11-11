"""git-guard doctor: только отчёт, ничего не меняет."""
import os, shutil, subprocess
from git_guard import audit, exclude, terms

HOOKS = ["pre-commit", "pre-push", "commit-msg", "prepare-commit-msg", "post-commit",
         "post-merge", "post-checkout", "pre-rebase"]


def _git_cfg(*a, repo=None):
    cmd = ["git"] + (["-C", repo] if repo else []) + ["config", *a]
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()


def report(root=None):
    root = root or os.path.expanduser("~/apps")
    out = []
    g = _git_cfg("--global", "core.hooksPath")
    here = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks")
    out.append(f"global core.hooksPath: {g or '(не задан)'}" + (" [наш]" if g and os.path.realpath(os.path.expanduser(g)) == os.path.realpath(here) else ""))
    out.append("обёртки в hooks/: " + (", ".join(h for h in HOOKS if not os.access(os.path.join(here, h), os.X_OK)) or "все 8 на месте") + (" (нет перечисленных)" if any(not os.access(os.path.join(here, h), os.X_OK) for h in HOOKS) else ""))
    gl = shutil.which("gitleaks")
    ver = subprocess.run([gl, "version"], capture_output=True, text=True).stdout.strip() if gl else ""
    out.append(f"gitleaks: {ver or 'НЕТ'}")
    tf = os.environ.get("GUARD_TERMS_FILE") or terms.TERMS
    if os.path.exists(tf):
        mode = oct(os.stat(tf).st_mode & 0o777)
        out.append(f"terms.txt: есть, терминов {len(terms.load(tf))}, права {mode}" + ("" if mode == "0o600" else " (ожидалось 0o600)"))
    else:
        out.append("terms.txt: НЕТ")
    ex = exclude.load()
    out.append(f"exclude-repos.txt: путей {len(ex)}")
    out.append("репо:")
    repos = sorted(d.path for d in os.scandir(root) if os.path.isdir(os.path.join(d.path, ".git")))
    for r in repos:
        loc = _git_cfg("--local", "core.hooksPath", repo=r)
        flags = []
        if loc:
            flags.append(f"ЛОКАЛЬНЫЙ core.hooksPath перекрывает глобальный: {loc}")
        if exclude.is_excluded(r, ex):
            flags.append("excluded")
        if flags:
            out.append(f"  {os.path.basename(r)}\t" + "; ".join(flags))
    out.append(f"  (проверено репо: {len(repos)}; без флагов не показаны)")
    return out


if __name__ == "__main__":
    print("\n".join(report()))
