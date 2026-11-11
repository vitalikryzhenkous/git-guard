# git-guard
Общая защита от утечек приватных данных для всех репо на машине.

## Что блокирует (pre-commit и pre-push)
- секреты (gitleaks)
- приватные термины из ~/.config/git-guard/terms.txt (компании, имена, пути)
- файлы из denylist: pipeline.yaml, profile.yaml, facts.yaml, log.jsonl, reports/, .env*
- подозрительные пути: Users/, AppData, Chrome/Lighthouse-профили
- >30 файлов или файл >1 МБ в коммите (override: GUARD_ALLOW_BIG=1)
pre-push проверяет все отправляемые коммиты, а не только рабочее дерево.

## Установка
./install.sh   # gitleaks, core.hooksPath, ~/.config/git/ignore, пустой terms.txt

## Конфиг
- config/default.yaml — общие правила (в git)
- ~/.config/git-guard/terms.txt — приватный словарь, НЕ в git
- .git-guard.yaml в репо — локальные правила (deny_names, deny_dirs, …; списки добавляются к общим)
- ~/.config/git-guard/exclude-repos.txt — репо вне контура (аудит и хуки: «excluded»; хук репо всё равно вызывается)

## Команды
python3 -m git_guard.audit            # скан всей истории всех репо в ~/apps, без вывода значений
python3 -m git_guard.check [repo...]  # staged, а если пусто — дерево HEAD; только счётчики
python3 -m git_guard.doctor           # отчёт: локальные core.hooksPath, excluded, gitleaks, terms.txt
python3 -m git_guard.terms            # подтянуть термины (slug из pipeline.yaml + company из index.csv)

## Хуки репо
Глобальные обёртки (pre-commit, pre-push + commit-msg, prepare-commit-msg, post-commit, post-merge, post-checkout, pre-rebase) вызывают хук репо: .githooks/, scripts/hooks/ или .git/hooks/ (первый найденный). Локальный core.hooksPath в репо перекрывает глобальный — смотри doctor.
Термины блокируют везде; исключение — `allow_terms` в .git-guard.yaml: `- путь-или-glob | причина`. Неподдерживаемый синтаксис конфига = ошибка и блок.

## Ограничения
Не переписывает историю. Не защищает от `--no-verify` — это запрещено правилами агентов.