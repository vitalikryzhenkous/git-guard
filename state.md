# git-guard — state

## DoD
- [x] 0. Аудит: репо в ~/apps, gitleaks по истории, термины по истории; отчёт без значений; ничего не исправлено
- [ ] 1. ~/.config/git/ignore: .env*, *.local.*, профили Chrome/Lighthouse, AppData/, *.pem, *.key (diff показан)
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
