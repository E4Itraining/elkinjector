"""Metrics data generator for ElkInjector."""

import random
from typing import Any

from faker import Faker

from elkinjector.config import MetricsGeneratorConfig
from elkinjector.generators.base import BaseGenerator


class MetricsGenerator(BaseGenerator):
    """Generator for system and application metrics."""

    # Metric definitions with value ranges and units
    METRIC_DEFINITIONS = {
        "cpu": {
            "metrics": [
                {"name": "cpu.usage.percent", "min": 0, "max": 100, "unit": "percent"},
                {"name": "cpu.user.percent", "min": 0, "max": 80, "unit": "percent"},
                {"name": "cpu.system.percent", "min": 0, "max": 40, "unit": "percent"},
                {"name": "cpu.idle.percent", "min": 0, "max": 100, "unit": "percent"},
                {"name": "cpu.load.1m", "min": 0, "max": 16, "unit": "load", "decimal": True},
                {"name": "cpu.load.5m", "min": 0, "max": 16, "unit": "load", "decimal": True},
                {"name": "cpu.load.15m", "min": 0, "max": 16, "unit": "load", "decimal": True},
            ]
        },
        "memory": {
            "metrics": [
                {"name": "memory.usage.percent", "min": 20, "max": 95, "unit": "percent"},
                {"name": "memory.used.bytes", "min": 1e9, "max": 32e9, "unit": "bytes"},
                {"name": "memory.free.bytes", "min": 1e8, "max": 16e9, "unit": "bytes"},
                {"name": "memory.cached.bytes", "min": 1e8, "max": 8e9, "unit": "bytes"},
                {"name": "memory.swap.used.bytes", "min": 0, "max": 4e9, "unit": "bytes"},
            ]
        },
        "disk": {
            "metrics": [
                {"name": "disk.usage.percent", "min": 10, "max": 90, "unit": "percent"},
                {"name": "disk.used.bytes", "min": 10e9, "max": 500e9, "unit": "bytes"},
                {"name": "disk.free.bytes", "min": 10e9, "max": 500e9, "unit": "bytes"},
                {"name": "disk.read.bytes_per_sec", "min": 0, "max": 500e6, "unit": "bytes/s"},
                {"name": "disk.write.bytes_per_sec", "min": 0, "max": 200e6, "unit": "bytes/s"},
                {"name": "disk.iops.read", "min": 0, "max": 10000, "unit": "ops/s"},
                {"name": "disk.iops.write", "min": 0, "max": 5000, "unit": "ops/s"},
            ]
        },
        "network": {
            "metrics": [
                {"name": "network.in.bytes_per_sec", "min": 0, "max": 1e9, "unit": "bytes/s"},
                {"name": "network.out.bytes_per_sec", "min": 0, "max": 1e9, "unit": "bytes/s"},
                {"name": "network.in.packets_per_sec", "min": 0, "max": 100000, "unit": "pps"},
                {"name": "network.out.packets_per_sec", "min": 0, "max": 100000, "unit": "pps"},
                {"name": "network.in.errors", "min": 0, "max": 100, "unit": "count"},
                {"name": "network.out.errors", "min": 0, "max": 100, "unit": "count"},
                {"name": "network.connections.active", "min": 0, "max": 10000, "unit": "count"},
            ]
        },
        "request_latency": {
            "metrics": [
                {"name": "http.request.duration.ms", "min": 1, "max": 5000, "unit": "ms"},
                {"name": "http.request.duration.p50", "min": 10, "max": 200, "unit": "ms"},
                {"name": "http.request.duration.p95", "min": 50, "max": 1000, "unit": "ms"},
                {"name": "http.request.duration.p99", "min": 100, "max": 3000, "unit": "ms"},
                {"name": "http.requests.total", "min": 100, "max": 100000, "unit": "count"},
                {"name": "http.requests.rate", "min": 10, "max": 10000, "unit": "req/s"},
                {"name": "http.errors.rate", "min": 0, "max": 100, "unit": "errors/s"},
            ]
        },
        "jvm": {
            "metrics": [
                {"name": "jvm.heap.used.bytes", "min": 100e6, "max": 8e9, "unit": "bytes"},
                {"name": "jvm.heap.max.bytes", "min": 1e9, "max": 16e9, "unit": "bytes"},
                {"name": "jvm.heap.usage.percent", "min": 10, "max": 95, "unit": "percent"},
                {"name": "jvm.gc.time.ms", "min": 0, "max": 1000, "unit": "ms"},
                {"name": "jvm.gc.count", "min": 0, "max": 100, "unit": "count"},
                {"name": "jvm.threads.count", "min": 10, "max": 500, "unit": "count"},
            ]
        },
        "database": {
            "metrics": [
                {"name": "db.connections.active", "min": 0, "max": 100, "unit": "count"},
                {"name": "db.connections.idle", "min": 0, "max": 50, "unit": "count"},
                {"name": "db.queries.rate", "min": 10, "max": 5000, "unit": "queries/s"},
                {"name": "db.query.duration.avg.ms", "min": 1, "max": 500, "unit": "ms"},
                {"name": "db.deadlocks", "min": 0, "max": 10, "unit": "count"},
                {"name": "db.cache.hit.ratio", "min": 0.5, "max": 1.0, "unit": "ratio", "decimal": True},
            ]
        },
    }

    def __init__(
        self,
        config: MetricsGeneratorConfig | None = None,
        index_prefix: str = "elkinjector",
    ):
        """Initialize the metrics generator.

        Args:
            config: Metrics generator configuration
            index_prefix: Prefix for the index name
        """
        self.config = config or MetricsGeneratorConfig()
        super().__init__(self.config.index_name, index_prefix)
        self.faker = Faker()

    def _generate_metric_value(self, metric_def: dict[str, Any]) -> float | int:
        """Generate a metric value based on definition."""
        min_val = metric_def["min"]
        max_val = metric_def["max"]

        if metric_def.get("decimal", False):
            return round(random.uniform(min_val, max_val), 2)
        else:
            return random.randint(int(min_val), int(max_val))

    def _get_metric_definition(self, metric_type: str) -> dict[str, Any]:
        """Get metric definitions for a metric type."""
        return self.METRIC_DEFINITIONS.get(metric_type, self.METRIC_DEFINITIONS["cpu"])

    def generate_one(self) -> dict[str, Any]:
        """Generate a single metrics document."""
        # Select a metric type
        metric_type = random.choice(self.config.metric_types)
        metric_def = self._get_metric_definition(metric_type)

        # Select a random metric from the type
        metric = random.choice(metric_def["metrics"])
        host = random.choice(self.config.hosts)

        # Generate the metric value
        value = self._generate_metric_value(metric)

        # Build the document
        document = {
            "@timestamp": self.utc_now(),
            "metric": {
                "name": metric["name"],
                "type": metric_type,
                "value": value,
                "unit": metric["unit"],
            },
            "host": {
                "name": host,
                "ip": self.faker.ipv4(),
                "os": {
                    "name": random.choice(["Linux", "Ubuntu", "CentOS", "Debian"]),
                    "version": f"{random.randint(18, 24)}.{random.randint(0, 10)}",
                },
            },
            "agent": {
                "name": "elkinjector-agent",
                "version": "1.0.0",
                "type": "metrics",
            },
        }

        # Add tags if enabled
        if self.config.include_tags:
            document["tags"] = self._generate_tags(metric_type, host)

        return document

    def _generate_tags(self, metric_type: str, host: str) -> dict[str, str]:
        """Generate tags for the metric."""
        tags = {
            "environment": random.choice(["production", "staging", "development"]),
            "region": random.choice(["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]),
            "datacenter": random.choice(["dc1", "dc2", "dc3"]),
            "cluster": f"cluster-{random.randint(1, 5)}",
        }

        # Add metric-specific tags
        if metric_type == "request_latency":
            tags["service"] = random.choice(["api", "web", "worker", "scheduler"])
            tags["endpoint"] = random.choice(["/api/users", "/api/orders", "/api/products", "/health"])

        if metric_type == "database":
            tags["database"] = random.choice(["postgresql", "mysql", "mongodb", "elasticsearch"])
            tags["instance"] = f"db-{random.randint(1, 3)}"

        if metric_type in ["cpu", "memory", "disk"]:
            tags["role"] = random.choice(["web", "api", "worker", "database", "cache"])

        return tags

    def generate_host_metrics(self, host: str | None = None) -> list[dict[str, Any]]:
        """Generate a complete set of metrics for a host.

        Args:
            host: Host name (random if not specified)

        Returns:
            List of metric documents for all metric types
        """
        host = host or random.choice(self.config.hosts)
        documents = []

        for metric_type in self.config.metric_types:
            metric_def = self._get_metric_definition(metric_type)

            for metric in metric_def["metrics"]:
                value = self._generate_metric_value(metric)

                document = {
                    "@timestamp": self.utc_now(),
                    "metric": {
                        "name": metric["name"],
                        "type": metric_type,
                        "value": value,
                        "unit": metric["unit"],
                    },
                    "host": {
                        "name": host,
                        "ip": self.faker.ipv4(),
                    },
                    "agent": {
                        "name": "elkinjector-agent",
                        "version": "1.0.0",
                        "type": "metrics",
                    },
                }

                if self.config.include_tags:
                    document["tags"] = self._generate_tags(metric_type, host)

                documents.append(document)

        return documents
