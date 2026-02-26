export type SourceRow = {
  source: string;
  leads: number;
  conversion_to_deals_pct: number;
  cac: number;
};

export type TrendPoint = {
  date: string;
  leads: number;
  deals: number;
  revenue: number;
};

export type RiskOpportunity = {
  title: string;
  impact: string;
  recommendation: string;
};

export type TargetComparison = {
  metric: string;
  actual: number;
  target: number;
  gap_pct: number;
};

export type DashboardOverview = {
  rows: SourceRow[];
  trends: TrendPoint[];
  top_risks_opportunities: RiskOpportunity[];
  targets: TargetComparison[];
  alerts: string[];
};
