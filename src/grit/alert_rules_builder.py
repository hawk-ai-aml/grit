from attr import define, field

from .utilities import create_uid_from_string

from grafanalib.core import (
    AlertExpression,
    EXP_TYPE_REDUCE, EXP_TYPE_MATH, EXP_REDUCER_FUNC_DROP_NN, EXP_REDUCER_FUNC_LAST,
    AlertRulev11, TimeRange, ALERTRULE_STATE_DATA_ALERTING, ALERTRULE_STATE_DATA_KEEPLAST_V11
)

from grafanalib.cloudwatch import CloudwatchMetricsTarget
from grafanalib.prometheus_target import PrometheusTarget
from grafanalib.elasticsearch import (ElasticsearchTarget, CountMetricAgg)
from abc import ABC, abstractmethod


class AlertRuleBuilder(ABC):
    """
    An interface class for building alert rules.
    """

    def __init__(self, environment, evaluateFor, dashboard_uid, datasource=None, uid_prefix=""):
        """
        Initialize the AlertRuleBuilder.

        Args:
            evaluateFor (int): The duration in seconds for which the alert condition must be met.
        """
        self.rules = []
        self.environment = environment
        self.evaluateFor = evaluateFor
        self.dashboard_uid = dashboard_uid

        self.datasource = datasource

    def register(self, title, metric, alert_expression, alert_msg, labels, panelId,
                 reduce_function=EXP_REDUCER_FUNC_LAST, time_range=TimeRange('5m', 'now'),
                 no_data_alert_state=ALERTRULE_STATE_DATA_KEEPLAST_V11, execute_error_alert_state=ALERTRULE_STATE_DATA_ALERTING):
        """
        Register a new alert rule.

        Args:
            title (str): The title of the alert rule.
            metric (dict): The metric configuration for the alert rule.
            alert_expression (str): The expression used to define the alert condition.
            alert_msg (str): The summary message for the alert.
            labels (dict): The labels associated with the alert rule.
            panelId (str): The panel ID associated with the alert rule.
        """
        rule = {
            "title": title,
            "metric": metric,
            "reduce_function": reduce_function,
            "alert_expression": alert_expression,
            "time_range": time_range,
            "annotations": {
                "summary": alert_msg
            },
            "labels": labels,
            "panelId": panelId,
            "no_data_alert_state": no_data_alert_state,
            "execute_error_alert_state": execute_error_alert_state
        }
        if self.dashboard_uid != "":
            rule["annotations"]["__panelId__"] = panelId
            rule["annotations"]["__dashboardUid__"] = self.dashboard_uid

        self.rules.append(rule)

    @abstractmethod
    def build(self, uid_prefix):
        """
        Build the alert rules.
        """
        raise NotImplementedError("Method build() must be implemented in a subclass.")

    @staticmethod
    def build_all(*alert_rule_builders):
        """
        Build the alert rules for all instances of AlertRuleBuilder.

        Args:
            uid_prefix (str): The prefix to be added to the UID of each alert rule.
            *alert_rule_builders (AlertRuleBuilder): Variable number of AlertRuleBuilder instances.

        Returns:
            list: A list of AlertRulev11 objects representing the built alert rules from all instances.
        """
        __alert_rules__ = []
        for builder in alert_rule_builders:
            __alert_rules__.extend(builder.build())
        return __alert_rules__

    def _convert_time_range_to_number(self, time_range):
        """
        Convert time range to seconds.

        Args:
            time_range (str): Time range in format '1h', '2d', '3w', 'now', 'now-15m', etc.

        Returns:
            int: Time range in seconds.
        """
        if time_range == 'now':
            return 0
        elif time_range.startswith('now-'):
            if time_range.endswith('m'):
                return int(time_range[4:-1]) * 60
            elif time_range.endswith('h'):
                return int(time_range[4:-1]) * 3600
            elif time_range.endswith('d'):
                return int(time_range[4:-1]) * 86400
            elif time_range.endswith('w'):
                return int(time_range[4:-1]) * 604800
            else:
                return 0
        elif time_range[-1] == 'm':
            return int(time_range[:-1]) * 60
        elif time_range[-1] == 'h':
            return int(time_range[:-1]) * 3600
        elif time_range[-1] == 'd':
            return int(time_range[:-1]) * 86400
        elif time_range[-1] == 'w':
            return int(time_range[:-1]) * 604800
        else:
            return 0


class CloudwatchAlertRuleBuilder(AlertRuleBuilder):
    """
    A class for building CloudWatch alert rules.
    """

    def __init__(self, environment, evaluateFor, metric_namespace, dashboard_uid, uid_prefix=""):
        super().__init__(environment, evaluateFor, dashboard_uid)
        self.metric_namespace = metric_namespace

    def build(self):
        """
        Build the CloudWatch alert rules.

        Args:
            uid_prefix (str): The prefix to be added to the UID of each alert rule.

        Returns:
            list: A list of AlertRulev11 objects representing the built alert rules.
        """
        __alert_rules__ = []

        if "aws" not in self.environment.provider:
            return __alert_rules__

        for _, alert in enumerate(self.rules):
            __alert_rules__.append(
                AlertRulev11(
                    title=alert["title"],
                    triggers=self._generate_triggers(alert),
                    timeRangeFrom=self._convert_time_range_to_number(alert["time_range"].to_json_data()[0]),
                    timeRangeTo=self._convert_time_range_to_number(alert["time_range"].to_json_data()[1]),
                    annotations=alert["annotations"],
                    labels=alert["labels"],
                    condition="ALERT_CONDITION",
                    noDataAlertState=alert["no_data_alert_state"],
                    errorAlertState=alert["execute_error_alert_state"],
                    evaluateFor=self.evaluateFor,
                    uid=create_uid_from_string(alert["title"]),
                    panel_id=alert["panelId"],
                    dashboard_uid=self.dashboard_uid,
                )
            )

        return __alert_rules__

    def _generate_triggers(self, alert):

        if isinstance(alert["metric"], list):
            triggers=[]
            for alert_metric in alert["metric"]:
                triggers.append(
                    CloudwatchMetricsTarget(
                        refId=alert_metric["refId"]+"-QUERY",
                        namespace=alert_metric.get("namespace", self.metric_namespace),
                        metricName=alert_metric["name"],
                        statistics=alert_metric["statistics"],
                        dimensions=alert_metric["dimensions"],
                        datasource=self.datasource if self.datasource else "cloudwatch",
                        matchExact=alert_metric.get("matchExact", True),
                        region=alert_metric.get("region", "default"),
                    ))

                triggers.append(
                        AlertExpression(
                            refId=alert_metric["refId"],
                            expressionType=EXP_TYPE_REDUCE,
                            expression=alert_metric["refId"]+"-QUERY",
                            reduceFunction=alert["reduce_function"],
                            reduceMode=EXP_REDUCER_FUNC_DROP_NN
                        ))

            triggers.append(
                AlertExpression(
                refId="ALERT_CONDITION",
                expressionType=EXP_TYPE_MATH,
                expression=alert["alert_expression"],
            ))

            return triggers

        return [
            CloudwatchMetricsTarget(
                refId='QUERY',
                namespace=alert["metric"].get("namespace", self.metric_namespace),
                metricName=alert["metric"]["name"],
                statistics=alert["metric"]["statistics"],
                dimensions=alert["metric"]["dimensions"],
                datasource=self.datasource if self.datasource else "cloudwatch",
                matchExact=alert["metric"].get("matchExact", True),
                region=alert["metric"].get("region", "default"),
            ),
            AlertExpression(
                refId="REDUCE_EXPRESSION",
                expressionType=EXP_TYPE_REDUCE,
                expression='QUERY',
                reduceFunction=alert["reduce_function"],
                reduceMode=EXP_REDUCER_FUNC_DROP_NN
            ),
            AlertExpression(
                refId="ALERT_CONDITION",
                expressionType=EXP_TYPE_MATH,
                expression=alert["alert_expression"],
            )
        ]

class PrometheusAlertRuleBuilder(AlertRuleBuilder):
    """
    A class for building Prometheus alert rules.
    """

    def build(self):
        """
        Build the Prometheus alert rules.

        Args:
            uid_prefix (str): The prefix to be added to the UID of each alert rule.

        Returns:
            list: A list of AlertRulev11 objects representing the built alert rules.
        """
        __alert_rules__ = []
        for _, alert in enumerate(self.rules):
            __alert_rules__.append(
                AlertRulev11(
                    title=alert["title"],
                    triggers=self._generate_triggers(alert),
                    timeRangeFrom=self._convert_time_range_to_number(alert["time_range"].to_json_data()[0]),
                    timeRangeTo=self._convert_time_range_to_number(alert["time_range"].to_json_data()[1]),
                    annotations=alert["annotations"],
                    labels=alert["labels"],
                    condition="ALERT_CONDITION",
                    noDataAlertState=alert["no_data_alert_state"],
                    errorAlertState=alert["execute_error_alert_state"],
                    evaluateFor=self.evaluateFor,
                    uid=create_uid_from_string(alert["title"]),
                    panel_id=alert["panelId"],
                    dashboard_uid=self.dashboard_uid,
                )
            )

        return __alert_rules__

    def _generate_triggers(self, alert):

        if isinstance(alert["metric"], list):
            triggers=[]
            for alert_metric in alert["metric"]:
                triggers.append(
                    PrometheusTarget(
                        refId=alert_metric["refId"]+"-QUERY",
                        expr=alert_metric["expr"],
                        legendFormat=alert_metric["legendFormat"],
                        datasource=self.datasource if self.datasource else "prometheus",
                    ))

                triggers.append(
                        AlertExpression(
                            refId=alert_metric["refId"],
                            expressionType=EXP_TYPE_REDUCE,
                            expression=alert_metric["refId"]+"-QUERY",
                            reduceFunction=alert["reduce_function"],
                            reduceMode=EXP_REDUCER_FUNC_DROP_NN
                        ))

            triggers.append(
                AlertExpression(
                refId="ALERT_CONDITION",
                expressionType=EXP_TYPE_MATH,
                expression=alert["alert_expression"],
            ))

            return triggers

        return [
            PrometheusTarget(
                refId='QUERY',
                expr=alert["metric"]["expr"],
                legendFormat=alert["metric"]["legendFormat"],
                datasource=self.datasource if self.datasource else "prometheus",
            ),
            AlertExpression(
                refId="REDUCE_EXPRESSION",
                expressionType=EXP_TYPE_REDUCE,
                expression='QUERY',
                reduceFunction=alert["reduce_function"],
                reduceMode=EXP_REDUCER_FUNC_DROP_NN
            ),
            AlertExpression(
                refId="ALERT_CONDITION",
                expressionType=EXP_TYPE_MATH,
                expression=alert["alert_expression"],
            )
        ]

class ElasticSearchAlertRuleBuilder(AlertRuleBuilder):
    """
    A class for building ElasticSearchTarget alert rules.
    """

    def register(self, title, bucket_aggs, query, datasource, reduce_function,
                 alert_expression, alert_msg,
                 labels, panelId, interval_ms=1000, apply_auto_bucket_agg_ids_function=False,
                 metric_aggs=[CountMetricAgg()], time_range=TimeRange('5m', 'now'),
                 no_data_alert_state=ALERTRULE_STATE_DATA_KEEPLAST_V11, execute_error_alert_state=ALERTRULE_STATE_DATA_ALERTING):
        """
        Register a new alert rule.

        Args:
            title (str): The title of the alert rule.
            metric (dict): The metric configuration for the alert rule.
            reduce_function (str): Function used in reduces expression
            alert_expression (str): The expression used to define the alert condition.
            alert_msg (str): The summary message for the alert.
            labels (dict): The labels associated with the alert rule.
            panelId (str): The panel ID associated with the alert rule.
            time_range (TimeRange): The time range for the alert rule. Default is '5m' to 'now'.
        """
        rule = {
            "title": title,
            "query": query,
            "bucket_aggs": bucket_aggs,
            "metric_aggs": metric_aggs,
            "interval_ms": interval_ms,
            "datasource": datasource,
            "reduce_function": reduce_function,
            "alert_expression": alert_expression,
            "time_range": time_range,
            "annotations": {
                "summary": alert_msg,
                "status": '{{- with $values -}}{{- $lastValue := "" -}}{{- $lastInstance := "" -}}{{- range $k, $v := . -}}{{- $lastValue = $v -}}{{- $lastInstance = $v.Labels -}}{{- end -}}\nInstance: {{ $lastInstance }} | Value:   {{ $lastValue }}{{- end -}}',
            },
            "labels": labels,
            "apply_auto_bucket_function": apply_auto_bucket_agg_ids_function,
            "panelId": panelId,
            "no_data_alert_state": no_data_alert_state,
            "execute_error_alert_state": execute_error_alert_state
        }

        if self.dashboard_uid != "":
            rule["annotations"]["__panelId__"] = panelId
            rule["annotations"]["__dashboardUid__"] = self.dashboard_uid

        self.rules.append(rule)

    def build(self):
        """
        Build the CloudWatch alert rules.

        Args:
            uid_prefix (str): The prefix to be added to the UID of each alert rule.

        Returns:
            list: A list of AlertRulev11 objects representing the built alert rules.
        """
        __alert_rules__ = []
        for _, alert in enumerate(self.rules):
            target = ElasticsearchTarget(
                query=alert["query"],
                bucketAggs=alert["bucket_aggs"],
                metricAggs=alert["metric_aggs"],
                intervalMs=alert["interval_ms"],
                refId='QUERY',
                datasource=alert["datasource"]
            )
            if alert["apply_auto_bucket_function"]:
                target = target.auto_bucket_agg_ids()

            __alert_rules__.append(
                AlertRulev11(
                    title=alert["title"],
                    triggers=[
                        target,
                        AlertExpression(
                            refId="REDUCE_EXPRESSION",
                            expressionType=EXP_TYPE_REDUCE,
                            expression='QUERY',
                            reduceFunction=alert["reduce_function"],
                            reduceMode=EXP_REDUCER_FUNC_DROP_NN
                        ),
                        AlertExpression(
                            refId="ALERT_CONDITION",
                            expressionType=EXP_TYPE_MATH,
                            expression=alert["alert_expression"],
                        )],
                    timeRangeFrom=self._convert_time_range_to_number(alert["time_range"].to_json_data()[0]),
                    timeRangeTo=self._convert_time_range_to_number(alert["time_range"].to_json_data()[1]),
                    annotations=alert["annotations"],
                    labels=alert["labels"],
                    condition="ALERT_CONDITION",
                    noDataAlertState=alert["no_data_alert_state"],
                    errorAlertState=alert["execute_error_alert_state"],
                    evaluateFor=self.evaluateFor,
                    uid=create_uid_from_string(alert["title"]),
                    panel_id=alert["panelId"],
                    dashboard_uid=self.dashboard_uid,
                )
            )

        return __alert_rules__
