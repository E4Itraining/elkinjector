"""Main data injector for ElkInjector."""

import logging
import signal
import sys
import time
from typing import Any, Callable

from elkinjector.client import ElasticsearchClient
from elkinjector.config import Config
from elkinjector.generators import JsonGenerator, LogGenerator, MetricsGenerator
from elkinjector.generators.base import BaseGenerator

logger = logging.getLogger(__name__)


class DataInjector:
    """Main class for injecting data into Elasticsearch."""

    def __init__(self, config: Config | None = None):
        """Initialize the data injector.

        Args:
            config: Configuration object
        """
        self.config = config or Config()
        self.client = ElasticsearchClient(self.config.elasticsearch)
        self.generators: dict[str, BaseGenerator] = {}
        self._running = False
        self._stats = {
            "total_documents": 0,
            "total_errors": 0,
            "start_time": None,
            "end_time": None,
        }

        # Setup generators based on config
        self._setup_generators()

    def _setup_generators(self) -> None:
        """Setup enabled generators based on configuration."""
        prefix = self.config.injection.index_prefix

        if self.config.logs.enabled:
            self.generators["logs"] = LogGenerator(self.config.logs, prefix)
            logger.info(f"Log generator enabled -> {self.generators['logs'].full_index_name}")

        if self.config.metrics.enabled:
            self.generators["metrics"] = MetricsGenerator(self.config.metrics, prefix)
            logger.info(
                f"Metrics generator enabled -> {self.generators['metrics'].full_index_name}"
            )

        if self.config.json.enabled:
            self.generators["json"] = JsonGenerator(self.config.json, prefix)
            logger.info(f"JSON generator enabled -> {self.generators['json'].full_index_name}")

    def connect(self) -> "DataInjector":
        """Connect to Elasticsearch.

        Returns:
            Self for method chaining
        """
        self.client.connect()

        # Verify connection
        if not self.client.ping():
            raise ConnectionError("Failed to connect to Elasticsearch")

        info = self.client.info()
        logger.info(
            f"Connected to Elasticsearch cluster: {info['cluster_name']} "
            f"(version {info['version']['number']})"
        )

        return self

    def disconnect(self) -> None:
        """Disconnect from Elasticsearch."""
        self.client.disconnect()

    def inject_batch(
        self,
        generator_name: str,
        batch_size: int | None = None,
        refresh: bool = False,
    ) -> tuple[int, int]:
        """Inject a batch of documents using a specific generator.

        Args:
            generator_name: Name of the generator to use
            batch_size: Number of documents (uses config default if not specified)
            refresh: Whether to refresh the index after injection

        Returns:
            Tuple of (success_count, error_count)
        """
        if generator_name not in self.generators:
            raise ValueError(f"Unknown generator: {generator_name}")

        generator = self.generators[generator_name]
        batch_size = batch_size or self.config.injection.batch_size

        # Generate batch
        documents = generator.generate_batch(batch_size)
        actions = generator.prepare_bulk_batch(documents)

        # Bulk index
        try:
            success, errors = self.client.bulk_index(
                actions,
                chunk_size=min(batch_size, 500),
                raise_on_error=False,
                refresh=refresh,
            )

            error_count = len(errors) if errors else 0
            self._stats["total_documents"] += success
            self._stats["total_errors"] += error_count

            logger.debug(f"Injected {success} documents, {error_count} errors")

            return success, error_count

        except Exception as e:
            logger.error(f"Bulk injection failed: {e}")
            self._stats["total_errors"] += batch_size
            return 0, batch_size

    def inject_all(
        self,
        batch_size: int | None = None,
        refresh: bool = False,
    ) -> dict[str, tuple[int, int]]:
        """Inject a batch from all enabled generators.

        Args:
            batch_size: Number of documents per generator
            refresh: Whether to refresh indices after injection

        Returns:
            Dictionary mapping generator names to (success, error) counts
        """
        results = {}

        for name in self.generators:
            results[name] = self.inject_batch(name, batch_size, refresh)

        return results

    def run(
        self,
        total_documents: int | None = None,
        continuous: bool | None = None,
        interval: float | None = None,
        callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        """Run the injection process.

        Args:
            total_documents: Total documents to inject (None for config value)
            continuous: Run continuously (None for config value)
            interval: Seconds between batches (None for config value)
            callback: Optional callback for progress updates

        Returns:
            Statistics dictionary
        """
        total = total_documents or self.config.injection.total_documents
        continuous = continuous if continuous is not None else self.config.injection.continuous
        interval = interval or self.config.injection.interval_seconds
        batch_size = self.config.injection.batch_size

        # Calculate documents per generator
        num_generators = len(self.generators)
        if num_generators == 0:
            logger.warning("No generators enabled")
            return self._stats

        docs_per_generator = batch_size // num_generators

        # Setup signal handlers for graceful shutdown
        self._running = True
        self._setup_signal_handlers()

        self._stats["start_time"] = time.time()
        logger.info("Starting injection process...")

        try:
            iteration = 0
            while self._running:
                iteration += 1

                # Inject from all generators
                for name, generator in self.generators.items():
                    if not self._running:
                        break

                    success, errors = self.inject_batch(name, docs_per_generator)

                    if callback:
                        callback(
                            {
                                "iteration": iteration,
                                "generator": name,
                                "success": success,
                                "errors": errors,
                                "total_documents": self._stats["total_documents"],
                                "total_errors": self._stats["total_errors"],
                            }
                        )

                # Check if we've reached the target
                if total and self._stats["total_documents"] >= total:
                    logger.info(f"Reached target of {total} documents")
                    break

                # Check if continuous mode
                if not continuous and total is None:
                    break

                # Wait for next iteration
                if self._running and (continuous or (total and self._stats["total_documents"] < total)):
                    time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self._running = False
            self._stats["end_time"] = time.time()

        # Log final stats
        duration = self._stats["end_time"] - self._stats["start_time"]
        rate = self._stats["total_documents"] / duration if duration > 0 else 0

        logger.info(
            f"Injection complete: {self._stats['total_documents']} documents "
            f"in {duration:.2f}s ({rate:.2f} docs/s), "
            f"{self._stats['total_errors']} errors"
        )

        return self._stats

    def stop(self) -> None:
        """Stop the injection process."""
        logger.info("Stopping injection process...")
        self._running = False

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, stopping...")
            self.stop()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    @property
    def stats(self) -> dict[str, Any]:
        """Get current statistics."""
        return self._stats.copy()

    def __enter__(self) -> "DataInjector":
        """Context manager entry."""
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.disconnect()
