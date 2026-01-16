"""Base generator class for data generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Iterator
import uuid


class BaseGenerator(ABC):
    """Abstract base class for all data generators."""

    def __init__(self, index_name: str, index_prefix: str = "elkinjector"):
        """Initialize the generator.

        Args:
            index_name: Name of the index (will be combined with prefix)
            index_prefix: Prefix for the index name
        """
        self.index_name = index_name
        self.index_prefix = index_prefix

    @property
    def full_index_name(self) -> str:
        """Get the full index name with prefix."""
        return f"{self.index_prefix}-{self.index_name}"

    @abstractmethod
    def generate_one(self) -> dict[str, Any]:
        """Generate a single document.

        Returns:
            A dictionary representing the document
        """
        pass

    def generate_batch(self, size: int) -> list[dict[str, Any]]:
        """Generate a batch of documents.

        Args:
            size: Number of documents to generate

        Returns:
            List of document dictionaries
        """
        return [self.generate_one() for _ in range(size)]

    def generate_stream(self, count: int | None = None) -> Iterator[dict[str, Any]]:
        """Generate a stream of documents.

        Args:
            count: Number of documents to generate (None for infinite)

        Yields:
            Document dictionaries
        """
        generated = 0
        while count is None or generated < count:
            yield self.generate_one()
            generated += 1

    @staticmethod
    def utc_now() -> str:
        """Get current UTC timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def generate_id() -> str:
        """Generate a unique document ID."""
        return str(uuid.uuid4())

    def prepare_bulk_action(self, document: dict[str, Any]) -> dict[str, Any]:
        """Prepare a document for bulk indexing.

        Args:
            document: The document to prepare

        Returns:
            Document with bulk action metadata
        """
        doc_id = document.pop("_id", self.generate_id())
        return {
            "_index": self.full_index_name,
            "_id": doc_id,
            "_source": document,
        }

    def prepare_bulk_batch(self, documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Prepare a batch of documents for bulk indexing.

        Args:
            documents: List of documents to prepare

        Returns:
            List of documents with bulk action metadata
        """
        return [self.prepare_bulk_action(doc) for doc in documents]
