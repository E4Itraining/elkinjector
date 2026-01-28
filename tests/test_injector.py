"""Tests for elkinjector.injector module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from elkinjector.config import Config
from elkinjector.injector import DataInjector


class TestDataInjector:
    """Tests for DataInjector."""

    def test_init_default(self):
        injector = DataInjector()
        assert injector.config is not None
        assert "logs" in injector.generators
        assert "metrics" in injector.generators
        assert "json" in injector.generators

    def test_init_with_config(self, full_config):
        injector = DataInjector(full_config)
        assert injector.config == full_config
        assert "logs" in injector.generators
        assert "metrics" in injector.generators
        assert "json" in injector.generators

    def test_generators_disabled(self):
        config = Config()
        config.logs.enabled = False
        config.metrics.enabled = False
        config.json.enabled = False
        injector = DataInjector(config)
        assert len(injector.generators) == 0

    def test_partial_generators(self):
        config = Config()
        config.logs.enabled = True
        config.metrics.enabled = False
        config.json.enabled = False
        injector = DataInjector(config)
        assert "logs" in injector.generators
        assert "metrics" not in injector.generators
        assert "json" not in injector.generators

    def test_stats_initial(self):
        injector = DataInjector()
        stats = injector.stats
        assert stats["total_documents"] == 0
        assert stats["total_errors"] == 0
        assert stats["start_time"] is None
        assert stats["end_time"] is None

    def test_stats_is_copy(self):
        injector = DataInjector()
        stats = injector.stats
        stats["total_documents"] = 999
        assert injector.stats["total_documents"] == 0

    @patch("elkinjector.client.Elasticsearch")
    def test_connect(self, mock_es_class):
        mock_instance = MagicMock()
        mock_instance.ping.return_value = True
        mock_instance.info.return_value = {
            "cluster_name": "test",
            "version": {"number": "8.12.0"},
        }
        mock_es_class.return_value = mock_instance

        injector = DataInjector()
        result = injector.connect()
        assert result is injector

    @patch("elkinjector.client.Elasticsearch")
    def test_connect_ping_fail(self, mock_es_class):
        mock_instance = MagicMock()
        mock_instance.ping.return_value = False
        mock_es_class.return_value = mock_instance

        injector = DataInjector()
        with pytest.raises(ConnectionError):
            injector.connect()

    def test_inject_batch_unknown_generator(self):
        injector = DataInjector()
        injector.client = MagicMock()
        injector.client._client = MagicMock()
        with pytest.raises(ValueError, match="Unknown generator"):
            injector.inject_batch("nonexistent")

    @patch("elkinjector.client.helpers")
    @patch("elkinjector.client.Elasticsearch")
    def test_inject_batch(self, mock_es_class, mock_helpers):
        mock_instance = MagicMock()
        mock_es_class.return_value = mock_instance
        mock_helpers.bulk.return_value = (10, [])

        config = Config()
        config.logs.enabled = True
        config.metrics.enabled = False
        config.json.enabled = False
        config.injection.batch_size = 10

        injector = DataInjector(config)
        injector.client._client = mock_instance

        success, errors = injector.inject_batch("logs", batch_size=10)
        assert success == 10
        assert errors == 0

    @patch("elkinjector.client.helpers")
    @patch("elkinjector.client.Elasticsearch")
    def test_inject_all(self, mock_es_class, mock_helpers):
        mock_instance = MagicMock()
        mock_es_class.return_value = mock_instance
        mock_helpers.bulk.return_value = (5, [])

        config = Config()
        config.logs.enabled = True
        config.metrics.enabled = True
        config.json.enabled = False
        config.injection.batch_size = 5

        injector = DataInjector(config)
        injector.client._client = mock_instance

        results = injector.inject_all(batch_size=5)
        assert "logs" in results
        assert "metrics" in results
        assert results["logs"] == (5, 0)
        assert results["metrics"] == (5, 0)

    @patch("elkinjector.client.helpers")
    @patch("elkinjector.client.Elasticsearch")
    def test_inject_batch_with_errors(self, mock_es_class, mock_helpers):
        mock_instance = MagicMock()
        mock_es_class.return_value = mock_instance
        mock_helpers.bulk.return_value = (8, [{"error": "doc1"}, {"error": "doc2"}])

        config = Config()
        config.logs.enabled = True
        config.metrics.enabled = False
        config.json.enabled = False

        injector = DataInjector(config)
        injector.client._client = mock_instance

        success, errors = injector.inject_batch("logs", batch_size=10)
        assert success == 8
        assert errors == 2

    @patch("elkinjector.client.helpers")
    @patch("elkinjector.client.Elasticsearch")
    def test_inject_batch_exception(self, mock_es_class, mock_helpers):
        mock_instance = MagicMock()
        mock_es_class.return_value = mock_instance
        mock_helpers.bulk.side_effect = Exception("Connection lost")

        config = Config()
        config.logs.enabled = True
        config.metrics.enabled = False
        config.json.enabled = False

        injector = DataInjector(config)
        injector.client._client = mock_instance

        success, errors = injector.inject_batch("logs", batch_size=10)
        assert success == 0
        assert errors == 10

    def test_stop(self):
        injector = DataInjector()
        injector._running = True
        injector.stop()
        assert injector._running is False

    @patch("elkinjector.client.helpers")
    @patch("elkinjector.client.Elasticsearch")
    def test_run_with_total(self, mock_es_class, mock_helpers):
        mock_instance = MagicMock()
        mock_es_class.return_value = mock_instance
        mock_helpers.bulk.return_value = (100, [])

        config = Config()
        config.logs.enabled = True
        config.metrics.enabled = False
        config.json.enabled = False
        config.injection.batch_size = 100

        injector = DataInjector(config)
        injector.client._client = mock_instance

        stats = injector.run(total_documents=100, interval=0.01)
        assert stats["total_documents"] >= 100
        assert stats["start_time"] is not None
        assert stats["end_time"] is not None

    @patch("elkinjector.client.helpers")
    @patch("elkinjector.client.Elasticsearch")
    def test_run_no_generators(self, mock_es_class, mock_helpers):
        config = Config()
        config.logs.enabled = False
        config.metrics.enabled = False
        config.json.enabled = False

        injector = DataInjector(config)
        stats = injector.run()
        assert stats["total_documents"] == 0

    @patch("elkinjector.client.Elasticsearch")
    def test_context_manager(self, mock_es_class):
        mock_instance = MagicMock()
        mock_instance.ping.return_value = True
        mock_instance.info.return_value = {
            "cluster_name": "test",
            "version": {"number": "8.12.0"},
        }
        mock_es_class.return_value = mock_instance

        with DataInjector() as injector:
            assert injector is not None

        mock_instance.close.assert_called_once()

    @patch("elkinjector.client.helpers")
    @patch("elkinjector.client.Elasticsearch")
    def test_run_with_callback(self, mock_es_class, mock_helpers):
        mock_instance = MagicMock()
        mock_es_class.return_value = mock_instance
        mock_helpers.bulk.return_value = (10, [])

        config = Config()
        config.logs.enabled = True
        config.metrics.enabled = False
        config.json.enabled = False
        config.injection.batch_size = 10

        injector = DataInjector(config)
        injector.client._client = mock_instance

        callback_calls = []
        stats = injector.run(
            total_documents=10,
            interval=0.01,
            callback=lambda s: callback_calls.append(s),
        )

        assert len(callback_calls) > 0
        assert "generator" in callback_calls[0]
        assert "success" in callback_calls[0]
