import inspect
import sys

from attr import define, field, ib

from grafanalib.elasticsearch import (
    ElasticsearchTarget, DateHistogramGroupBy, TermsGroupBy, CountMetricAgg, CardinalityMetricAgg
)
from grafanalib.core import TimeSeries, GreaterThan, Target, TimeRange

from .helpers import gen_random_str

ALERT_RULES_MAGIC_STR = '__alert_rules__'

@define
class TimeSeriesWrapper(TimeSeries):
    """
    Wrapper for grafanalib.TimeSeries

    """

    def add_alert(self, *args, **kwargs):
        title = kwargs.get("title", "")
        builder = kwargs.get("builder", None)
        threshold = kwargs.get("threshold", 0)
        labels = kwargs.get("labels", {})
        alert_msg = kwargs.get("alert_msg", "NOT_IMPLEMENTED")
        env = kwargs.get("env", None)

        if not title:
            title = self.title

        builder.register(
            panel=self,
            title=f"[{env}]".upper() + " " + title + " | Pagerduty",
            bucket_aggs=[
                DateHistogramGroupBy(
                    field='updatedAt',
                    interval='1m'
                )
            ],
            reduce_function="sum",
            alert_expression="$REDUCE_EXPRESSION > " + threshold,
            alert_msg=alert_msg,
            labels=labels,
            time_range=TimeRange("24h", "now-15m")
        )

        return self
