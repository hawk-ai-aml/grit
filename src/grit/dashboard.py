import inspect
import sys

from attr import define, field, ib

import grafanalib.core

from .stack import Stack
from .helpers import gen_random_str

DASHBOARD_MAGIC_STR = '__dashboard__'


@define
class GritDash(grafanalib.core.Dashboard):
    """
    Compose dashboard from Stack

    :param stack: stack of panel rows
    :param dataSource: dataSource for panels
    :param register: automatically register the dashboard

    """
    stack: Stack = field(default=Stack())
    dataSource: str = ib(default=False)
    panels: list[grafanalib.core.Panel] = field(default=[])
    register: bool = True

    def __init__(self, **kwargs):
        self.__attrs_init__(**kwargs)
        caller = inspect.currentframe().f_back
        caller_module = sys.modules[caller.f_globals['__name__']]
        setattr(caller_module, DASHBOARD_MAGIC_STR + gen_random_str(), self)

    def __attrs_post_init__(self):
        def dataSource_override(p: grafanalib.core.Panel):
            if not hasattr(p, 'dataSource') or p.dataSource == None:
                p.dataSource = self.dataSource
            return p

        self.panels = list(map(dataSource_override, self.stack.to_panels()))
