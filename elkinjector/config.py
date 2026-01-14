"""Configuration management for ElkInjector."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ElasticsearchConfig:
    """Elasticsearch connection configuration."""

    host: str = "localhost"
    port: int = 9200
    scheme: str = "http"
    username: str | None = None
    password: str | None = None
    api_key: str | None = None
    ca_certs: str | None = None
    verify_certs: bool = True
    timeout: int = 30

    @property
    def url(self) -> str:
        """Get the full Elasticsearch URL."""
        return f"{self.scheme}://{self.host}:{self.port}"


@dataclass
class InjectionConfig:
    """Data injection configuration."""

    batch_size: int = 1000
    interval_seconds: float = 1.0
    total_documents: int | None = None
    continuous: bool = False
    index_prefix: str = "elkinjector"


@dataclass
class LogGeneratorConfig:
    """Log generator configuration."""

    enabled: bool = True
    index_name: str = "logs"
    log_levels: list[str] = field(
        default_factory=lambda: ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    )
    log_level_weights: list[int] = field(default_factory=lambda: [10, 50, 25, 10, 5])
    services: list[str] = field(
        default_factory=lambda: ["api-gateway", "auth-service", "user-service", "payment-service"]
    )
    include_stack_trace: bool = True
    stack_trace_probability: float = 0.1


@dataclass
class MetricsGeneratorConfig:
    """Metrics generator configuration."""

    enabled: bool = True
    index_name: str = "metrics"
    metric_types: list[str] = field(
        default_factory=lambda: ["cpu", "memory", "disk", "network", "request_latency"]
    )
    hosts: list[str] = field(
        default_factory=lambda: ["server-01", "server-02", "server-03", "server-04"]
    )
    include_tags: bool = True


@dataclass
class JsonGeneratorConfig:
    """JSON document generator configuration."""

    enabled: bool = True
    index_name: str = "documents"
    template: dict[str, Any] | None = None
    template_file: str | None = None


@dataclass
class Config:
    """Main configuration class."""

    elasticsearch: ElasticsearchConfig = field(default_factory=ElasticsearchConfig)
    injection: InjectionConfig = field(default_factory=InjectionConfig)
    logs: LogGeneratorConfig = field(default_factory=LogGeneratorConfig)
    metrics: MetricsGeneratorConfig = field(default_factory=MetricsGeneratorConfig)
    json: JsonGeneratorConfig = field(default_factory=JsonGeneratorConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Config":
        """Load configuration from a YAML file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        """Create configuration from a dictionary."""
        config = cls()

        if "elasticsearch" in data:
            config.elasticsearch = ElasticsearchConfig(**data["elasticsearch"])

        if "injection" in data:
            config.injection = InjectionConfig(**data["injection"])

        if "logs" in data:
            config.logs = LogGeneratorConfig(**data["logs"])

        if "metrics" in data:
            config.metrics = MetricsGeneratorConfig(**data["metrics"])

        if "json" in data:
            config.json = JsonGeneratorConfig(**data["json"])

        return config

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        config = cls()

        # Elasticsearch config from env
        config.elasticsearch.host = os.getenv("ES_HOST", config.elasticsearch.host)
        config.elasticsearch.port = int(os.getenv("ES_PORT", config.elasticsearch.port))
        config.elasticsearch.scheme = os.getenv("ES_SCHEME", config.elasticsearch.scheme)
        config.elasticsearch.username = os.getenv("ES_USERNAME", config.elasticsearch.username)
        config.elasticsearch.password = os.getenv("ES_PASSWORD", config.elasticsearch.password)
        config.elasticsearch.api_key = os.getenv("ES_API_KEY", config.elasticsearch.api_key)

        # Injection config from env
        config.injection.batch_size = int(
            os.getenv("INJECTION_BATCH_SIZE", config.injection.batch_size)
        )
        config.injection.interval_seconds = float(
            os.getenv("INJECTION_INTERVAL", config.injection.interval_seconds)
        )

        return config

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to a dictionary."""
        return {
            "elasticsearch": {
                "host": self.elasticsearch.host,
                "port": self.elasticsearch.port,
                "scheme": self.elasticsearch.scheme,
                "username": self.elasticsearch.username,
                "password": self.elasticsearch.password,
                "api_key": self.elasticsearch.api_key,
                "ca_certs": self.elasticsearch.ca_certs,
                "verify_certs": self.elasticsearch.verify_certs,
                "timeout": self.elasticsearch.timeout,
            },
            "injection": {
                "batch_size": self.injection.batch_size,
                "interval_seconds": self.injection.interval_seconds,
                "total_documents": self.injection.total_documents,
                "continuous": self.injection.continuous,
                "index_prefix": self.injection.index_prefix,
            },
            "logs": {
                "enabled": self.logs.enabled,
                "index_name": self.logs.index_name,
                "log_levels": self.logs.log_levels,
                "services": self.logs.services,
            },
            "metrics": {
                "enabled": self.metrics.enabled,
                "index_name": self.metrics.index_name,
                "metric_types": self.metrics.metric_types,
                "hosts": self.metrics.hosts,
            },
            "json": {
                "enabled": self.json.enabled,
                "index_name": self.json.index_name,
                "template": self.json.template,
            },
        }

    def save_yaml(self, path: str | Path) -> None:
        """Save configuration to a YAML file."""
        path = Path(path)
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)
