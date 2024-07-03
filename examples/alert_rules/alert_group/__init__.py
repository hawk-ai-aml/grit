from .alert_rule import *
from grit.alert_rules_group import AlertRulesGroup

AlertRulesGroup(name="TestGroup",
                rules=[alert_rule.get_rule()],
                folder="AWS",
                evaluateInterval="1m")
