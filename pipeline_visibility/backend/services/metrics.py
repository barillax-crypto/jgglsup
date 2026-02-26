from datetime import datetime
from statistics import mean


def calc_arr(monthly_revenue: float) -> float:
    return monthly_revenue * 12


def calc_mrr(monthly_payments: list[float]) -> float:
    return sum(monthly_payments)


def calc_cac(marketing_cost: float, new_customers: int) -> float:
    return marketing_cost / new_customers if new_customers else 0.0


def calc_conversion(leads: int, deals: int) -> float:
    return (deals / leads * 100) if leads else 0.0


def calc_sales_velocity(open_dates: list[datetime], close_dates: list[datetime]) -> float:
    if not open_dates or not close_dates or len(open_dates) != len(close_dates):
        return 0.0
    durations = [(c - o).days for o, c in zip(open_dates, close_dates)]
    return float(mean(durations))


def calc_romi(revenue: float, marketing_cost: float) -> float:
    return ((revenue - marketing_cost) / marketing_cost * 100) if marketing_cost else 0.0


def calc_pipeline_value(open_deals: list[dict]) -> float:
    return sum(float(deal.get("amount", 0)) * float(deal.get("probability", 0)) for deal in open_deals)
