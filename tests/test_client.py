"""Tests for elkinjector.client module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from elkinjector.client import ElasticsearchClient
from elkinjector.config import ElasticsearchConfig


class TestElasticsearchClient:
    """Tests for ElasticsearchClient."""

    def test_init_default(self):
        client = ElasticsearchClient()
        assert client.config.host == "localhost"
        assert client._client is None

    def test_init_with_config(self, es_config):
        client = ElasticsearchClient(es_config)
        assert client.config == es_config

    def test_client_property_not_connected(self):
        client = ElasticsearchClient()
        with pytest.raises(RuntimeError, match="Not connected"):
            _ = client.client

    @patch("elkinjector.client.Elasticsearch")
    def test_connect(self, mock_es_class, es_config):
        mock_instance = MagicMock()
        mock_es_class.return_value = mock_instance

        client = ElasticsearchClient(es_config)
        result = client.connect()

        assert result is client
        assert client._client is mock_instance
        mock_es_class.assert_called_once()

    @patch("elkinjector.client.Elasticsearch")
    def test_connect_with_auth(self, mock_es_class):
        config = ElasticsearchConfig(
            host="es-host",
            port=9200,
            scheme="http",
            username="admin",
            password="secret",
        )
        mock_es_class.return_value = MagicMock()

        client = ElasticsearchClient(config)
        client.connect()

        call_kwargs = mock_es_class.call_args[1]
        assert call_kwargs["basic_auth"] == ("admin", "secret")

    @patch("elkinjector.client.Elasticsearch")
    def test_connect_with_api_key(self, mock_es_class):
        config = ElasticsearchConfig(
            host="es-host",
            scheme="http",
            api_key="my-api-key",
        )
        mock_es_class.return_value = MagicMock()

        client = ElasticsearchClient(config)
        client.connect()

        call_kwargs = mock_es_class.call_args[1]
        assert call_kwargs["api_key"] == "my-api-key"

    @patch("elkinjector.client.Elasticsearch")
    def test_connect_https_ssl(self, mock_es_class):
        config = ElasticsearchConfig(
            host="es-host",
            scheme="https",
            verify_certs=False,
            ca_certs="/path/to/ca.crt",
        )
        mock_es_class.return_value = MagicMock()

        client = ElasticsearchClient(config)
        client.connect()

        call_kwargs = mock_es_class.call_args[1]
        assert call_kwargs["verify_certs"] is False
        assert call_kwargs["ca_certs"] == "/path/to/ca.crt"

    @patch("elkinjector.client.Elasticsearch")
    def test_disconnect(self, mock_es_class):
        mock_instance = MagicMock()
        mock_es_class.return_value = mock_instance

        client = ElasticsearchClient()
        client.connect()
        client.disconnect()

        mock_instance.close.assert_called_once()
        assert client._client is None

    def test_disconnect_not_connected(self):
        client = ElasticsearchClient()
        client.disconnect()  # Should not raise

    @patch("elkinjector.client.Elasticsearch")
    def test_ping_success(self, mock_es_class):
        mock_instance = MagicMock()
        mock_instance.ping.return_value = True
        mock_es_class.return_value = mock_instance

        client = ElasticsearchClient()
        client.connect()
        assert client.ping() is True

    @patch("elkinjector.client.Elasticsearch")
    def test_ping_failure(self, mock_es_class):
        mock_instance = MagicMock()
        mock_instance.ping.side_effect = Exception("Connection refused")
        mock_es_class.return_value = mock_instance

        client = ElasticsearchClient()
        client.connect()
        assert client.ping() is False

    @patch("elkinjector.client.Elasticsearch")
    def test_info(self, mock_es_class):
        mock_instance = MagicMock()
        mock_instance.info.return_value = {"cluster_name": "test", "version": {"number": "8.12.0"}}
        mock_es_class.return_value = mock_instance

        client = ElasticsearchClient()
        client.connect()
        info = client.info()
        assert info["cluster_name"] == "test"

    @patch("elkinjector.client.Elasticsearch")
    def test_health(self, mock_es_class):
        mock_instance = MagicMock()
        mock_instance.cluster.health.return_value = {"status": "green"}
        mock_es_class.return_value = mock_instance

        client = ElasticsearchClient()
        client.connect()
        health = client.health()
        assert health["status"] == "green"

    @patch("elkinjector.client.Elasticsearch")
    def test_index_document(self, mock_es_class):
        mock_instance = MagicMock()
        mock_instance.index.return_value = {"result": "created"}
        mock_es_class.return_value = mock_instance

        client = ElasticsearchClient()
        client.connect()
        result = client.index_document("test-index", {"field": "value"})
        assert result["result"] == "created"

    @patch("elkinjector.client.Elasticsearch")
    def test_index_document_with_id(self, mock_es_class):
        mock_instance = MagicMock()
        mock_instance.index.return_value = {"result": "created"}
        mock_es_class.return_value = mock_instance

        client = ElasticsearchClient()
        client.connect()
        client.index_document("test-index", {"field": "value"}, doc_id="my-id")

        call_kwargs = mock_instance.index.call_args[1]
        assert call_kwargs["id"] == "my-id"

    @patch("elkinjector.client.helpers")
    @patch("elkinjector.client.Elasticsearch")
    def test_bulk_index(self, mock_es_class, mock_helpers):
        mock_instance = MagicMock()
        mock_es_class.return_value = mock_instance
        mock_helpers.bulk.return_value = (10, [])

        client = ElasticsearchClient()
        client.connect()
        success, errors = client.bulk_index([{"_index": "test", "_source": {}}])
        assert success == 10
        assert errors == []

    @patch("elkinjector.client.Elasticsearch")
    def test_create_index(self, mock_es_class):
        mock_instance = MagicMock()
        mock_instance.indices.create.return_value = {"acknowledged": True}
        mock_es_class.return_value = mock_instance

        client = ElasticsearchClient()
        client.connect()
        result = client.create_index("new-index")
        assert result["acknowledged"] is True

    @patch("elkinjector.client.Elasticsearch")
    def test_delete_index(self, mock_es_class):
        mock_instance = MagicMock()
        mock_instance.indices.delete.return_value = {"acknowledged": True}
        mock_es_class.return_value = mock_instance

        client = ElasticsearchClient()
        client.connect()
        result = client.delete_index("old-index")
        assert result["acknowledged"] is True

    @patch("elkinjector.client.Elasticsearch")
    def test_index_exists(self, mock_es_class):
        mock_instance = MagicMock()
        mock_instance.indices.exists.return_value = True
        mock_es_class.return_value = mock_instance

        client = ElasticsearchClient()
        client.connect()
        assert client.index_exists("test-index") is True

    @patch("elkinjector.client.Elasticsearch")
    def test_count(self, mock_es_class):
        mock_instance = MagicMock()
        mock_instance.count.return_value = {"count": 42}
        mock_es_class.return_value = mock_instance

        client = ElasticsearchClient()
        client.connect()
        assert client.count("test-index") == 42

    @patch("elkinjector.client.Elasticsearch")
    def test_context_manager(self, mock_es_class):
        mock_instance = MagicMock()
        mock_es_class.return_value = mock_instance

        with ElasticsearchClient() as client:
            assert client._client is not None

        mock_instance.close.assert_called_once()
