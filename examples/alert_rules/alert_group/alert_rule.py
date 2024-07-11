from grafanalib.cloudwatch import CloudwatchMetricsTarget
from grafanalib.core import (
    AlertRulev11, AlertExpression, EXP_TYPE_REDUCE, EXP_REDUCER_MODE_STRICT, EXP_TYPE_MATH, AlertGroup
)


def get_rule():
    return rule


rule = AlertRulev11(
    title="AWS EC2 | High CPU Utilization",
    triggers=[
        CloudwatchMetricsTarget(
            region="default",
            namespace="AWS/EC2",
            metricName="CPUUtilization",
            statistics=["Average"],
            dimensions={'InstanceId': '*'},
            matchExact=True,
            refId='A',
        ),
        AlertExpression(
            refId="B",
            expressionType=EXP_TYPE_REDUCE,
            expression='A',
            reduceFunction='mean',
            reduceMode=EXP_REDUCER_MODE_STRICT
        ),
        AlertExpression(
            refId="C",
            expressionType=EXP_TYPE_MATH,
            expression='$B > 90'
        )],
    annotations={
        "summary": "High CPU Utilization on AWS EC2 instances",
        "__dashboardUid__": "uid-ec2-alerts",
        "__panelId__": "1"
    },
    labels={"severity": "critical"},
    condition="C",
    evaluateFor="1m",
    uid="alertTestSerg",
    dashboard_uid="uid-ec2-alerts",
    panel_id=1
)
