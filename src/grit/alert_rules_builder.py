from attr import define, field

import grafanalib.core

from grafanalib.core import (
    AlertExpression,
    EXP_TYPE_REDUCE, EXP_TYPE_MATH, EXP_REDUCER_FUNC_DROP_NN, EXP_REDUCER_FUNC_LAST, CTYPE_QUERY,
    AlertRulev11, Target, TimeRange
)

from grafanalib.cloudwatch import CloudwatchMetricsTarget
from grafanalib.prometheus_target import PrometheusTarget
from grafanalib.elasticsearch import ElasticsearchTarget, DateHistogramGroupBy
from abc import ABC, abstractmethod


class AlertRuleBuilder(ABC):
    """
    An interface class for building alert rules.
    """

    def __init__(self, environment, evaluateFor, uid_prefix):
        """
        Initialize the AlertRuleBuilder.

        Args:
            evaluateFor (int): The duration in seconds for which the alert condition must be met.
        """
        self.rules = []
        self.environment = environment
        self.evaluateFor = evaluateFor
        self.uid_prefix = uid_prefix

    def register(self, title, metric, alert_expression, alert_msg, labels, __panelId__,
                 time_range=TimeRange('5m', 'now')):
        """
        Register a new alert rule.

        Args:
            title (str): The title of the alert rule.
            metric (dict): The metric configuration for the alert rule.
            alert_expression (str): The expression used to define the alert condition.
            alert_msg (str): The summary message for the alert.
            labels (dict): The labels associated with the alert rule.
            __panelId__ (str): The panel ID associated with the alert rule.
        """
        rule = {
            "title": title,
            "metric": metric,
            "alert_expression": alert_expression,
            "time_range": time_range,
            "annotations": {
                "summary": alert_msg
            },
            "labels": labels,
            "__panelId__": __panelId__
        }
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

    def convert_time_range_to_number(self, time_range):
        """
        Convert time range to seconds.

        Args:
            time_range (str): Time range in format '1h', '2d', '3w', etc.

        Returns:
            int: Time range in seconds.
        """
        if time_range == 'now':
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

    def __init__(self, environment, evaluateFor, uid_prefix, metric_namespace):
        super().__init__(environment, evaluateFor, uid_prefix)
        self.metric_namespace = metric_namespace

    def register(self, title, metric, reduce_function, alert_expression, alert_msg, labels, __panelId__,
                 time_range=TimeRange('5m', 'now')):
        """
        Register a new alert rule.

        Args:
            title (str): The title of the alert rule.
            metric (dict): The metric configuration for the alert rule.
            reduce_function (str): Function used in reduces expression
            alert_expression (str): The expression used to define the alert condition.
            alert_msg (str): The summary message for the alert.
            labels (dict): The labels associated with the alert rule.
            __panelId__ (str): The panel ID associated with the alert rule.
            time_range (TimeRange): The time range for the alert rule. Default is '5m' to 'now'.
        """
        super().register(title, metric, alert_expression, alert_msg, labels, __panelId__, time_range)
        self.rules[-1]["reduce_function"] = reduce_function

    def build(self):
        """
        Build the CloudWatch alert rules.

        Args:
            uid_prefix (str): The prefix to be added to the UID of each alert rule.

        Returns:
            list: A list of AlertRulev11 objects representing the built alert rules.
        """
        __alert_rules__ = []
        for _id, alert in enumerate(self.rules):
            __alert_rules__.append(
                AlertRulev11(
                    title=alert["title"],
                    triggers=[
                        CloudwatchMetricsTarget(
                            refId='QUERY',
                            namespace=alert["metric"].get("namespace", self.metric_namespace),
                            metricName=alert["metric"]["name"],
                            statistics=alert["metric"]["statistics"],
                            dimensions=alert["metric"]["dimensions"],
                            datasource="cloudwatch"
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
                        )],
                    timeRangeFrom=self.convert_time_range_to_number(alert["time_range"].to_json_data()[0]),
                    timeRangeTo=self.convert_time_range_to_number(alert["time_range"].to_json_data()[1]),
                    annotations=alert["annotations"],
                    labels=alert["labels"],
                    condition="ALERT_CONDITION",
                    evaluateFor=self.evaluateFor,
                    uid=self.uid_prefix + str(_id),
                )
            )

        return __alert_rules__


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
        for _id, alert in enumerate(self.rules):
            __alert_rules__.append(
                AlertRulev11(
                    title=alert["title"],
                    triggers=[
                        PrometheusTarget(
                            refId='QUERY',
                            expr=alert["metric"]["expr"],
                            legendFormat=alert["metric"]["legendFormat"],
                            datasource="prometheus"
                        ),
                        AlertExpression(
                            refId="REDUCE_EXPRESSION",
                            expressionType=EXP_TYPE_REDUCE,
                            expression='QUERY',
                            reduceFunction=EXP_REDUCER_FUNC_LAST,
                            reduceMode=EXP_REDUCER_FUNC_DROP_NN
                        ),
                        AlertExpression(
                            refId="ALERT_CONDITION",
                            expressionType=EXP_TYPE_MATH,
                            expression=alert["alert_expression"],
                        )],
                    timeRangeFrom=self.convert_time_range_to_number(alert["time_range"].to_json_data()[0]),
                    timeRangeTo=self.convert_time_range_to_number(alert["time_range"].to_json_data()[1]),
                    annotations=alert["annotations"],
                    labels=alert["labels"],
                    condition="ALERT_CONDITION",
                    evaluateFor=self.evaluateFor,
                    uid=self.uid_prefix + str(_id),
                )
            )

        return __alert_rules__


class ElasticSearchAlertRuleBuilder(AlertRuleBuilder):
    """
    A class for building CloudWatch alert rules.
    """

    def __init__(self, environment, evaluateFor, uid_prefix):
        super().__init__(environment, evaluateFor, uid_prefix)

    def register(self, title, bucket_aggs, metric_aggs, query, datasource, reduce_function, alert_expression, alert_msg,
                 labels, __panelId__, time_range=TimeRange('5m', 'now')):
        """
        Register a new alert rule.

        Args:
            title (str): The title of the alert rule.
            metric (dict): The metric configuration for the alert rule.
            reduce_function (str): Function used in reduces expression
            alert_expression (str): The expression used to define the alert condition.
            alert_msg (str): The summary message for the alert.
            labels (dict): The labels associated with the alert rule.
            __panelId__ (str): The panel ID associated with the alert rule.
            time_range (TimeRange): The time range for the alert rule. Default is '5m' to 'now'.
        """
        rule = {
            "title": title,
            "query": query,
            "bucket_aggs": bucket_aggs,
            "metric_aggs": metric_aggs,
            "datasource": datasource,
            "alert_expression": alert_expression,
            "time_range": time_range,
            "annotations": {
                "summary": alert_msg
            },
            "labels": labels,
            "__panelId__": __panelId__
        }
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
        for _id, alert in enumerate(self.rules):
            __alert_rules__.append(
                AlertRulev11(
                    title=alert["title"],
                    triggers=[
                        ElasticsearchTarget(
                            query=alert["query"],
                            bucketAggs=alert["bucket_aggs"],
                            metricAggs=alert["metric_aggs"],
                            refId='QUERY',
                            datasource=alert["datasource"]
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
                        )],
                    timeRangeFrom=self.convert_time_range_to_number(alert["time_range"].to_json_data()[0]),
                    timeRangeTo=self.convert_time_range_to_number(alert["time_range"].to_json_data()[1]),
                    annotations=alert["annotations"],
                    labels=alert["labels"],
                    condition="ALERT_CONDITION",
                    evaluateFor=self.evaluateFor,
                    uid=self.uid_prefix + str(_id),
                )
            )

        return __alert_rules__
