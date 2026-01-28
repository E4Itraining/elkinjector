"""Tests for elkinjector.generators module."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from elkinjector.config import JsonGeneratorConfig, LogGeneratorConfig, MetricsGeneratorConfig
from elkinjector.generators import JsonGenerator, LogGenerator, MetricsGenerator
from elkinjector.generators.base import BaseGenerator


class TestBaseGenerator:
    """Tests for BaseGenerator abstract class."""

    def test_cannot_instantiate(self):
        """BaseGenerator is abstract and cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseGenerator("test", "prefix")

    def test_full_index_name(self, log_config):
        gen = LogGenerator(log_config, index_prefix="myprefix")
        assert gen.full_index_name == "myprefix-test-logs"

    def test_utc_now_format(self):
        ts = BaseGenerator.utc_now()
        assert "T" in ts
        assert "+" in ts or "Z" in ts

    def test_generate_id(self):
        id1 = BaseGenerator.generate_id()
        id2 = BaseGenerator.generate_id()
        assert id1 != id2
        assert len(id1) == 36  # UUID format


class TestLogGenerator:
    """Tests for LogGenerator."""

    def test_init_default(self):
        gen = LogGenerator()
        assert gen.full_index_name == "elkinjector-logs"
        assert gen.config.enabled is True

    def test_init_with_config(self, log_config):
        gen = LogGenerator(log_config, index_prefix="test")
        assert gen.full_index_name == "test-test-logs"

    def test_generate_one(self, log_config):
        gen = LogGenerator(log_config)
        doc = gen.generate_one()

        assert "@timestamp" in doc
        assert "level" in doc
        assert doc["level"] in log_config.log_levels
        assert "message" in doc
        assert "service" in doc
        assert "name" in doc["service"]
        assert "host" in doc
        assert "name" in doc["host"]
        assert "ip" in doc["host"]
        assert "process" in doc
        assert "trace" in doc

    def test_generate_batch(self, log_config):
        gen = LogGenerator(log_config)
        batch = gen.generate_batch(50)
        assert len(batch) == 50
        for doc in batch:
            assert "@timestamp" in doc
            assert "level" in doc

    def test_generate_stream(self, log_config):
        gen = LogGenerator(log_config)
        docs = list(gen.generate_stream(count=5))
        assert len(docs) == 5

    def test_prepare_bulk_action(self, log_config):
        gen = LogGenerator(log_config)
        doc = gen.generate_one()
        action = gen.prepare_bulk_action(doc)

        assert "_index" in action
        assert "_id" in action
        assert "_source" in action
        assert action["_index"] == gen.full_index_name

    def test_prepare_bulk_batch(self, log_config):
        gen = LogGenerator(log_config)
        docs = gen.generate_batch(5)
        actions = gen.prepare_bulk_batch(docs)

        assert len(actions) == 5
        for action in actions:
            assert "_index" in action
            assert "_id" in action
            assert "_source" in action

    def test_log_levels_distribution(self, log_config):
        """Verify log levels are generated according to weights."""
        gen = LogGenerator(log_config)
        levels = [gen.generate_one()["level"] for _ in range(1000)]

        # All levels should appear
        for level in log_config.log_levels:
            assert level in levels

    def test_stack_trace_for_errors(self):
        """Verify stack traces are generated for error/critical logs."""
        config = LogGeneratorConfig(
            include_stack_trace=True,
            stack_trace_probability=1.0,  # Always generate
            log_levels=["ERROR"],
            log_level_weights=[100],
        )
        gen = LogGenerator(config)
        doc = gen.generate_one()
        assert doc["level"] == "ERROR"
        assert "error" in doc
        assert "stack_trace" in doc["error"]
        assert "Traceback" in doc["error"]["stack_trace"]

    def test_no_stack_trace_when_disabled(self):
        config = LogGeneratorConfig(
            include_stack_trace=False,
            log_levels=["ERROR"],
            log_level_weights=[100],
        )
        gen = LogGenerator(config)
        doc = gen.generate_one()
        assert "error" not in doc


class TestMetricsGenerator:
    """Tests for MetricsGenerator."""

    def test_init_default(self):
        gen = MetricsGenerator()
        assert gen.full_index_name == "elkinjector-metrics"

    def test_init_with_config(self, metrics_config):
        gen = MetricsGenerator(metrics_config, index_prefix="test")
        assert gen.full_index_name == "test-test-metrics"

    def test_generate_one(self, metrics_config):
        gen = MetricsGenerator(metrics_config)
        doc = gen.generate_one()

        assert "@timestamp" in doc
        assert "metric" in doc
        assert "name" in doc["metric"]
        assert "type" in doc["metric"]
        assert "value" in doc["metric"]
        assert "unit" in doc["metric"]
        assert "host" in doc
        assert "agent" in doc

    def test_metric_types(self, metrics_config):
        gen = MetricsGenerator(metrics_config)
        types_seen = set()
        for _ in range(200):
            doc = gen.generate_one()
            types_seen.add(doc["metric"]["type"])

        # Should see all configured types
        for mt in metrics_config.metric_types:
            assert mt in types_seen

    def test_generate_batch(self, metrics_config):
        gen = MetricsGenerator(metrics_config)
        batch = gen.generate_batch(20)
        assert len(batch) == 20

    def test_tags_included(self, metrics_config):
        gen = MetricsGenerator(metrics_config)
        doc = gen.generate_one()
        assert "tags" in doc
        assert "environment" in doc["tags"]
        assert "region" in doc["tags"]

    def test_tags_excluded(self):
        config = MetricsGeneratorConfig(include_tags=False)
        gen = MetricsGenerator(config)
        doc = gen.generate_one()
        assert "tags" not in doc

    def test_generate_host_metrics(self, metrics_config):
        gen = MetricsGenerator(metrics_config)
        docs = gen.generate_host_metrics(host="my-server")
        assert len(docs) > 0
        for doc in docs:
            assert doc["host"]["name"] == "my-server"

    def test_metric_value_ranges(self):
        gen = MetricsGenerator()
        for _ in range(100):
            doc = gen.generate_one()
            value = doc["metric"]["value"]
            assert isinstance(value, (int, float))


class TestJsonGenerator:
    """Tests for JsonGenerator."""

    def test_init_default(self):
        gen = JsonGenerator()
        assert gen.full_index_name == "elkinjector-documents"
        assert gen.template == JsonGenerator.DEFAULT_TEMPLATE

    def test_init_with_template(self, json_config):
        gen = JsonGenerator(json_config)
        doc = gen.generate_one()
        assert "@timestamp" in doc
        assert "user_id" in doc
        assert "action" in doc
        assert doc["action"] in ["login", "logout"]
        assert "value" in doc
        assert isinstance(doc["value"], int)
        assert 1 <= doc["value"] <= 100

    def test_placeholder_timestamp(self):
        gen = JsonGenerator()
        gen.set_template({"ts": "{{timestamp}}"})
        doc = gen.generate_one()
        assert "T" in doc["ts"]

    def test_placeholder_uuid(self):
        gen = JsonGenerator()
        gen.set_template({"id": "{{uuid}}"})
        doc = gen.generate_one()
        assert len(doc["id"]) == 36

    def test_placeholder_uuid_short(self):
        gen = JsonGenerator()
        gen.set_template({"id": "{{uuid_short}}"})
        doc = gen.generate_one()
        assert len(doc["id"]) == 8

    def test_placeholder_int(self):
        gen = JsonGenerator()
        gen.set_template({"val": "{{int:10:20}}"})
        doc = gen.generate_one()
        assert isinstance(doc["val"], int)
        assert 10 <= doc["val"] <= 20

    def test_placeholder_float(self):
        gen = JsonGenerator()
        gen.set_template({"val": "{{float:1.0:5.0}}"})
        doc = gen.generate_one()
        assert isinstance(doc["val"], float)
        assert 1.0 <= doc["val"] <= 5.0

    def test_placeholder_choice(self):
        gen = JsonGenerator()
        gen.set_template({"color": "{{choice:red,green,blue}}"})
        doc = gen.generate_one()
        assert doc["color"] in ["red", "green", "blue"]

    def test_placeholder_name(self):
        gen = JsonGenerator()
        gen.set_template({"name": "{{name}}"})
        doc = gen.generate_one()
        assert isinstance(doc["name"], str)
        assert len(doc["name"]) > 0

    def test_placeholder_email(self):
        gen = JsonGenerator()
        gen.set_template({"email": "{{email}}"})
        doc = gen.generate_one()
        assert "@" in doc["email"]

    def test_placeholder_ipv4(self):
        gen = JsonGenerator()
        gen.set_template({"ip": "{{ipv4}}"})
        doc = gen.generate_one()
        parts = doc["ip"].split(".")
        assert len(parts) == 4

    def test_placeholder_bool(self):
        gen = JsonGenerator()
        gen.set_template({"flag": "{{bool}}"})
        doc = gen.generate_one()
        assert isinstance(doc["flag"], bool)

    def test_placeholder_latitude_longitude(self):
        gen = JsonGenerator()
        gen.set_template({"lat": "{{latitude}}", "lon": "{{longitude}}"})
        doc = gen.generate_one()
        assert isinstance(doc["lat"], float)
        assert isinstance(doc["lon"], float)

    def test_nested_template(self):
        gen = JsonGenerator()
        gen.set_template({
            "user": {
                "name": "{{name}}",
                "contact": {
                    "email": "{{email}}",
                    "phone": "{{phone}}",
                },
            },
        })
        doc = gen.generate_one()
        assert "user" in doc
        assert "name" in doc["user"]
        assert "contact" in doc["user"]
        assert "email" in doc["user"]["contact"]

    def test_list_in_template(self):
        gen = JsonGenerator()
        gen.set_template({
            "tags": ["{{word}}", "{{word}}", "{{word}}"],
        })
        doc = gen.generate_one()
        assert len(doc["tags"]) == 3

    def test_mixed_text_and_placeholder(self):
        gen = JsonGenerator()
        gen.set_template({"msg": "Hello {{name}}, your IP is {{ipv4}}"})
        doc = gen.generate_one()
        assert "Hello" in doc["msg"]
        assert "your IP is" in doc["msg"]

    def test_unknown_placeholder(self):
        gen = JsonGenerator()
        gen.set_template({"val": "{{nonexistent}}"})
        doc = gen.generate_one()
        assert "unknown" in doc["val"]

    def test_load_template_from_file(self):
        template = {"key": "{{uuid}}", "ts": "{{timestamp}}"}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(template, f)
            tmp_path = f.name

        try:
            gen = JsonGenerator()
            gen.load_template_from_file(tmp_path)
            doc = gen.generate_one()
            assert "key" in doc
            assert "ts" in doc
        finally:
            os.unlink(tmp_path)

    def test_load_template_file_not_found(self):
        gen = JsonGenerator()
        with pytest.raises(FileNotFoundError):
            gen.load_template_from_file("/nonexistent/template.json")

    def test_get_available_placeholders(self):
        placeholders = JsonGenerator.get_available_placeholders()
        assert isinstance(placeholders, list)
        assert "timestamp" in placeholders
        assert "uuid" in placeholders
        assert "email" in placeholders
        assert "ipv4" in placeholders
        assert "bool" in placeholders
        assert len(placeholders) >= 20

    def test_generate_batch(self, json_config):
        gen = JsonGenerator(json_config)
        batch = gen.generate_batch(10)
        assert len(batch) == 10

    def test_set_template(self):
        gen = JsonGenerator()
        new_template = {"field": "{{word}}"}
        gen.set_template(new_template)
        assert gen.template == new_template
        doc = gen.generate_one()
        assert "field" in doc
