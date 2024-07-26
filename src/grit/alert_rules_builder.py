from attr import define, field

import grafanalib.core

from grafanalib.core import (
    AlertExpression,
    EXP_TYPE_REDUCE, EXP_TYPE_MATH, EXP_REDUCER_FUNC_DROP_NN, EXP_REDUCER_FUNC_LAST, CTYPE_QUERY,
    AlertRulev11
)

from grafanalib.cloudwatch import CloudwatchMetricsTarget

@define
class CloudwatchAlertRuleBuilder:
    """
    A class for building CloudWatch alert rules.
    """

    rules: list[dict] = field(default=[])
    evaluateFor: int = field(default=0)
    environment: object = field(default=None)
    
    def __init__(self, environment, evaluateFor):
        """
        Initialize the CloudwatchAlertRuleBuilder.

        Args:
            evaluateFor (int): The duration in seconds for which the alert condition must be met.
        """
        self.rules = []
        self.environment = environment
        self.evaluateFor = evaluateFor

    def register(self, title, metric, alert_expression, alert_msg, labels, __panelId__):
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
            "annotations": {
                "summary": alert_msg
            },
            "labels": labels,
            "__panelId__": __panelId__
        }
        self.rules.append(rule)

    def build(self, uid_prefix):
        """
        Build the CloudWatch alert rules.

        Args:
            uid_prefix (str): The prefix to be added to the UID of each alert rule.

        Returns:
            list: A list of AlertRulev11 objects representing the built alert rules.
        """
        __alert_rules__=[]
        for _id, alert in enumerate(self.rules):
            __alert_rules__.append(
                AlertRulev11(
                    title=alert["title"],
                    triggers=[
                        CloudwatchMetricsTarget(
                            refId='QUERY',
                            namespace="AWS/ES",
                            metricName=alert["metric"]["name"],
                            statistics=alert["metric"]["statistics"],
                            dimensions=alert["metric"]["dimensions"],
                            datasource="cloudwatch"
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
                    annotations=alert["annotations"],
                    labels=alert["labels"],
                    condition="ALERT_CONDITION",
                    evaluateFor=self.evaluateFor,
                    uid=uid_prefix + str(_id),
                )
            )
        
        return __alert_rules__
