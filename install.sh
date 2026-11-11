#!/usr/bin/env bash
# Установка git-guard. Откат: git config --global --unset core.hooksPath
set -eu
d="$(cd "$(dirname "$0")" && pwd)"
command -v gitleaks >/dev/null || { echo "нет gitleaks"; exit 1; }
install -d -m 700 ~/.config/git-guard; touch ~/.config/git-guard/terms.txt ~/.config/git-guard/exclude-repos.txt
git config --global core.hooksPath "$d/hooks"
echo "core.hooksPath=$d/hooks"
