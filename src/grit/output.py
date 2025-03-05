from abc import ABC, abstractmethod
from typing import Any
import os
import attr

from grafanalib.core import Dashboard, AlertFileBasedProvisioning, Templating

from grit import DashboardEncoder, json

class GritOut(ABC):
    """
    Interface for Grit dashboard components.
    Ensures consistent structure for dashboard classes like EXCEPTIONS.
    """

    # Class attributes expected in EXCEPTIONS
    DASHBOARD_TITLE: str
    DASHBOARD_UUID: str

    def __init__(self, environment: Any, datasources: Any, services: list[str]=[], folder_name: str=""):
        """
        Initialize the GritOut instance.

        Args:
            environment (Any): Environment configuration object.
            datasources (Any): Data sources for the dashboards.
            services (List[str]): List of services to monitor.
            folder_name (str): Name of the alert folder.
        """
        self.environment = environment
        self.datasources = datasources
        self.services = services
        self.folder_name = folder_name

        self.dash_obj:Dashboard = []
        self.alert_obj:AlertFileBasedProvisioning = []

    def init__alerts(self) -> None:
        """Optional: Initialize alerts for the dashboard."""
        print("Default init__alerts method. Override if needed.")

    def init_dashboard(self, datasource, templating=attr.Factory(Templating)) -> None:
        """Initialize the GritDash Object and adds it to the processing list

        Args:
            datasource (Any): Datasource class object
        """
        from grit import GritDash

        self.dash_obj.append(
            GritDash(
                uid=self.DASHBOARD_UUID,
                title=self.DASHBOARD_TITLE,
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
                    rules=AlertRuleBuilder.build_all(self.es_alerts),
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
                with open(f"{out_base_dir_alerts}/{_obj.uid}.json", "w") as file:
                    file.write(json.dumps(
                        _obj.to_json_data(), sort_keys=True, indent=2, cls=DashboardEncoder))
