"""Tests for elkinjector.config module."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from elkinjector.config import (
    Config,
    ElasticsearchConfig,
    InjectionConfig,
    JsonGeneratorConfig,
    LogGeneratorConfig,
    MetricsGeneratorConfig,
)


class TestElasticsearchConfig:
    """Tests for ElasticsearchConfig dataclass."""

    def test_defaults(self):
        config = ElasticsearchConfig()
        assert config.host == "localhost"
        assert config.port == 9200
        assert config.scheme == "http"
        assert config.username is None
        assert config.password is None
        assert config.api_key is None
        assert config.ca_certs is None
        assert config.verify_certs is True
        assert config.timeout == 30

    def test_url_property(self):
        config = ElasticsearchConfig(host="myhost", port=9201, scheme="https")
        assert config.url == "https://myhost:9201"

    def test_url_default(self):
        config = ElasticsearchConfig()
        assert config.url == "http://localhost:9200"

    def test_custom_values(self):
        config = ElasticsearchConfig(
            host="es.example.com",
            port=9201,
            scheme="https",
            username="admin",
            password="secret",
            ca_certs="/path/to/ca.crt",
            verify_certs=False,
            timeout=60,
        )
        assert config.host == "es.example.com"
        assert config.port == 9201
        assert config.scheme == "https"
        assert config.username == "admin"
        assert config.password == "secret"
        assert config.ca_certs == "/path/to/ca.crt"
        assert config.verify_certs is False
        assert config.timeout == 60


class TestInjectionConfig:
    """Tests for InjectionConfig dataclass."""

    def test_defaults(self):
        config = InjectionConfig()
        assert config.batch_size == 1000
        assert config.interval_seconds == 1.0
        assert config.total_documents is None
        assert config.continuous is False
        assert config.index_prefix == "elkinjector"

    def test_custom_values(self):
        config = InjectionConfig(
            batch_size=500,
            interval_seconds=0.5,
            total_documents=10000,
            continuous=True,
            index_prefix="custom-prefix",
        )
        assert config.batch_size == 500
        assert config.interval_seconds == 0.5
        assert config.total_documents == 10000
        assert config.continuous is True
        assert config.index_prefix == "custom-prefix"


class TestLogGeneratorConfig:
    """Tests for LogGeneratorConfig dataclass."""

    def test_defaults(self):
        config = LogGeneratorConfig()
        assert config.enabled is True
        assert config.index_name == "logs"
        assert len(config.log_levels) == 5
        assert "INFO" in config.log_levels
        assert len(config.log_level_weights) == 5
        assert len(config.services) == 4
        assert config.include_stack_trace is True
        assert config.stack_trace_probability == 0.1


class TestMetricsGeneratorConfig:
    """Tests for MetricsGeneratorConfig dataclass."""

    def test_defaults(self):
        config = MetricsGeneratorConfig()
        assert config.enabled is True
        assert config.index_name == "metrics"
        assert "cpu" in config.metric_types
        assert "memory" in config.metric_types
        assert len(config.hosts) == 4
        assert config.include_tags is True


class TestJsonGeneratorConfig:
    """Tests for JsonGeneratorConfig dataclass."""

    def test_defaults(self):
        config = JsonGeneratorConfig()
        assert config.enabled is True
        assert config.index_name == "documents"
        assert config.template is None
        assert config.template_file is None


class TestConfig:
    """Tests for the main Config class."""

    def test_defaults(self):
        config = Config()
        assert isinstance(config.elasticsearch, ElasticsearchConfig)
        assert isinstance(config.injection, InjectionConfig)
        assert isinstance(config.logs, LogGeneratorConfig)
        assert isinstance(config.metrics, MetricsGeneratorConfig)
        assert isinstance(config.json, JsonGeneratorConfig)

    def test_from_dict(self):
        data = {
            "elasticsearch": {
                "host": "custom-host",
                "port": 9201,
                "scheme": "https",
            },
            "injection": {
                "batch_size": 500,
                "interval_seconds": 2.0,
            },
            "logs": {
                "enabled": False,
            },
        }
        config = Config.from_dict(data)
        assert config.elasticsearch.host == "custom-host"
        assert config.elasticsearch.port == 9201
        assert config.elasticsearch.scheme == "https"
        assert config.injection.batch_size == 500
        assert config.injection.interval_seconds == 2.0
        assert config.logs.enabled is False

    def test_from_dict_empty(self):
        config = Config.from_dict({})
        assert config.elasticsearch.host == "localhost"
        assert config.injection.batch_size == 1000

    def test_to_dict(self):
        config = Config()
        data = config.to_dict()
        assert "elasticsearch" in data
        assert "injection" in data
        assert "logs" in data
        assert "metrics" in data
        assert "json" in data
        assert data["elasticsearch"]["host"] == "localhost"
        assert data["injection"]["batch_size"] == 1000

    def test_from_yaml(self):
        yaml_content = {
            "elasticsearch": {
                "host": "yaml-host",
                "port": 9300,
            },
            "injection": {
                "batch_size": 200,
            },
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(yaml_content, f)
            tmp_path = f.name

        try:
            config = Config.from_yaml(tmp_path)
            assert config.elasticsearch.host == "yaml-host"
            assert config.elasticsearch.port == 9300
            assert config.injection.batch_size == 200
        finally:
            os.unlink(tmp_path)

    def test_from_yaml_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            Config.from_yaml("/nonexistent/path.yaml")

    def test_save_yaml(self):
        config = Config()
        config.elasticsearch.host = "saved-host"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            tmp_path = f.name

        try:
            config.save_yaml(tmp_path)
            loaded = Config.from_yaml(tmp_path)
            assert loaded.elasticsearch.host == "saved-host"
        finally:
            os.unlink(tmp_path)

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("ES_HOST", "env-host")
        monkeypatch.setenv("ES_PORT", "9201")
        monkeypatch.setenv("ES_SCHEME", "https")
        monkeypatch.setenv("ES_USERNAME", "admin")
        monkeypatch.setenv("ES_PASSWORD", "secret")
        monkeypatch.setenv("INJECTION_BATCH_SIZE", "500")
        monkeypatch.setenv("INJECTION_INTERVAL", "2.5")

        config = Config.from_env()
        assert config.elasticsearch.host == "env-host"
        assert config.elasticsearch.port == 9201
        assert config.elasticsearch.scheme == "https"
        assert config.elasticsearch.username == "admin"
        assert config.elasticsearch.password == "secret"
        assert config.injection.batch_size == 500
        assert config.injection.interval_seconds == 2.5

    def test_roundtrip_dict(self):
        """Test that config survives a to_dict/from_dict roundtrip."""
        original = Config()
        original.elasticsearch.host = "roundtrip-host"
        original.injection.batch_size = 999
        data = original.to_dict()
        restored = Config.from_dict(data)
        assert restored.elasticsearch.host == "roundtrip-host"
        assert restored.injection.batch_size == 999
