from datetime import datetime, timedelta

from pipeline_visibility.backend.services.metrics import (
    calc_arr,
    calc_cac,
    calc_conversion,
    calc_mrr,
    calc_pipeline_value,
    calc_romi,
    calc_sales_velocity,
)


def test_metrics_engine():
    assert calc_arr(100) == 1200
    assert calc_mrr([100, 200]) == 300
    assert calc_cac(1000, 10) == 100
    assert calc_conversion(100, 20) == 20
    assert calc_romi(2000, 1000) == 100
    assert calc_pipeline_value([{"amount": 1000, "probability": 0.5}]) == 500

    now = datetime.utcnow()
    assert calc_sales_velocity([now], [now + timedelta(days=15)]) == 15
