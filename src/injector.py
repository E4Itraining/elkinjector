#!/usr/bin/env python3
"""
Elasticsearch v8 Data Injector
Continuous data injection for Elasticsearch v8 with HTTPS and authentication support.
"""

import os
import sys
import time
import random
import string
import logging
import signal
from datetime import datetime, timezone
from typing import Generator, Dict, Any, Optional
from dataclasses import dataclass, field

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, AuthenticationException, ElasticsearchException


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


@dataclass
class InjectorConfig:
    """Configuration for the Elasticsearch injector."""
    es_host: str = field(default_factory=lambda: os.getenv('ES_HOST', 'https://elasticsearch:9200'))
    es_user: str = field(default_factory=lambda: os.getenv('ES_USER', 'elastic'))
    es_password: str = field(default_factory=lambda: os.getenv('ES_PASSWORD', 'changeme'))
    es_index: str = field(default_factory=lambda: os.getenv('ES_INDEX', 'injector-data'))
    es_verify_certs: bool = field(default_factory=lambda: os.getenv('ES_VERIFY_CERTS', 'false').lower() == 'true')
    es_ca_certs: Optional[str] = field(default_factory=lambda: os.getenv('ES_CA_CERTS'))

    batch_size: int = field(default_factory=lambda: int(os.getenv('BATCH_SIZE', '100')))
    injection_interval: float = field(default_factory=lambda: float(os.getenv('INJECTION_INTERVAL', '1.0')))
    data_type: str = field(default_factory=lambda: os.getenv('DATA_TYPE', 'logs'))  # logs, metrics, events

    max_retries: int = field(default_factory=lambda: int(os.getenv('MAX_RETRIES', '5')))
    retry_delay: float = field(default_factory=lambda: float(os.getenv('RETRY_DELAY', '5.0')))


class DataGenerator:
    """Generates various types of synthetic data."""

    LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    SERVICES = ['api-gateway', 'user-service', 'auth-service', 'payment-service', 'notification-service']
    HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
    HTTP_STATUS_CODES = [200, 201, 204, 400, 401, 403, 404, 500, 502, 503]
    ENVIRONMENTS = ['production', 'staging', 'development']
    REGIONS = ['eu-west-1', 'us-east-1', 'us-west-2', 'ap-southeast-1']

    @classmethod
    def generate_log(cls) -> Dict[str, Any]:
        """Generate a synthetic log entry."""
        service = random.choice(cls.SERVICES)
        level = random.choices(
            cls.LOG_LEVELS,
            weights=[10, 50, 25, 10, 5]  # Weighted distribution
        )[0]

        messages = {
            'DEBUG': [
                f"Processing request for user_{random.randint(1, 10000)}",
                f"Cache lookup for key: {cls._random_string(12)}",
                f"Database query executed in {random.randint(1, 100)}ms"
            ],
            'INFO': [
                f"Request completed successfully: {random.choice(cls.HTTP_METHODS)} /api/v1/{cls._random_string(8)}",
                f"User login successful: user_{random.randint(1, 10000)}",
                f"Service started on port {random.choice([8080, 8081, 3000, 5000])}"
            ],
            'WARNING': [
                f"High memory usage detected: {random.randint(75, 95)}%",
                f"Slow query detected: {random.randint(500, 5000)}ms",
                f"Rate limit approaching for client: {cls._random_string(8)}"
            ],
            'ERROR': [
                f"Failed to connect to database: timeout after {random.randint(5, 30)}s",
                f"Authentication failed for user: user_{random.randint(1, 10000)}",
                f"External API returned error: HTTP {random.choice([500, 502, 503])}"
            ],
            'CRITICAL': [
                "Database connection pool exhausted",
                "Out of memory error occurred",
                f"Service health check failed after {random.randint(3, 10)} attempts"
            ]
        }

        return {
            '@timestamp': datetime.now(timezone.utc).isoformat(),
            'level': level,
            'service': service,
            'message': random.choice(messages[level]),
            'environment': random.choice(cls.ENVIRONMENTS),
            'region': random.choice(cls.REGIONS),
            'host': f"{service}-{random.randint(1, 5)}.internal",
            'trace_id': cls._random_string(32),
            'span_id': cls._random_string(16),
            'metadata': {
                'version': f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 20)}",
                'build': cls._random_string(7)
            }
        }

    @classmethod
    def generate_metric(cls) -> Dict[str, Any]:
        """Generate a synthetic metric entry."""
        service = random.choice(cls.SERVICES)
        metric_types = ['cpu', 'memory', 'disk', 'network', 'request_latency', 'error_rate']
        metric_type = random.choice(metric_types)

        values = {
            'cpu': random.uniform(0, 100),
            'memory': random.uniform(0, 100),
            'disk': random.uniform(0, 100),
            'network': random.uniform(0, 1000),  # Mbps
            'request_latency': random.uniform(1, 5000),  # ms
            'error_rate': random.uniform(0, 10)  # percentage
        }

        units = {
            'cpu': 'percent',
            'memory': 'percent',
            'disk': 'percent',
            'network': 'mbps',
            'request_latency': 'ms',
            'error_rate': 'percent'
        }

        return {
            '@timestamp': datetime.now(timezone.utc).isoformat(),
            'metric_name': metric_type,
            'metric_value': round(values[metric_type], 2),
            'unit': units[metric_type],
            'service': service,
            'environment': random.choice(cls.ENVIRONMENTS),
            'region': random.choice(cls.REGIONS),
            'host': f"{service}-{random.randint(1, 5)}.internal",
            'tags': {
                'cluster': f"cluster-{random.randint(1, 3)}",
                'pod': f"{service}-{cls._random_string(5)}"
            }
        }

    @classmethod
    def generate_event(cls) -> Dict[str, Any]:
        """Generate a synthetic event entry."""
        event_types = ['user_signup', 'user_login', 'purchase', 'page_view', 'api_call', 'error']
        event_type = random.choice(event_types)

        event_data = {
            'user_signup': {
                'user_id': f"user_{random.randint(1, 100000)}",
                'email_domain': random.choice(['gmail.com', 'yahoo.com', 'outlook.com', 'company.com']),
                'signup_source': random.choice(['web', 'mobile_app', 'api'])
            },
            'user_login': {
                'user_id': f"user_{random.randint(1, 100000)}",
                'login_method': random.choice(['password', 'oauth_google', 'oauth_github', 'sso']),
                'success': random.choice([True, True, True, False])  # 75% success rate
            },
            'purchase': {
                'user_id': f"user_{random.randint(1, 100000)}",
                'amount': round(random.uniform(9.99, 999.99), 2),
                'currency': random.choice(['USD', 'EUR', 'GBP']),
                'product_id': f"prod_{random.randint(1, 1000)}"
            },
            'page_view': {
                'user_id': f"user_{random.randint(1, 100000)}",
                'page': random.choice(['/home', '/products', '/checkout', '/profile', '/settings']),
                'referrer': random.choice(['google', 'direct', 'facebook', 'twitter', None])
            },
            'api_call': {
                'method': random.choice(cls.HTTP_METHODS),
                'endpoint': f"/api/v1/{random.choice(['users', 'products', 'orders', 'payments'])}",
                'status_code': random.choice(cls.HTTP_STATUS_CODES),
                'response_time_ms': random.randint(10, 2000)
            },
            'error': {
                'error_type': random.choice(['ValidationError', 'AuthenticationError', 'DatabaseError', 'TimeoutError']),
                'error_code': f"ERR_{random.randint(1000, 9999)}",
                'stack_trace': f"at {cls._random_string(20)}.{cls._random_string(10)}()"
            }
        }

        return {
            '@timestamp': datetime.now(timezone.utc).isoformat(),
            'event_type': event_type,
            'event_data': event_data[event_type],
            'service': random.choice(cls.SERVICES),
            'environment': random.choice(cls.ENVIRONMENTS),
            'region': random.choice(cls.REGIONS),
            'session_id': cls._random_string(24),
            'client_ip': f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        }

    @staticmethod
    def _random_string(length: int) -> str:
        """Generate a random alphanumeric string."""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


class ElasticsearchInjector:
    """Handles continuous data injection into Elasticsearch v8."""

    def __init__(self, config: InjectorConfig):
        self.config = config
        self.client: Optional[Elasticsearch] = None
        self.running = True
        self.documents_injected = 0

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received shutdown signal ({signum}). Stopping injection...")
        self.running = False

    def connect(self) -> bool:
        """Establish connection to Elasticsearch v8."""
        for attempt in range(1, self.config.max_retries + 1):
            try:
                logger.info(f"Connecting to Elasticsearch at {self.config.es_host} (attempt {attempt}/{self.config.max_retries})")

                # Elasticsearch v8 client configuration
                client_kwargs = {
                    'hosts': [self.config.es_host],
                    'verify_certs': self.config.es_verify_certs,
                    'ssl_show_warn': False,
                    'request_timeout': 30,
                    'max_retries': 3,
                    'retry_on_timeout': True
                }

                # Add authentication only if credentials are provided
                if self.config.es_user and self.config.es_password:
                    client_kwargs['basic_auth'] = (self.config.es_user, self.config.es_password)

                # Add CA certificates if provided
                if self.config.es_ca_certs:
                    client_kwargs['ca_certs'] = self.config.es_ca_certs

                self.client = Elasticsearch(**client_kwargs)

                # Test connection and verify v8 compatibility
                info = self.client.info()
                version = info['version']['number']

                if not version.startswith('8.'):
                    logger.error(f"Incompatible Elasticsearch version: {version}. This injector requires v8.x")
                    return False

                logger.info(f"Connected to Elasticsearch v{version}")
                return True

            except AuthenticationException as e:
                logger.error(f"Authentication failed: {e}")
                return False
            except ConnectionError as e:
                logger.warning(f"Connection attempt {attempt} failed: {e}")
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_delay * attempt)
            except Exception as e:
                logger.error(f"Unexpected error during connection: {e}")
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_delay * attempt)

        logger.error("Failed to connect to Elasticsearch after all retries")
        return False

    def create_index_if_not_exists(self) -> bool:
        """Create the target index with appropriate mappings if it doesn't exist."""
        try:
            index_name = self.config.es_index

            if self.client.indices.exists(index=index_name):
                logger.info(f"Index '{index_name}' already exists")
                return True

            # Define index mappings based on data type
            mappings = {
                'logs': {
                    'properties': {
                        '@timestamp': {'type': 'date'},
                        'level': {'type': 'keyword'},
                        'service': {'type': 'keyword'},
                        'message': {'type': 'text'},
                        'environment': {'type': 'keyword'},
                        'region': {'type': 'keyword'},
                        'host': {'type': 'keyword'},
                        'trace_id': {'type': 'keyword'},
                        'span_id': {'type': 'keyword'},
                        'metadata': {
                            'type': 'object',
                            'properties': {
                                'version': {'type': 'keyword'},
                                'build': {'type': 'keyword'}
                            }
                        }
                    }
                },
                'metrics': {
                    'properties': {
                        '@timestamp': {'type': 'date'},
                        'metric_name': {'type': 'keyword'},
                        'metric_value': {'type': 'float'},
                        'unit': {'type': 'keyword'},
                        'service': {'type': 'keyword'},
                        'environment': {'type': 'keyword'},
                        'region': {'type': 'keyword'},
                        'host': {'type': 'keyword'},
                        'tags': {'type': 'object'}
                    }
                },
                'events': {
                    'properties': {
                        '@timestamp': {'type': 'date'},
                        'event_type': {'type': 'keyword'},
                        'event_data': {'type': 'object'},
                        'service': {'type': 'keyword'},
                        'environment': {'type': 'keyword'},
                        'region': {'type': 'keyword'},
                        'session_id': {'type': 'keyword'},
                        'client_ip': {'type': 'ip'}
                    }
                }
            }

            mapping = mappings.get(self.config.data_type, mappings['logs'])

            # Index settings optimized for ingestion
            settings = {
                'number_of_shards': 1,
                'number_of_replicas': 0,
                'refresh_interval': '5s'
            }

            self.client.indices.create(
                index=index_name,
                mappings=mapping,
                settings=settings
            )

            logger.info(f"Created index '{index_name}' with {self.config.data_type} mappings")
            return True

        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            return False

    def generate_documents(self) -> Generator[Dict[str, Any], None, None]:
        """Generate documents based on configured data type."""
        generators = {
            'logs': DataGenerator.generate_log,
            'metrics': DataGenerator.generate_metric,
            'events': DataGenerator.generate_event
        }

        generator = generators.get(self.config.data_type, DataGenerator.generate_log)

        while self.running:
            yield generator()

    def inject_batch(self, documents: list) -> bool:
        """Inject a batch of documents using bulk API."""
        if not documents:
            return True

        try:
            operations = []
            for doc in documents:
                operations.append({'index': {'_index': self.config.es_index}})
                operations.append(doc)

            response = self.client.bulk(operations=operations, refresh=False)

            if response.get('errors'):
                error_count = sum(1 for item in response['items'] if 'error' in item.get('index', {}))
                logger.warning(f"Bulk indexing had {error_count} errors out of {len(documents)} documents")

            successful = len(documents) - sum(1 for item in response['items'] if 'error' in item.get('index', {}))
            self.documents_injected += successful
            return True

        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            return False

    def run(self):
        """Main injection loop."""
        logger.info(f"Starting continuous injection - Type: {self.config.data_type}, Batch size: {self.config.batch_size}, Interval: {self.config.injection_interval}s")

        batch = []
        doc_generator = self.generate_documents()
        last_status_time = time.time()

        while self.running:
            try:
                # Collect a batch of documents
                batch = []
                for _ in range(self.config.batch_size):
                    if not self.running:
                        break
                    batch.append(next(doc_generator))

                # Inject the batch
                if batch:
                    self.inject_batch(batch)

                # Log status every 30 seconds
                current_time = time.time()
                if current_time - last_status_time >= 30:
                    logger.info(f"Status: {self.documents_injected} documents injected so far")
                    last_status_time = current_time

                # Wait before next batch
                time.sleep(self.config.injection_interval)

            except StopIteration:
                break
            except Exception as e:
                logger.error(f"Error during injection: {e}")
                time.sleep(self.config.retry_delay)

        logger.info(f"Injection stopped. Total documents injected: {self.documents_injected}")

    def close(self):
        """Close the Elasticsearch connection."""
        if self.client:
            self.client.close()
            logger.info("Elasticsearch connection closed")


def main():
    """Main entry point for the injector."""
    logger.info("=" * 50)
    logger.info("Elasticsearch v8 Data Injector Starting")
    logger.info("=" * 50)

    config = InjectorConfig()

    logger.info(f"Configuration:")
    logger.info(f"  - Host: {config.es_host}")
    logger.info(f"  - Index: {config.es_index}")
    logger.info(f"  - Data type: {config.data_type}")
    logger.info(f"  - Batch size: {config.batch_size}")
    logger.info(f"  - Injection interval: {config.injection_interval}s")
    logger.info(f"  - Verify certificates: {config.es_verify_certs}")

    injector = ElasticsearchInjector(config)

    try:
        if not injector.connect():
            logger.error("Failed to connect to Elasticsearch. Exiting.")
            sys.exit(1)

        if not injector.create_index_if_not_exists():
            logger.error("Failed to create index. Exiting.")
            sys.exit(1)

        injector.run()

    finally:
        injector.close()


if __name__ == '__main__':
    main()
