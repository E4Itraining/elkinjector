"""Shared test fixtures for ElkInjector tests."""

from __future__ import annotations

import pytest

from elkinjector.config import (
    Config,
    ElasticsearchConfig,
    InjectionConfig,
    JsonGeneratorConfig,
    LogGeneratorConfig,
    MetricsGeneratorConfig,
)


@pytest.fixture
def es_config():
    """Default Elasticsearch configuration for tests."""
    return ElasticsearchConfig(
        host="localhost",
        port=9200,
        scheme="http",
    )


@pytest.fixture
def injection_config():
    """Default injection configuration for tests."""
    return InjectionConfig(
        batch_size=10,
        interval_seconds=0.1,
        total_documents=100,
        index_prefix="test-elkinjector",
    )


@pytest.fixture
def log_config():
    """Default log generator configuration for tests."""
    return LogGeneratorConfig(
        enabled=True,
        index_name="test-logs",
        log_levels=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        log_level_weights=[10, 50, 25, 10, 5],
        services=["test-service-a", "test-service-b"],
        include_stack_trace=True,
        stack_trace_probability=0.5,
    )


@pytest.fixture
def metrics_config():
    """Default metrics generator configuration for tests."""
    return MetricsGeneratorConfig(
        enabled=True,
        index_name="test-metrics",
        metric_types=["cpu", "memory", "disk"],
        hosts=["test-host-01", "test-host-02"],
        include_tags=True,
    )


@pytest.fixture
def json_config():
    """Default JSON generator configuration for tests."""
    return JsonGeneratorConfig(
        enabled=True,
        index_name="test-documents",
        template={
            "@timestamp": "{{timestamp}}",
            "user_id": "{{uuid_short}}",
            "action": "{{choice:login,logout}}",
            "value": "{{int:1:100}}",
        },
    )


@pytest.fixture
def full_config(es_config, injection_config, log_config, metrics_config, json_config):
    """Full configuration for tests."""
    return Config(
        elasticsearch=es_config,
        injection=injection_config,
        logs=log_config,
        metrics=metrics_config,
        json=json_config,
    )
