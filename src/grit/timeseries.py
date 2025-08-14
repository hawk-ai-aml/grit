from attr import define

from grafanalib.core import TimeSeries, TimeRange, GreaterThan, ALERTRULE_STATE_DATA_OK

from grafanalib.elasticsearch import CountMetricAgg

from grit import CloudwatchAlertRuleBuilder, PrometheusAlertRuleBuilder, ElasticSearchAlertRuleBuilder

@define
class TimeSeriesWrapper(TimeSeries):
    """
    Wrapper for grafanalib.TimeSeries

    """

    def build_alert_annotations(self, msg, impact, runbook, call_to_action):
        """
        Build alert annotations for the time series.

        :param msg: Alert message
        :param impact: Impact of the alert
        :param runbook: Runbook URL
        :param call_to_action: Call to action text
        :return: Dictionary of annotations
        """
        return {
            "summary": msg,
            "impact": impact,
            "runbook": runbook,
            "call_to_action": call_to_action,
        }

    def add_alert(self, *args, **kwargs):
        title = kwargs.get("title", "")
        builder = kwargs.get("builder", None)
        threshold = kwargs.get("threshold", GreaterThan(0))
        labels = kwargs.get("labels", {})
        grouping = kwargs.get("grouping", "")
        env = kwargs.get("env", None)
        team = kwargs.get("team", "")
        reduce_function = kwargs.get("reduce_function", "last")
        no_data_alert_state = kwargs.get("no_data_alert_state", ALERTRULE_STATE_DATA_OK)


        alert_annotation = self.build_alert_annotations(
            msg=kwargs.get("alert_msg", "Please provide an alert message"),
            impact=kwargs.get("impact", ""),
            runbook=kwargs.get("runbook", ""),
            call_to_action=kwargs.get("call_to_action", "")
        )

        if grouping:
            labels["grouping"] = grouping

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

            bucket_aggs = kwargs.get("bucket_aggs", [])
            metricAggs = kwargs.get("metricAggs", [])
            apply_auto_bucket_agg_ids_function = kwargs.get("apply_auto_bucket_agg_ids_function", False)
            query = kwargs.get("query", "")

            if not bucket_aggs and hasattr(self.targets[0], 'bucketAggs'):
                bucket_aggs = self.targets[0].bucketAggs

            time_field = self.targets[0].bucketAggs[0].field if hasattr(self.targets[0].bucketAggs[0], 'field') else None

            if not metricAggs:
                if hasattr(self.targets[0], 'metricAggs'):
                    metricAggs = self.targets[0].metricAggs
                else:
                    metricAggs = [CountMetricAgg()]

            builder.register(
                panel=self,
                title=_title,
                query=query,
                bucket_aggs=bucket_aggs,
                metric_aggs=metricAggs,
                apply_auto_bucket_agg_ids_function=apply_auto_bucket_agg_ids_function,
                reduce_function=reduce_function,
                alert_expression="$REDUCE_EXPRESSION " + str(threshold),
                alert_annotation=alert_annotation,
                labels=labels,
                time_range=TimeRange(time_from, time_shift),
                time_field=time_field,
                no_data_alert_state=no_data_alert_state
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
                alert_annotation=alert_annotation,
                labels=labels,
                time_range=TimeRange(time_from, time_shift),
                no_data_alert_state=no_data_alert_state
            )
        elif isinstance(builder, CloudwatchAlertRuleBuilder):
            builder.register(
                panel=self,
                title=_title,
                metric={
                    "name": self.targets[0].metricName,
                    "statistics": self.targets[0].statistics,
                    "dimensions": self.targets[0].dimensions,
                },
                time_range=TimeRange(time_from, time_shift),
                reduce_function=reduce_function,
                alert_expression="$REDUCE_EXPRESSION " + str(threshold),
                alert_annotation=alert_annotation,
                labels=labels,
                no_data_alert_state=no_data_alert_state
            )

        return self
