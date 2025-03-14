from attr import define

from grafanalib.core import TimeSeries, TimeRange, GreaterThan

from grit import CloudwatchAlertRuleBuilder, PrometheusAlertRuleBuilder, ElasticSearchAlertRuleBuilder

@define
class TimeSeriesWrapper(TimeSeries):
    """
    Wrapper for grafanalib.TimeSeries

    """

    def add_alert(self, *args, **kwargs):
        title = kwargs.get("title", "")
        builder = kwargs.get("builder", None)
        threshold = kwargs.get("threshold", GreaterThan(0))
        labels = kwargs.get("labels", {})
        alert_msg = kwargs.get("alert_msg", "NOT_IMPLEMENTED")
        env = kwargs.get("env", None)
        team = kwargs.get("team", "")
        reduce_function = kwargs.get("reduce_function", "last")
        bucket_aggs = kwargs.get("bucket_aggs", [])

        if not bucket_aggs and hasattr(self.targets[0], 'bucketAggs'):
            bucket_aggs = self.targets[0].bucketAggs

        if not title:
            title = self.title

        time_from = kwargs.get("timeFrom", "1h")
        time_shift = kwargs.get("timeShift", "now")
        if self.timeFrom:
            time_from = self.timeFrom

        if self.timeShift:
            time_shift = self.timeShift

        _title=f"[{env}]".upper() + " " + title
        if team:
            _title += " | " + team

        if isinstance(builder, ElasticSearchAlertRuleBuilder):
            builder.register(
                panel=self,
                title=_title,
                bucket_aggs=bucket_aggs,
                reduce_function=reduce_function,
                alert_expression="$REDUCE_EXPRESSION " + str(threshold),
                alert_msg=alert_msg,
                labels=labels,
                time_range=TimeRange(time_from, time_shift)
            )
        elif isinstance(builder, PrometheusAlertRuleBuilder):
            builder.register(
                panel=self,
                title=_title,
                metric={
                    "expr": self.targets[0].expr,
                    "legendFormat": self.targets[0].legendFormat,
                },
                reduce_function=reduce_function,
                alert_expression="$REDUCE_EXPRESSION " + str(threshold),
                alert_msg=alert_msg,
                labels=labels,
                time_range=TimeRange(time_from, time_shift)
            )
        elif isinstance(builder, CloudwatchAlertRuleBuilder):
            raise NotImplementedError("This method should not be used yet.")

        return self
