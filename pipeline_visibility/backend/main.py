from datetime import datetime, timedelta
import csv
import io
from fastapi import Depends, FastAPI, File, UploadFile
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, engine, get_db
from .models import FieldMapping
from .schemas import (
    CsvUploadResponse,
    DashboardOverview,
    FieldMappingInput,
    RiskOpportunity,
    SourceRow,
    SyncStatus,
    TargetComparison,
    TrendPoint,
)
from .security import get_tenant_context, require_role
from .services.metrics import calc_cac, calc_conversion
from .services.sync import SyncService

app = FastAPI(title=settings.app_name)
Base.metadata.create_all(bind=engine)
sync_service = SyncService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/dashboard/overview", response_model=DashboardOverview)
def get_dashboard_overview(
    days: int = 30,
    tenant_ctx: tuple[str, str] = Depends(get_tenant_context),
) -> DashboardOverview:
    org_id, _ = tenant_ctx
    channels = [
        {"source": "paid_search", "leads": 120, "deals": 24, "marketing_cost": 1_800_000},
        {"source": "organic", "leads": 90, "deals": 18, "marketing_cost": 450_000},
        {"source": "referral", "leads": 60, "deals": 20, "marketing_cost": 120_000},
    ]

    rows = [
        SourceRow(
            source=ch["source"],
            leads=ch["leads"],
            conversion_to_deals_pct=round(calc_conversion(ch["leads"], ch["deals"]), 2),
            cac=round(calc_cac(ch["marketing_cost"], ch["deals"]), 2),
        )
        for ch in channels
    ]

    today = datetime.utcnow().date()
    trend_points = [
        TrendPoint(
            date=(today - timedelta(days=i)).isoformat(),
            leads=max(20, 80 - i),
            deals=max(5, 20 - i // 3),
            revenue=float(max(350_000, 1_500_000 - i * 17_000)),
        )
        for i in reversed(range(min(days, 90)))
    ]

    risks = [
        RiskOpportunity(
            title="CAC paid_search выше целевого на 11%",
            impact="Снижение ROMI по платному трафику",
            recommendation="Перераспределить 15% бюджета в referral и запустить A/B по креативам",
        ),
        RiskOpportunity(
            title="Ускорение pipeline в referral",
            impact="Рост выручки в горизонте квартала",
            recommendation="Увеличить партнерские активности и внедрить SLA на обработку лидов",
        ),
        RiskOpportunity(
            title="Просадка middle-funnel по organic",
            impact="Риск невыполнения квартального плана",
            recommendation="Добавить nurture-цепочки и пересмотреть lead scoring",
        ),
    ]

    targets = [
        TargetComparison(metric="MRR", actual=12_600_000, target=14_000_000, gap_pct=-10.0),
        TargetComparison(metric="Deals conversion", actual=20.8, target=22.0, gap_pct=-5.45),
        TargetComparison(metric="CAC", actual=59_000, target=55_000, gap_pct=7.27),
    ]

    alerts = sync_service.get_sync_alerts(
        org_id=org_id,
        sources=["bitrix24", "amocrm", "ga4", "yandex_metrica", "billing"],
        alert_hours=settings.sync_alert_hours,
    )
    return DashboardOverview(
        rows=rows,
        trends=trend_points,
        top_risks_opportunities=risks,
        targets=targets,
        alerts=alerts,
    )


@app.post("/api/v1/integrations/{source}/sync", response_model=SyncStatus)
def trigger_sync(source: str, tenant_ctx: tuple[str, str] = Depends(get_tenant_context)) -> SyncStatus:
    org_id, role = tenant_ctx
    require_role(role, {"admin", "manager"})
    result = sync_service.sync(org_id=org_id, source=source)
    return SyncStatus(**result.__dict__)


@app.post("/api/v1/data/upload-csv", response_model=CsvUploadResponse)
def upload_csv(
    file: UploadFile = File(...),
    tenant_ctx: tuple[str, str] = Depends(get_tenant_context),
) -> CsvUploadResponse:
    _, role = tenant_ctx
    require_role(role, {"admin", "manager"})

    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    imported_rows = sum(1 for _ in reader)
    return CsvUploadResponse(imported_rows=imported_rows)


@app.post("/api/v1/field-mappings")
def save_field_mapping(
    payload: FieldMappingInput,
    tenant_ctx: tuple[str, str] = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    org_id, role = tenant_ctx
    require_role(role, {"admin"})

    mapping = FieldMapping(
        org_id=org_id,
        source=payload.source,
        external_field=payload.external_field,
        internal_field=payload.internal_field,
    )
    db.add(mapping)
    db.commit()
    return {"status": "saved"}
