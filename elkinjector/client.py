"""Elasticsearch client wrapper for ElkInjector."""

from __future__ import annotations

import logging
from typing import Any

from elasticsearch import Elasticsearch, helpers

from elkinjector.config import ElasticsearchConfig

logger = logging.getLogger(__name__)


class ElasticsearchClient:
    """Wrapper around the Elasticsearch client with convenience methods."""

    def __init__(self, config: ElasticsearchConfig | None = None):
        """Initialize the Elasticsearch client.

        Args:
            config: Elasticsearch configuration
        """
        self.config = config or ElasticsearchConfig()
        self._client: Elasticsearch | None = None

    def connect(self) -> "ElasticsearchClient":
        """Connect to Elasticsearch.

        Returns:
            Self for method chaining
        """
        # Build connection kwargs
        kwargs: dict[str, Any] = {
            "hosts": [self.config.url],
            "request_timeout": self.config.timeout,
        }

        # Add authentication
        if self.config.api_key:
            kwargs["api_key"] = self.config.api_key
        elif self.config.username and self.config.password:
            kwargs["basic_auth"] = (self.config.username, self.config.password)

        # Add SSL configuration
        if self.config.scheme == "https":
            kwargs["verify_certs"] = self.config.verify_certs
            if self.config.ca_certs:
                kwargs["ca_certs"] = self.config.ca_certs

        self._client = Elasticsearch(**kwargs)
        logger.info(f"Connected to Elasticsearch at {self.config.url}")

        return self

    def disconnect(self) -> None:
        """Disconnect from Elasticsearch."""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("Disconnected from Elasticsearch")

    @property
    def client(self) -> Elasticsearch:
        """Get the underlying Elasticsearch client."""
        if self._client is None:
            raise RuntimeError("Not connected to Elasticsearch. Call connect() first.")
        return self._client

    def ping(self) -> bool:
        """Check if Elasticsearch is reachable.

        Returns:
            True if reachable, False otherwise
        """
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Ping failed: {e}")
            return False

    def info(self) -> dict[str, Any]:
        """Get Elasticsearch cluster info.

        Returns:
            Cluster information dictionary
        """
        return self.client.info()

    def health(self) -> dict[str, Any]:
        """Get cluster health status.

        Returns:
            Cluster health dictionary
        """
        return self.client.cluster.health()

    def index_document(
        self,
        index: str,
        document: dict[str, Any],
        doc_id: str | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        """Index a single document.

        Args:
            index: Index name
            document: Document to index
            doc_id: Optional document ID
            refresh: Whether to refresh the index after indexing

        Returns:
            Index response
        """
        kwargs: dict[str, Any] = {
            "index": index,
            "document": document,
        }
        if doc_id:
            kwargs["id"] = doc_id
        if refresh:
            kwargs["refresh"] = refresh

        return self.client.index(**kwargs)

    def bulk_index(
        self,
        actions: list[dict[str, Any]],
        chunk_size: int = 500,
        raise_on_error: bool = True,
        refresh: bool = False,
    ) -> tuple[int, list[Any]]:
        """Bulk index documents.

        Args:
            actions: List of bulk actions (documents with _index, _id, _source)
            chunk_size: Number of documents per chunk
            raise_on_error: Whether to raise on errors
            refresh: Whether to refresh indices after bulk

        Returns:
            Tuple of (success_count, error_list)
        """
        success, errors = helpers.bulk(
            self.client,
            actions,
            chunk_size=chunk_size,
            raise_on_error=raise_on_error,
            refresh=refresh,
        )
        return success, errors

    def streaming_bulk(
        self,
        actions,
        chunk_size: int = 500,
        raise_on_error: bool = True,
    ):
        """Stream bulk index documents.

        Args:
            actions: Iterator of bulk actions
            chunk_size: Number of documents per chunk
            raise_on_error: Whether to raise on errors

        Yields:
            Tuple of (success, info) for each document
        """
        yield from helpers.streaming_bulk(
            self.client,
            actions,
            chunk_size=chunk_size,
            raise_on_error=raise_on_error,
        )

    def create_index(
        self,
        index: str,
        mappings: dict[str, Any] | None = None,
        settings: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create an index.

        Args:
            index: Index name
            mappings: Index mappings
            settings: Index settings

        Returns:
            Create index response
        """
        body: dict[str, Any] = {}
        if mappings:
            body["mappings"] = mappings
        if settings:
            body["settings"] = settings

        return self.client.indices.create(index=index, body=body if body else None)

    def delete_index(self, index: str) -> dict[str, Any]:
        """Delete an index.

        Args:
            index: Index name

        Returns:
            Delete index response
        """
        return self.client.indices.delete(index=index)

    def index_exists(self, index: str) -> bool:
        """Check if an index exists.

        Args:
            index: Index name

        Returns:
            True if exists, False otherwise
        """
        return self.client.indices.exists(index=index)

    def count(self, index: str) -> int:
        """Get document count in an index.

        Args:
            index: Index name

        Returns:
            Document count
        """
        response = self.client.count(index=index)
        return response["count"]

    def refresh(self, index: str) -> dict[str, Any]:
        """Refresh an index.

        Args:
            index: Index name

        Returns:
            Refresh response
        """
        return self.client.indices.refresh(index=index)

    def __enter__(self) -> "ElasticsearchClient":
        """Context manager entry."""
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.disconnect()
