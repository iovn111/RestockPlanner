# Restock Planner

Десктопное приложение для Windows, которое помогает небольшим продавцам Wildberries решить, когда и сколько товара заказать у поставщика, с учётом прошлых дефицитов и новинок без истории продаж. Работает офлайн; интернет нужен только для загрузки данных.

Курсовой проект (Бизнес-информатика, 3 курс).

## Документация

- `docs/PROJECT_SPEC.md` — спецификация: проблема, методы, эксперимент, продукт
- `docs/DECISIONS.md` — журнал решений

## Разработка

Нужны Windows 10/11 и [uv](https://docs.astral.sh/uv/). Python 3.12 uv установит сам.

```
uv sync                         # установить зависимости
uv run pytest                   # тесты
uv run ruff check .             # проверка стиля
uv run restock-planner          # запустить приложение
uv run restock-sync             # ручной запуск синхронизации данных
```

Пробная сборка `.exe` (проверка упаковки PySide6 + statsforecast):

```
uv run pyinstaller packaging/smoke/smoke_app.py --name smoke_app --onedir --noconfirm --distpath packaging/output/dist --workpath packaging/output/build --specpath packaging/output
```

Результат: `packaging/output/dist/smoke_app/smoke_app.exe`.

## Структура

```
src/restock/
  data/         источники данных (DataSource) и единая модель данных
  core/         методы: восстановление спроса, новинки, прогноз, расчёт заказа
  experiments/  бэктест, метрики, искусственное цензурирование, симуляция
  db/           модели SQLite, миграции
  services/     сценарии: синхронизация, пересчёт рекомендаций, экспорт в Excel
  sync/         restock-sync и задача в Планировщике заданий Windows
  gui/          окна PySide6
  notify/       уведомления Windows
packaging/      сборка .exe и установщика
notebooks/      исследование данных
tests/
data/           датасеты (не хранятся в git)
```
