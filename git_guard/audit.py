"""Аудит истории: gitleaks + термины. Печатает repo, commit, file, type — без значений."""
import json, os, subprocess, sys, tempfile
from git_guard import terms


def repos(root=os.path.expanduser("~/apps")):
    return sorted(d.path for d in os.scandir(root) if os.path.isdir(os.path.join(d.path, ".git")))


def has_commits(repo):
    return subprocess.run(["git", "-C", repo, "rev-parse", "-q", "--verify", "HEAD"],
                          capture_output=True).returncode == 0


def leaks(repo):
    with tempfile.TemporaryDirectory() as td:
        rep = os.path.join(td, "r.json")
        subprocess.run(["gitleaks", "git", repo, "--redact", "--no-banner", "--exit-code", "0",
                        "-r", rep, "-f", "json"], capture_output=True)
        try:
            data = json.load(open(rep))
        except (OSError, ValueError):
            return None
    return [(r.get("Commit", "")[:10], r.get("File", ""), "secret:" + r.get("RuleID", "?")) for r in data or []]


def term_hits(repo, pat):
    p = subprocess.Popen(["git", "-C", repo, "log", "--all", "-p", "--no-color", "-U0",
                          "--format=@@C %H"], stdout=subprocess.PIPE, text=True,
                         encoding="utf-8", errors="replace")
    commit = fname = None
    hits = set()
    for line in p.stdout:
        if line.startswith("@@C "):
            commit = line[4:14]
        elif line.startswith("+++ "):
            fname = line[6:].strip() if line[4:6] == "b/" else None
        elif line.startswith("+") and fname and pat.search(line):
            hits.add((commit, fname, "term"))
    p.wait()
    return sorted(hits)


def main():
    pat = terms.pattern(terms.load())
    print(f"terms: {'on' if pat else 'EMPTY'}")
    for repo in repos():
        name = os.path.basename(repo)
        if not has_commits(repo):
            print(f"{name}\t-\t-\tno-commits")
            continue
        found = leaks(repo)
        if found is None:
            print(f"{name}\t-\t-\tgitleaks-error")
            found = []
        if pat:
            found += term_hits(repo, pat)
        for c, f, t in sorted(set(found)):
            print(f"{name}\t{c}\t{f}\t{t}")
        print(f"{name}\t# total {len(found)}")


if __name__ == "__main__":
    main()
