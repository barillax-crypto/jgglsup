# Pipeline Visibility Dashboard (MVP)

MVP SaaS-платформа для RANICA: связывает маркетинговые лиды с фактической выручкой для B2B компаний СНГ.

## Что реализовано
- **Dashboard Overview API**: таблица источников, тренды 30/60/90 дней, top risks/opportunities, сравнение с target metrics.
- **Data Integration API**: ручной триггер синка для `bitrix24`, `amocrm`, `ga4`, `yandex_metrica`, `billing`; импорт CSV.
- **Metrics Engine**: ARR/MRR/CAC/Conversion/Sales Velocity/ROMI/Pipeline Value.
- **Multi-tenant + RBAC**: изоляция через `X-Org-Id`, роли `admin|manager|viewer`.
- **Field Mapping API**: маппинг кастомных полей CRM в стандартные поля платформы.
- **Real-time sync control**: retry логика и alert, если источник не синкался >24 часов.

## Быстрый старт
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn pipeline_visibility.backend.main:app --reload --port 8010
```

## Примеры API
```bash
curl -H "X-Org-Id: org-1" "http://localhost:8010/api/v1/dashboard/overview?days=30"

curl -X POST -H "X-Org-Id: org-1" -H "X-User-Role: manager" \
  "http://localhost:8010/api/v1/integrations/ga4/sync"
```

## Архитектурные блоки
- `main.py` — FastAPI endpoints.
- `models.py` — SQLAlchemy multi-tenant schema.
- `services/metrics.py` — расчетная логика метрик.
- `services/sync.py` — retry + freshness alerts для sync.
- `celery_app.py` — async jobs (Celery + Redis).

## Frontend (Next.js)
Frontend находится в `pipeline_visibility/frontend`.

```bash
cd pipeline_visibility/frontend
npm install
npm run dev
```

UI доступен по `http://localhost:3000` и использует API `http://localhost:8010` (или `NEXT_PUBLIC_API_BASE_URL`).
