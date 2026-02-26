# Pipeline Visibility Dashboard Frontend

Next.js frontend для MVP дашборда.

## Run
```bash
cd pipeline_visibility/frontend
npm install
npm run dev
```

Открой: `http://localhost:3000`.

По умолчанию frontend ходит в backend по `http://localhost:8010`.
Переопределение: `NEXT_PUBLIC_API_BASE_URL`.

## Что есть в UI
- Таблица источников маркетинга: лиды, конверсия в deals, CAC.
- Тренды по Leads/Deals/Revenue (30/60/90 дней).
- Top 3 risks/opportunities.
- Сравнение с целевыми метриками.
- KPI карточки (всего лидов, взвешенная конверсия, средний CAC).
- Режим fallback (демо-данные), если backend временно недоступен.
