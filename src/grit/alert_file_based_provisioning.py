import inspect
import sys

from attr import define, field

import grafanalib.core

from .helpers import gen_random_str

ALERT_RULES_MAGIC_STR = '__alert_rules__'

@define
class GritAlert(grafanalib.core.AlertFileBasedProvisioning):
    """
    Compose dashboard from Stack

    """

    def __init__(self, **kwargs):
        self.__attrs_init__(**kwargs)
        caller = inspect.currentframe().f_back
        caller_module = sys.modules[caller.f_globals['__name__']]
        setattr(caller_module, ALERT_RULES_MAGIC_STR + gen_random_str(), self)
