import inspect
import sys

from attr import define, field

import grafanalib.core

from .helpers import gen_random_str

ALERT_RULES_MAGIC_STR = '__alert_rules__'

@define
class AlertRulesGroup(grafanalib.core.AlertGroup):
    """
    Compose Alert Rules Group

    :param name: name of the dashboard
    :param rules: list of alert rules
    :param folder: folder name
    :param evaluateInterval: evaluate interval

    """
    name: str = field(default='')
    rules: list[grafanalib.core.AlertRulev11] = field(default=[])
    folder: str = field(default='alert')
    evaluateInterval: str = field(default='1m')

    def __init__(self, **kwargs):
        self.__attrs_init__(**kwargs)
        caller = inspect.currentframe().f_back
        caller_module = sys.modules[caller.f_globals['__name__']]
        setattr(caller_module, ALERT_RULES_MAGIC_STR + gen_random_str(), self)

    def __attrs_post_init__(self):
        super().__init__(
            name=self.name,
            rules=self.rules,
            folder=self.folder,
            evaluateInterval=self.evaluateInterval,
        )
