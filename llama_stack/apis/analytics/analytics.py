# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable

from pydantic import BaseModel, Field

from llama_stack.providers.utils.telemetry.trace_protocol import trace_protocol
from llama_stack.schema_utils import json_schema_type, webmethod


class MetricType(Enum):
    """Types of metrics that can be tracked.
    
    :cvar COUNTER: A value that can only increase
    :cvar GAUGE: A value that can go up or down
    :cvar HISTOGRAM: Distribution of values
    :cvar SUMMARY: Summary statistics (count, sum, mean, etc.)
    """
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertSeverity(Enum):
    """Severity levels for alerts.
    
    :cvar INFO: Informational alert
    :cvar WARNING: Warning alert
    :cvar ERROR: Error alert
    :cvar CRITICAL: Critical alert
    """
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@json_schema_type
class Metric(BaseModel):
    """Definition of a metric to track.
    
    :param name: Name of the metric
    :param description: Description of the metric
    :param type: Type of metric
    :param labels: Labels/dimensions for the metric
    :param unit: Unit of measurement
    """
    name: str
    description: Optional[str] = None
    type: MetricType
    labels: Optional[List[str]] = Field(default_factory=list)
    unit: Optional[str] = None


@json_schema_type
class MetricValue(BaseModel):
    """Value of a metric at a point in time.
    
    :param metric_name: Name of the metric
    :param value: Value of the metric
    :param timestamp: Time when the metric was recorded
    :param labels: Label values for the metric
    """
    metric_name: str
    value: float
    timestamp: str
    labels: Optional[Dict[str, str]] = Field(default_factory=dict)


@json_schema_type
class MetricQuery(BaseModel):
    """Query for retrieving metric values.
    
    :param metric_name: Name of the metric to query
    :param start_time: Start time for the query
    :param end_time: End time for the query
    :param aggregation: Aggregation function to apply
    :param group_by: Labels to group by
    :param filters: Filters to apply to the query
    """
    metric_name: str
    start_time: str
    end_time: str
    aggregation: Optional[str] = None
    group_by: Optional[List[str]] = Field(default_factory=list)
    filters: Optional[Dict[str, str]] = Field(default_factory=dict)


@json_schema_type
class MetricQueryResult(BaseModel):
    """Result of a metric query.
    
    :param metric_name: Name of the metric
    :param timestamps: List of timestamps
    :param values: List of values corresponding to timestamps
    :param groups: Grouping information if group_by was specified
    """
    metric_name: str
    timestamps: List[str]
    values: List[float]
    groups: Optional[Dict[str, List[str]]] = Field(default_factory=dict)


@json_schema_type
class Dashboard(BaseModel):
    """Definition of a dashboard.
    
    :param dashboard_id: Unique identifier for the dashboard
    :param name: Name of the dashboard
    :param description: Description of the dashboard
    :param panels: List of panels in the dashboard
    :param refresh_interval: How often to refresh the dashboard (in seconds)
    """
    dashboard_id: str
    name: str
    description: Optional[str] = None
    panels: List[Dict[str, Any]] = Field(default_factory=list)
    refresh_interval: Optional[int] = 60


@json_schema_type
class AlertRule(BaseModel):
    """Rule for generating alerts based on metric values.
    
    :param rule_id: Unique identifier for the rule
    :param name: Name of the rule
    :param description: Description of the rule
    :param metric_name: Name of the metric to monitor
    :param condition: Condition that triggers the alert
    :param severity: Severity of the alert
    :param labels: Labels to attach to the alert
    :param annotations: Additional information about the alert
    """
    rule_id: str
    name: str
    description: Optional[str] = None
    metric_name: str
    condition: str
    severity: AlertSeverity
    labels: Optional[Dict[str, str]] = Field(default_factory=dict)
    annotations: Optional[Dict[str, str]] = Field(default_factory=dict)


@json_schema_type
class Alert(BaseModel):
    """Alert generated when a rule condition is met.
    
    :param alert_id: Unique identifier for the alert
    :param rule_id: ID of the rule that generated the alert
    :param timestamp: Time when the alert was generated
    :param severity: Severity of the alert
    :param summary: Summary of the alert
    :param details: Detailed information about the alert
    :param labels: Labels attached to the alert
    :param status: Status of the alert (active, resolved, etc.)
    """
    alert_id: str
    rule_id: str
    timestamp: str
    severity: AlertSeverity
    summary: str
    details: Optional[str] = None
    labels: Optional[Dict[str, str]] = Field(default_factory=dict)
    status: str


@json_schema_type
class UsageReport(BaseModel):
    """Report on usage of AI resources.
    
    :param report_id: Unique identifier for the report
    :param start_time: Start time for the report period
    :param end_time: End time for the report period
    :param user_id: ID of the user (if applicable)
    :param resource_type: Type of resource (model, agent, etc.)
    :param resource_id: ID of the resource
    :param metrics: Usage metrics
    :param cost: Cost information
    """
    report_id: str
    start_time: str
    end_time: str
    user_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    cost: Optional[Dict[str, Any]] = Field(default_factory=dict)


@runtime_checkable
@trace_protocol
class Analytics(Protocol):
    """Llama Stack Analytics API for monitoring, alerting, and reporting.
    
    This API provides enterprise-grade analytics capabilities for Llama Stack:
    - Real-time monitoring of AI model performance
    - Usage tracking and cost estimation
    - Alerting for anomalies and issues
    - Dashboards for visualizing metrics
    - Usage reporting for billing and capacity planning
    """
    
    @webmethod(route="/analytics/metrics", method="POST")
    async def create_metric(
        self,
        metric: Metric,
    ) -> Metric:
        """Create a new metric definition.
        
        :param metric: Metric to create
        :returns: Created metric
        """
        ...
    
    @webmethod(route="/analytics/metrics/{metric_name}", method="GET")
    async def get_metric(
        self,
        metric_name: str,
    ) -> Metric:
        """Get a metric definition by name.
        
        :param metric_name: Name of the metric
        :returns: Metric definition
        """
        ...
    
    @webmethod(route="/analytics/metrics/{metric_name}", method="DELETE")
    async def delete_metric(
        self,
        metric_name: str,
    ) -> None:
        """Delete a metric definition.
        
        :param metric_name: Name of the metric
        """
        ...
    
    @webmethod(route="/analytics/metrics/values", method="POST")
    async def record_metric(
        self,
        metric_value: MetricValue,
    ) -> None:
        """Record a metric value.
        
        :param metric_value: Metric value to record
        """
        ...
    
    @webmethod(route="/analytics/metrics/query", method="POST")
    async def query_metrics(
        self,
        query: MetricQuery,
    ) -> MetricQueryResult:
        """Query metric values.
        
        :param query: Query parameters
        :returns: Query results
        """
        ...
    
    @webmethod(route="/analytics/dashboards", method="POST")
    async def create_dashboard(
        self,
        dashboard: Dashboard,
    ) -> Dashboard:
        """Create a new dashboard.
        
        :param dashboard: Dashboard to create
        :returns: Created dashboard
        """
        ...
    
    @webmethod(route="/analytics/dashboards/{dashboard_id}", method="GET")
    async def get_dashboard(
        self,
        dashboard_id: str,
    ) -> Dashboard:
        """Get a dashboard by ID.
        
        :param dashboard_id: ID of the dashboard
        :returns: Dashboard
        """
        ...
    
    @webmethod(route="/analytics/dashboards/{dashboard_id}", method="PUT")
    async def update_dashboard(
        self,
        dashboard_id: str,
        dashboard: Dashboard,
    ) -> Dashboard:
        """Update a dashboard.
        
        :param dashboard_id: ID of the dashboard
        :param dashboard: Updated dashboard
        :returns: Updated dashboard
        """
        ...
    
    @webmethod(route="/analytics/dashboards/{dashboard_id}", method="DELETE")
    async def delete_dashboard(
        self,
        dashboard_id: str,
    ) -> None:
        """Delete a dashboard.
        
        :param dashboard_id: ID of the dashboard
        """
        ...
    
    @webmethod(route="/analytics/alerts/rules", method="POST")
    async def create_alert_rule(
        self,
        rule: AlertRule,
    ) -> AlertRule:
        """Create a new alert rule.
        
        :param rule: Alert rule to create
        :returns: Created alert rule
        """
        ...
    
    @webmethod(route="/analytics/alerts/rules/{rule_id}", method="GET")
    async def get_alert_rule(
        self,
        rule_id: str,
    ) -> AlertRule:
        """Get an alert rule by ID.
        
        :param rule_id: ID of the alert rule
        :returns: Alert rule
        """
        ...
    
    @webmethod(route="/analytics/alerts/rules/{rule_id}", method="PUT")
    async def update_alert_rule(
        self,
        rule_id: str,
        rule: AlertRule,
    ) -> AlertRule:
        """Update an alert rule.
        
        :param rule_id: ID of the alert rule
        :param rule: Updated alert rule
        :returns: Updated alert rule
        """
        ...
    
    @webmethod(route="/analytics/alerts/rules/{rule_id}", method="DELETE")
    async def delete_alert_rule(
        self,
        rule_id: str,
    ) -> None:
        """Delete an alert rule.
        
        :param rule_id: ID of the alert rule
        """
        ...
    
    @webmethod(route="/analytics/alerts", method="GET")
    async def get_alerts(
        self,
        rule_id: Optional[str] = None,
        severity: Optional[AlertSeverity] = None,
        status: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: Optional[int] = 100,
        offset: Optional[int] = 0,
    ) -> List[Alert]:
        """Get alerts with optional filtering.
        
        :param rule_id: Filter by rule ID
        :param severity: Filter by severity
        :param status: Filter by status
        :param start_time: Filter by start time
        :param end_time: Filter by end time
        :param limit: Maximum number of alerts to return
        :param offset: Offset for pagination
        :returns: List of alerts
        """
        ...
    
    @webmethod(route="/analytics/usage/report", method="POST")
    async def generate_usage_report(
        self,
        start_time: str,
        end_time: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        include_cost: Optional[bool] = True,
    ) -> UsageReport:
        """Generate a usage report.
        
        :param start_time: Start time for the report period
        :param end_time: End time for the report period
        :param user_id: Filter by user ID
        :param resource_type: Filter by resource type
        :param resource_id: Filter by resource ID
        :param include_cost: Whether to include cost information
        :returns: Usage report
        """
        ...
    
    @webmethod(route="/analytics/usage/reports/{report_id}", method="GET")
    async def get_usage_report(
        self,
        report_id: str,
    ) -> UsageReport:
        """Get a usage report by ID.
        
        :param report_id: ID of the report
        :returns: Usage report
        """
        ...
