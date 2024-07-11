Grid Toolkit for Grafana
===

Generate similar but varying dashboards from code with many variations for hundreds of environments. Based on a forked grafanalib which is maintained by HAWK.

This open source project supports Grafana v11.+ dashboards, alert_rules and notifications.

## Installation and Quick Start

```bash
❯❯❯ virtualenv .py3
❯❯❯ source .py3/bin/activate

❯❯❯ pip install .

❯❯❯ python -m grit -h

# Inspect examples
❯❯❯ python -m grit inspect --module examples.dashboards
# Example output
---
name: examples.dashboards
folders:
- jmeter
- mongodb
variations:
  environment:
  - dev
  - prod
  - qa
  - test

# Generate dashboards for all environments
❯❯❯ python -m grit generate --module examples.dashboards --out 'out/{environment}' --var 'environment=*' 
# Example output 
Generating out/dev
Generating out/prod
Generating out/qa
Generating out/test

```

## Overview
Example dashboard

```python
GritDash(
    uid="human-id",
    version=8,
    title="your dashboard title",
    description="your dashboards description",
    tags=[
        'tag1',
        'tag2'
    ],
    timezone="browser",
    # Apply datasource to all panels in the dashboard
    dataSource="Prometheus",
    stack=Stack(
        row7(panel1),
        # Use simple utilities, row6 is row of panels of height 6
        row6(panel1, panel2),
        # Autosize panels, this will be 3 equal panels in the row
        row5(panel1, panel2, panel3),
        # ... or 4, if you want, no need to calculate coordinates
        row4(panel1, panel2, panel3, panel4),
        # ... sometimes less is more
        row3(panel1, panel2, panel3, panel4, panel5),
    )
)
```

Example alert rules

```python

    GritAlert(
        groups=[AlertGroup(
        name="TestGroup",
        rules=[AlertRulev11(
                title="Provisioning TEST v4.24",
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
                  )],
                annotations={
                    "summary": "High CPU Utilization on AWS EC2 instances",
                    "__dashboardUid__": "uid-ec2-alerts",
                    "__panelId__": "1"
                },
                labels={"severity": "critical", "notification": "slack"},
                condition="C",
                evaluateFor="1m",
                uid="alertTest",
                dashboard_uid="uid-ec2-alerts",
                panel_id=1
      )
    ],
        folder="TEST",
        evaluateInterval="1m"
    )],
        uid="uid-alert-group",
    )

```

# Variations

Variations allow to create a different collection of dashboards from same code base, for example per-environment variation can be achieved with Environment variation.

You can create multiple variations, and quickly generate hundreds of dashboards

```python
# Variation is just subclass of Variation
class Environment(Variation):
  color: str = "green"

Environment(name="dev", color="blue")
Environment(name="qa")
Environment(name="test")
Environment(name="prod", color="red")
```

When writing dashboard you can access specific variation values by calling `<VariationClass>.resolve()`

```python
# Illustrative code
environment = Environment.resolve()
print(environment.color)
print(environment.name)
```

You create as many variations as you want and combine them
```python
class Environment(Variation):
  color: str = "green"

Environment(name="dev", color="blue")
Environment(name="qa")
Environment(name="test")
Environment(name="prod", color="red")

class Turn(Variation):
  pass

class Taste(Variation):
  pass

class Animal(Variation):
  pass

Turn(name="first")
Turn(name="second")
Turn(name="third")

Taste(name="sweet")
Taste(name="sour")

Animal(name="rabbit")
Animal(name="donkey")
Animal(name="turtle")
Animal(name="rat")
```

And use all of them during generation, you can template output directory structure to your liking!

```bash

❯❯❯ python -m grit generate --module grafana.dashboards --out 'out/{turn}-{taste}-{animal}-company/{environment}' --var environment=qa environment=prod animal=* turn=first taste=sweet
Generating out/first-sweet-donkey-company/qa
Generating out/first-sweet-donkey-company/prod
Generating out/first-sweet-rabbit-company/qa
Generating out/first-sweet-rabbit-company/prod
Generating out/first-sweet-rat-company/qa
Generating out/first-sweet-rat-company/prod
Generating out/first-sweet-turtle-company/qa
Generating out/first-sweet-turtle-company/prod
```

# Command-Line

## Inspect dashboards

```yaml
❯❯❯ python -m grit inspect --module dashboards
---
name: dashboards
folders:
- jmeter
- mongodb
variations:
  environment:
  - dev
  - nab-dev
  - nab-prod
  - prod
  - qa
  - test
```

## Publish to Grafana

```
# Needs .env file with some vars
❯❯❯ python -m grit publish --module grafana.dashboards --var environment=dev
```

## Generate to output directory

```shell
❯❯❯ python -m grit generate --module grafana.dashboards --out 'out/{environment}' --var environment=*
Generating out/dev
Generating out/nab-dev
Generating out/nab-prod
Generating out/prod
Generating out/qa
Generating out/test
```

# Utilities

## Rows
You have some handy utilities

### Predefined row heights

Each creating row of respective height
  *  `row3`
  *  `row4`
  *  `row5`
  *  `row6`
  *  `row7`
  *  `row8`

# How to develop

```
virtualenv .py3
source .py3/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
python -m grit --version
```
