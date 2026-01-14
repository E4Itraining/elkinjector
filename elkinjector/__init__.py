"""
ElkInjector - Data injection tool for Elasticsearch

Supports injection of:
- Logs (application logs, system logs, access logs)
- Metrics (system metrics, application metrics)
- Custom JSON documents
"""

__version__ = "1.0.0"
__author__ = "E4Itraining"

from elkinjector.client import ElasticsearchClient
from elkinjector.config import Config
from elkinjector.injector import DataInjector

__all__ = ["ElasticsearchClient", "Config", "DataInjector", "__version__"]
