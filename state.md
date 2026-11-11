# git-guard — state

## DoD
- [x] 0. Аудит: репо в ~/apps, gitleaks по истории, термины по истории; отчёт без значений; ничего не исправлено
- [x] 1. ~/.config/git/ignore: .env*, *.local.*, профили Chrome/Lighthouse, AppData/, *.pem, *.key (diff показан)
- [ ] 2. Python git_guard/ + bash-хуки ≤5 строк (pre-commit, pre-push), лимиты, пути, denylist, gitleaks, термины, хук репо; core.hooksPath
- [ ] 3. pytest во временных репо: каждый блок ✗ + чистый коммит ✓
- [ ] 4. ~/.claude/CLAUDE.md, раздел «Git»
- [ ] 5. Шаблон GitHub Action (gitleaks) — файл, без установки

Правило: стоп после каждого шага.

## Решения
- Термины: ~/.config/git-guard/terms.txt (приватный, не в git). Источники: ключи верхнего уровня pipeline.yaml + колонка company из job-radar/index.csv. Значения полей не берутся.
- Поиск терминов: граница слова, без регистра; термины <3 символов пропускаются (считаются).
- Логика — Python 3 stdlib, хуки — тонкие bash-обёртки.
- Аудит обходит только ~/apps/*/ с каталогом .git; worktree (.git-файл) пропущены — история общая.
- AgentDeck — чужой форк, вне контура: ~/.config/git-guard/exclude-repos.txt (пути репо; аудит и хуки пропускают с пометкой excluded). Находки не рассматриваются, .gitleaksignore там не создаётся.
- Подтверждено владельцем: jev PAT недействителен (401); job-radar tests/fixtures/{profile,facts}.yaml — синтетика (term-находки в tests/fixtures ложные).
- Denylist: общий минимум в config/default.yaml (pipeline.yaml, log.jsonl, .env* кроме example/sample/template); profile.yaml, facts.yaml, reports/ — только через .git-guard.yaml репо.
- .gitleaksignore по fingerprint — в jev (PAT); правки в чужих репо — отдельные ветки, без push, diff показать.
