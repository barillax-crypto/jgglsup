from datetime import datetime
from pydantic import BaseModel, Field


class SourceRow(BaseModel):
    source: str
    leads: int
    conversion_to_deals_pct: float
    cac: float


class TrendPoint(BaseModel):
    date: str
    leads: int
    deals: int
    revenue: float


class RiskOpportunity(BaseModel):
    title: str
    impact: str
    recommendation: str


class TargetComparison(BaseModel):
    metric: str
    actual: float
    target: float
    gap_pct: float


class DashboardOverview(BaseModel):
    rows: list[SourceRow]
    trends: list[TrendPoint]
    top_risks_opportunities: list[RiskOpportunity]
    targets: list[TargetComparison]
    alerts: list[str]


class SyncRequest(BaseModel):
    source: str = Field(pattern="^(bitrix24|amocrm|ga4|yandex_metrica|billing|csv)$")


class SyncStatus(BaseModel):
    source: str
    status: str
    retries: int
    synced_at: datetime


class CsvUploadResponse(BaseModel):
    imported_rows: int
    source: str = "csv"


class FieldMappingInput(BaseModel):
    source: str
    external_field: str
    internal_field: str
