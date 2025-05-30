"""
MongoDB Monitoring and Health Check System
Provides comprehensive monitoring, alerting, and performance tracking
for MongoDB operations in the Code Evolution Tracker.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import PyMongoError
import json
import time

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status levels"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class MetricType(Enum):
    """Types of metrics being tracked"""

    CONNECTION = "connection"
    PERFORMANCE = "performance"
    STORAGE = "storage"
    OPERATIONS = "operations"
    ERROR = "error"


@dataclass
class HealthMetric:
    """Individual health metric with thresholds"""

    name: str
    value: Union[int, float, str, bool]
    unit: str = ""
    status: HealthStatus = HealthStatus.UNKNOWN
    threshold_warning: Optional[Union[int, float]] = None
    threshold_critical: Optional[Union[int, float]] = None
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metric_type: MetricType = MetricType.PERFORMANCE

    def evaluate_status(self) -> HealthStatus:
        """Evaluate health status based on value and thresholds"""
        if not isinstance(self.value, (int, float)):
            return self.status

        if (
            self.threshold_critical is not None
            and self.value >= self.threshold_critical
        ):
            self.status = HealthStatus.CRITICAL
            self.message = f"{self.name} is critical: {self.value}{self.unit}"
        elif (
            self.threshold_warning is not None and self.value >= self.threshold_warning
        ):
            self.status = HealthStatus.WARNING
            self.message = f"{self.name} is elevated: {self.value}{self.unit}"
        else:
            self.status = HealthStatus.HEALTHY
            self.message = f"{self.name} is normal: {self.value}{self.unit}"

        return self.status


@dataclass
class HealthCheckResult:
    """Complete health check result"""

    overall_status: HealthStatus
    metrics: List[HealthMetric]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0
    errors: List[str] = field(default_factory=list)

    def get_metrics_by_type(self, metric_type: MetricType) -> List[HealthMetric]:
        """Get metrics filtered by type"""
        return [metric for metric in self.metrics if metric.metric_type == metric_type]

    def get_status_summary(self) -> Dict[str, int]:
        """Get count of metrics by status"""
        summary = {status.value: 0 for status in HealthStatus}
        for metric in self.metrics:
            summary[metric.status.value] += 1
        return summary

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "overall_status": self.overall_status.value,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "status_summary": self.get_status_summary(),
            "metrics": [
                {
                    "name": metric.name,
                    "value": metric.value,
                    "unit": metric.unit,
                    "status": metric.status.value,
                    "type": metric.metric_type.value,
                    "message": metric.message,
                    "timestamp": metric.timestamp.isoformat(),
                }
                for metric in self.metrics
            ],
            "errors": self.errors,
        }


class PerformanceTracker:
    """Track performance metrics over time"""

    def __init__(self, max_history: int = 100):
        """Initialize performance tracker"""
        self.max_history = max_history
        self.metrics_history: Dict[str, List[HealthMetric]] = {}
        self.operation_counts: Dict[str, int] = {}
        self.error_counts: Dict[str, int] = {}

    def record_metric(self, metric: HealthMetric) -> None:
        """Record a metric in history"""
        if metric.name not in self.metrics_history:
            self.metrics_history[metric.name] = []

        history = self.metrics_history[metric.name]
        history.append(metric)

        # Keep only recent history
        if len(history) > self.max_history:
            history.pop(0)

    def record_operation(self, operation: str) -> None:
        """Record an operation count"""
        self.operation_counts[operation] = self.operation_counts.get(operation, 0) + 1

    def record_error(self, error_type: str) -> None:
        """Record an error count"""
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

    def get_average_metric(self, metric_name: str, minutes: int = 5) -> Optional[float]:
        """Get average metric value over last N minutes"""
        if metric_name not in self.metrics_history:
            return None

        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        recent_metrics = [
            metric
            for metric in self.metrics_history[metric_name]
            if metric.timestamp >= cutoff_time
            and isinstance(metric.value, (int, float))
        ]

        if not recent_metrics:
            return None

        return sum(metric.value for metric in recent_metrics) / len(recent_metrics)

    def get_trend(self, metric_name: str, minutes: int = 10) -> Optional[str]:
        """Get trend for a metric (increasing, decreasing, stable)"""
        if metric_name not in self.metrics_history:
            return None

        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        recent_metrics = [
            metric
            for metric in self.metrics_history[metric_name]
            if metric.timestamp >= cutoff_time
            and isinstance(metric.value, (int, float))
        ]

        if len(recent_metrics) < 3:
            return "insufficient_data"

        # Calculate trend using first and last values
        first_value = recent_metrics[0].value
        last_value = recent_metrics[-1].value

        if isinstance(first_value, (int, float)) and isinstance(
            last_value, (int, float)
        ):
            change_percent = (
                ((last_value - first_value) / first_value) * 100
                if first_value != 0
                else 0
            )

            if change_percent > 10:
                return "increasing"
            elif change_percent < -10:
                return "decreasing"
            else:
                return "stable"

        return "unknown"


class MongoDBMonitor:
    """
    Comprehensive MongoDB monitoring system with health checks,
    performance tracking, and alerting capabilities.
    """

    def __init__(
        self,
        database: AsyncIOMotorDatabase,
        alert_callbacks: Optional[List[Callable]] = None,
    ):
        """
        Initialize MongoDB monitor

        Args:
            database: MongoDB database instance
            alert_callbacks: List of callback functions for alerts
        """
        self.database = database
        self.alert_callbacks = alert_callbacks or []
        self.performance_tracker = PerformanceTracker()
        self.last_health_check: Optional[HealthCheckResult] = None
        self.monitoring_active = False
        self._monitoring_task: Optional[asyncio.Task] = None

    async def comprehensive_health_check(self) -> HealthCheckResult:
        """
        Perform comprehensive MongoDB health check

        Returns:
            Complete health check result with all metrics
        """
        start_time = time.time()
        metrics: List[HealthMetric] = []
        errors: List[str] = []

        try:
            # Connection health
            connection_metrics = await self._check_connection_health()
            metrics.extend(connection_metrics)

            # Performance metrics
            performance_metrics = await self._check_performance_metrics()
            metrics.extend(performance_metrics)

            # Storage metrics
            storage_metrics = await self._check_storage_metrics()
            metrics.extend(storage_metrics)

            # Operation metrics
            operation_metrics = await self._check_operation_metrics()
            metrics.extend(operation_metrics)

            # Index health
            index_metrics = await self._check_index_health()
            metrics.extend(index_metrics)

        except Exception as e:
            error_msg = f"Health check error: {e}"
            errors.append(error_msg)
            logger.error(f"❌ {error_msg}")

        # Calculate overall status
        overall_status = self._calculate_overall_status(metrics)

        # Create result
        duration_ms = (time.time() - start_time) * 1000
        result = HealthCheckResult(
            overall_status=overall_status,
            metrics=metrics,
            duration_ms=duration_ms,
            errors=errors,
        )

        # Record metrics in performance tracker
        for metric in metrics:
            self.performance_tracker.record_metric(metric)

        # Store last result
        self.last_health_check = result

        # Trigger alerts if needed
        await self._check_alerts(result)

        return result

    async def _check_connection_health(self) -> List[HealthMetric]:
        """Check MongoDB connection health"""
        metrics = []

        try:
            # Ping test with timing
            start_time = time.time()
            await self.database.command("ping")
            ping_time = (time.time() - start_time) * 1000

            ping_metric = HealthMetric(
                name="ping_response_time",
                value=round(ping_time, 2),
                unit="ms",
                threshold_warning=100.0,
                threshold_critical=500.0,
                metric_type=MetricType.CONNECTION,
            )
            ping_metric.evaluate_status()
            metrics.append(ping_metric)

            # Server status
            server_status = await self.database.command("serverStatus")

            # Connection count
            connections = server_status.get("connections", {})
            current_connections = connections.get("current", 0)
            available_connections = connections.get("available", 0)

            connection_metric = HealthMetric(
                name="active_connections",
                value=current_connections,
                unit="",
                threshold_warning=50,
                threshold_critical=100,
                metric_type=MetricType.CONNECTION,
            )
            connection_metric.evaluate_status()
            metrics.append(connection_metric)

            # Connection availability
            if available_connections > 0:
                connection_usage = (
                    current_connections / (current_connections + available_connections)
                ) * 100
                usage_metric = HealthMetric(
                    name="connection_usage_percent",
                    value=round(connection_usage, 2),
                    unit="%",
                    threshold_warning=70.0,
                    threshold_critical=90.0,
                    metric_type=MetricType.CONNECTION,
                )
                usage_metric.evaluate_status()
                metrics.append(usage_metric)

            # Uptime
            uptime_seconds = server_status.get("uptime", 0)
            uptime_metric = HealthMetric(
                name="server_uptime",
                value=uptime_seconds,
                unit="seconds",
                metric_type=MetricType.CONNECTION,
                status=HealthStatus.HEALTHY,
                message=f"Server uptime: {uptime_seconds // 3600}h {(uptime_seconds % 3600) // 60}m",
            )
            metrics.append(uptime_metric)

        except Exception as e:
            error_metric = HealthMetric(
                name="connection_error",
                value=str(e),
                status=HealthStatus.CRITICAL,
                metric_type=MetricType.ERROR,
                message=f"Connection check failed: {e}",
            )
            metrics.append(error_metric)

        return metrics

    async def _check_performance_metrics(self) -> List[HealthMetric]:
        """Check MongoDB performance metrics"""
        metrics = []

        try:
            server_status = await self.database.command("serverStatus")

            # Memory usage
            memory = server_status.get("mem", {})
            resident_mb = memory.get("resident", 0)
            virtual_mb = memory.get("virtual", 0)

            memory_metric = HealthMetric(
                name="memory_resident",
                value=resident_mb,
                unit="MB",
                threshold_warning=1024,  # 1GB
                threshold_critical=2048,  # 2GB
                metric_type=MetricType.PERFORMANCE,
            )
            memory_metric.evaluate_status()
            metrics.append(memory_metric)

            # Network metrics
            network = server_status.get("network", {})
            bytes_in = network.get("bytesIn", 0)
            bytes_out = network.get("bytesOut", 0)

            network_in_metric = HealthMetric(
                name="network_bytes_in",
                value=bytes_in,
                unit="bytes",
                metric_type=MetricType.PERFORMANCE,
                status=HealthStatus.HEALTHY,
                message=f"Network bytes in: {bytes_in:,}",
            )
            metrics.append(network_in_metric)

            # Operations per second
            opcounters = server_status.get("opcounters", {})
            insert_ops = opcounters.get("insert", 0)
            query_ops = opcounters.get("query", 0)
            update_ops = opcounters.get("update", 0)
            delete_ops = opcounters.get("delete", 0)

            total_ops = insert_ops + query_ops + update_ops + delete_ops
            ops_metric = HealthMetric(
                name="total_operations",
                value=total_ops,
                unit="",
                metric_type=MetricType.OPERATIONS,
                status=HealthStatus.HEALTHY,
                message=f"Total operations: {total_ops:,}",
            )
            metrics.append(ops_metric)

            # WiredTiger cache if available
            wired_tiger = server_status.get("wiredTiger", {})
            if wired_tiger:
                cache = wired_tiger.get("cache", {})
                cache_used = cache.get("bytes currently in the cache", 0)
                cache_max = cache.get("maximum bytes configured", 0)

                if cache_max > 0:
                    cache_usage = (cache_used / cache_max) * 100
                    cache_metric = HealthMetric(
                        name="cache_usage_percent",
                        value=round(cache_usage, 2),
                        unit="%",
                        threshold_warning=75.0,
                        threshold_critical=90.0,
                        metric_type=MetricType.PERFORMANCE,
                    )
                    cache_metric.evaluate_status()
                    metrics.append(cache_metric)

        except Exception as e:
            error_metric = HealthMetric(
                name="performance_check_error",
                value=str(e),
                status=HealthStatus.WARNING,
                metric_type=MetricType.ERROR,
                message=f"Performance check failed: {e}",
            )
            metrics.append(error_metric)

        return metrics

    async def _check_storage_metrics(self) -> List[HealthMetric]:
        """Check MongoDB storage metrics"""
        metrics = []

        try:
            # Database statistics
            db_stats = await self.database.command("dbStats")

            # Database size
            data_size = db_stats.get("dataSize", 0)
            storage_size = db_stats.get("storageSize", 0)
            index_size = db_stats.get("indexSize", 0)

            data_size_mb = data_size / (1024 * 1024)
            storage_size_mb = storage_size / (1024 * 1024)
            index_size_mb = index_size / (1024 * 1024)

            data_metric = HealthMetric(
                name="database_data_size",
                value=round(data_size_mb, 2),
                unit="MB",
                metric_type=MetricType.STORAGE,
                status=HealthStatus.HEALTHY,
                message=f"Database data size: {data_size_mb:.2f} MB",
            )
            metrics.append(data_metric)

            index_metric = HealthMetric(
                name="database_index_size",
                value=round(index_size_mb, 2),
                unit="MB",
                metric_type=MetricType.STORAGE,
                status=HealthStatus.HEALTHY,
                message=f"Database index size: {index_size_mb:.2f} MB",
            )
            metrics.append(index_metric)

            # Collection count
            collections = db_stats.get("collections", 0)
            collection_metric = HealthMetric(
                name="collection_count",
                value=collections,
                unit="",
                metric_type=MetricType.STORAGE,
                status=HealthStatus.HEALTHY,
                message=f"Collections: {collections}",
            )
            metrics.append(collection_metric)

            # Index count
            indexes = db_stats.get("indexes", 0)
            index_count_metric = HealthMetric(
                name="index_count",
                value=indexes,
                unit="",
                metric_type=MetricType.STORAGE,
                status=HealthStatus.HEALTHY,
                message=f"Indexes: {indexes}",
            )
            metrics.append(index_count_metric)

        except Exception as e:
            error_metric = HealthMetric(
                name="storage_check_error",
                value=str(e),
                status=HealthStatus.WARNING,
                metric_type=MetricType.ERROR,
                message=f"Storage check failed: {e}",
            )
            metrics.append(error_metric)

        return metrics

    async def _check_operation_metrics(self) -> List[HealthMetric]:
        """Check MongoDB operation metrics"""
        metrics = []

        try:
            # Get current operations
            current_op = await self.database.command("currentOp")
            in_prog = current_op.get("inprog", [])

            # Count operations by type
            operation_types = {}
            long_running_ops = 0

            for op in in_prog:
                op_type = op.get("op", "unknown")
                operation_types[op_type] = operation_types.get(op_type, 0) + 1

                # Check for long-running operations (>30 seconds)
                secs_running = op.get("secs_running", 0)
                if secs_running > 30:
                    long_running_ops += 1

            # Active operations metric
            active_ops_metric = HealthMetric(
                name="active_operations",
                value=len(in_prog),
                unit="",
                threshold_warning=10,
                threshold_critical=25,
                metric_type=MetricType.OPERATIONS,
            )
            active_ops_metric.evaluate_status()
            metrics.append(active_ops_metric)

            # Long-running operations metric
            long_ops_metric = HealthMetric(
                name="long_running_operations",
                value=long_running_ops,
                unit="",
                threshold_warning=2,
                threshold_critical=5,
                metric_type=MetricType.OPERATIONS,
            )
            long_ops_metric.evaluate_status()
            metrics.append(long_ops_metric)

        except Exception as e:
            error_metric = HealthMetric(
                name="operation_check_error",
                value=str(e),
                status=HealthStatus.WARNING,
                metric_type=MetricType.ERROR,
                message=f"Operation check failed: {e}",
            )
            metrics.append(error_metric)

        return metrics

    async def _check_index_health(self) -> List[HealthMetric]:
        """Check MongoDB index health"""
        metrics = []

        try:
            # Get list of collections
            collections = await self.database.list_collection_names()

            total_indexes = 0
            total_size_mb = 0

            for collection_name in collections:
                try:
                    collection = self.database[collection_name]

                    # Get index statistics
                    index_stats = await collection.aggregate(
                        [{"$indexStats": {}}]
                    ).to_list(None)
                    total_indexes += len(index_stats)

                    # Get collection stats for index size
                    coll_stats = await self.database.command(
                        "collStats", collection_name
                    )
                    index_size = coll_stats.get("totalIndexSize", 0)
                    total_size_mb += index_size / (1024 * 1024)

                except Exception:
                    # Skip collections that can't be accessed
                    continue

            # Total indexes metric
            index_count_metric = HealthMetric(
                name="total_indexes_across_collections",
                value=total_indexes,
                unit="",
                metric_type=MetricType.STORAGE,
                status=HealthStatus.HEALTHY,
                message=f"Total indexes: {total_indexes}",
            )
            metrics.append(index_count_metric)

            # Index size metric
            index_size_metric = HealthMetric(
                name="total_index_size",
                value=round(total_size_mb, 2),
                unit="MB",
                threshold_warning=500.0,
                threshold_critical=1000.0,
                metric_type=MetricType.STORAGE,
            )
            index_size_metric.evaluate_status()
            metrics.append(index_size_metric)

        except Exception as e:
            error_metric = HealthMetric(
                name="index_check_error",
                value=str(e),
                status=HealthStatus.WARNING,
                metric_type=MetricType.ERROR,
                message=f"Index check failed: {e}",
            )
            metrics.append(error_metric)

        return metrics

    def _calculate_overall_status(self, metrics: List[HealthMetric]) -> HealthStatus:
        """Calculate overall health status from individual metrics"""
        if not metrics:
            return HealthStatus.UNKNOWN

        # Count status levels
        critical_count = sum(1 for m in metrics if m.status == HealthStatus.CRITICAL)
        warning_count = sum(1 for m in metrics if m.status == HealthStatus.WARNING)

        # Determine overall status
        if critical_count > 0:
            return HealthStatus.CRITICAL
        elif warning_count > 0:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY

    async def _check_alerts(self, result: HealthCheckResult) -> None:
        """Check if alerts should be triggered and call alert callbacks"""
        if result.overall_status in [HealthStatus.CRITICAL, HealthStatus.WARNING]:
            for callback in self.alert_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(result)
                    else:
                        callback(result)
                except Exception as e:
                    logger.error(f"❌ Alert callback failed: {e}")

    async def start_continuous_monitoring(self, interval_seconds: int = 60) -> None:
        """Start continuous health monitoring"""
        if self.monitoring_active:
            logger.warning("⚠️  Monitoring already active")
            return

        self.monitoring_active = True
        self._monitoring_task = asyncio.create_task(
            self._monitoring_loop(interval_seconds)
        )
        logger.info(
            f"🔍 Started continuous MongoDB monitoring (interval: {interval_seconds}s)"
        )

    async def stop_continuous_monitoring(self) -> None:
        """Stop continuous health monitoring"""
        self.monitoring_active = False

        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("🛑 Stopped continuous MongoDB monitoring")

    async def _monitoring_loop(self, interval_seconds: int) -> None:
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                await self.comprehensive_health_check()
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Monitoring loop error: {e}")
                await asyncio.sleep(interval_seconds)

    def get_performance_summary(self, minutes: int = 30) -> Dict[str, Any]:
        """Get performance summary for the last N minutes"""
        summary = {
            "period_minutes": minutes,
            "timestamp": datetime.utcnow().isoformat(),
            "averages": {},
            "trends": {},
            "operation_counts": dict(self.performance_tracker.operation_counts),
            "error_counts": dict(self.performance_tracker.error_counts),
        }

        # Calculate averages for key metrics
        key_metrics = [
            "ping_response_time",
            "active_connections",
            "memory_resident",
            "cache_usage_percent",
            "active_operations",
        ]

        for metric_name in key_metrics:
            avg_value = self.performance_tracker.get_average_metric(
                metric_name, minutes
            )
            if avg_value is not None:
                summary["averages"][metric_name] = round(avg_value, 2)

            trend = self.performance_tracker.get_trend(metric_name, minutes)
            if trend:
                summary["trends"][metric_name] = trend

        return summary

    async def export_health_report(
        self, include_history: bool = True
    ) -> Dict[str, Any]:
        """Export comprehensive health report"""
        report = {
            "report_timestamp": datetime.utcnow().isoformat(),
            "last_health_check": (
                self.last_health_check.to_dict() if self.last_health_check else None
            ),
            "monitoring_active": self.monitoring_active,
            "performance_summary": self.get_performance_summary(60),  # Last hour
        }

        if include_history:
            report["metrics_history"] = {
                metric_name: [
                    {
                        "value": m.value,
                        "status": m.status.value,
                        "timestamp": m.timestamp.isoformat(),
                    }
                    for m in history[-20:]  # Last 20 measurements
                ]
                for metric_name, history in self.performance_tracker.metrics_history.items()
            }

        return report
