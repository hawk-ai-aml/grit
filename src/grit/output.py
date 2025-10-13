from abc import ABC, abstractmethod
from typing import Any
import os
from attr import define

from grafanalib.core import Dashboard, AlertFileBasedProvisioning, Templating, Time

from grit import DashboardEncoder, json

@define
class GritOut(ABC):
    """
    Interface for Grit dashboard components.
    Ensures consistent structure for dashboard classes like EXCEPTIONS.
    """



    def __init__(self, environment: Any, datasources: Any, services: list[str]=[], folder_name: str=""):
        """
        Initialize the GritOut instance.

        Args:
            environment (Any): Environment configuration object.
            datasources (Any): Data sources for the dashboards.
            services (List[str]): List of services to monitor.
            folder_name (str): Name of the alert folder.
        """
        self._alert_rule_builder:list = []
        self._dashboard_title = ""
        self._dashboard_uuid = ""

        self.environment = environment
        self.datasources = datasources
        self.services = services
        self.folder_name = folder_name

        self.dash_obj:Dashboard = []
        self.alert_obj:AlertFileBasedProvisioning = []

    @property
    def DASHBOARD_TITLE(self):
        """Deprecated: Use `dashboard_title` property instead"""
        return self._dashboard_title
    
    @DASHBOARD_TITLE.setter
    def DASHBOARD_TITLE(self, value):
        self._dashboard_title = value

    @property
    def dashboard_title(self):
        """The title of the dashboard"""
        return self._dashboard_title
    
    @dashboard_title.setter
    def dashboard_title(self, value):
        self._dashboard_title = value

    @property
    def DASHBOARD_UUID(self):
        """Deprecated: Use `dashboard_uuid` property instead"""
        return self._dashboard_uuid
    
    @DASHBOARD_UUID.setter
    def DASHBOARD_UUID(self, value):
        self._dashboard_uuid = value

    @property
    def dashboard_uuid(self):
        """The unique identifier for the dashboard"""
        return self._dashboard_uuid
    
    @dashboard_uuid.setter
    def dashboard_uuid(self, value):
        self._dashboard_uuid = value

    @property
    def alert_rule_builder(self):
        """The list of AlertRuleBuilder objects to append to the group"""
        return self._alert_rule_builder
    
    @property
    def ALERT_RULE_BUILDER(self):
        """Deprecated: Use `alert_rule_builder` property instead"""
        return self._alert_rule_builder
    
    @ALERT_RULE_BUILDER.setter
    def ALERT_RULE_BUILDER(self, value):
        """Deprecated: Should not set this property (noop)"""
        print("noop: ALERT_RULE_BUILDER is deprecated / value is only set in constructor")

    def init__alerts(self) -> None:
        """Optional: Initialize alerts for the dashboard."""
        print("Default init__alerts method. Override if needed.")

    def init_dashboard(self, datasource, templating=Templating(), time=Time('now-1h', 'now')) -> None:
        """Initialize the GritDash Object and adds it to the processing list

        Args:
            datasource (Any): Datasource class object
        """
        from grit import GritDash

        self.dash_obj.append(
            GritDash(
                uid=self.DASHBOARD_UUID,
                title=self.DASHBOARD_TITLE,
                time=time,
                dataSource=datasource,
                templating=templating,
                description="This panel has been provisioned. Manual changes on the panel will be overridden if they are not persisted.",
                tags=['hawk'],
                stack=self.stack()
            )
        )

    def init_alert_group(self, evaluateInterval:str) -> None:
        """Initialize the GritAlert Object and adds it to the processing list

        Args:
            datasource (Any): Datasource class object
        """
        from grit import GritAlert, AlertRuleBuilder
        from grafanalib.core import AlertGroup

        self.alert_obj.append(
            GritAlert(
                uid="{}-alerts".format(self.DASHBOARD_UUID),
                groups=[AlertGroup(
                    name=self.DASHBOARD_TITLE,
                    rules=AlertRuleBuilder.build_all(*self.ALERT_RULE_BUILDER),
                    folder=self.folder_name,
                    evaluateInterval=evaluateInterval
                )]
            )
        )

    @abstractmethod
    def stack(self) -> Any:
        """Define the dashboard stack layout."""
        pass

    def output(self) -> Any:
        """
        Generate the dashboard output.

        Returns:
            Any: The dashboard output.
        """

        out_base_dir = "out/" + self.environment.name
        out_base_dir_alerts = out_base_dir + "-alerts/"

        os.makedirs(f"{out_base_dir}/{self.folder_name}/", exist_ok=True)
        os.makedirs(f"{out_base_dir_alerts}", exist_ok=True)

        for _obj in self.dash_obj:
            if isinstance(_obj, Dashboard):
                with open(f"{out_base_dir}/{self.folder_name}/{self.DASHBOARD_UUID}.json", "w") as file:
                    file.write(json.dumps(
                        _obj.to_json_data(), sort_keys=True, indent=2, cls=DashboardEncoder))

        for _obj in self.alert_obj:
            if isinstance(_obj, AlertFileBasedProvisioning):
                # print(self.ALERT_RULE_BUILDER[0].rules)
                with open(f"{out_base_dir_alerts}/{_obj.uid}.json", "w") as file:
                    file.write(json.dumps(
                        _obj.to_json_data(), sort_keys=True, indent=2, cls=DashboardEncoder))
