import inspect
import sys

from attr import define, field, ib

import grafanalib.core

from .helpers import gen_random_str

ALERT_RULES_MAGIC_STR = '__alert_rules__'

@define
class GritAlert(grafanalib.core.AlertFileBasedProvisioning):
    """
    Initialize and group Alert Groups

    :param groups: list of alert groups
    :param uid: unique identifier to generate the alert file

    """
    groups: grafanalib.core.AlertGroup = ib()
    uid: str = ib()

    def __init__(self, **kwargs):
        self.__attrs_init__(**kwargs)
        caller = inspect.currentframe().f_back
        caller_module = sys.modules[caller.f_globals['__name__']]
        setattr(caller_module, ALERT_RULES_MAGIC_STR + gen_random_str(), self)
