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
- .git-guard.yaml в репо — локальные исключения

## Команды
git-guard audit [repo]   # скан всей истории, без вывода значений
git-guard check          # ручной прогон по staged
git-guard terms sync     # подтянуть термины из job-radar/pipeline.yaml

## Хуки репо
Глобальный хук вызывает .githooks/ или scripts/hooks/ репо после своих проверок.

## Ограничения
Не переписывает историю. Не защищает от `--no-verify` — это запрещено правилами агентов.