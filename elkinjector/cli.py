"""Command-line interface for ElkInjector."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click

from elkinjector import __version__
from elkinjector.config import Config
from elkinjector.generators import JsonGenerator
from elkinjector.injector import DataInjector


def setup_logging(verbose: bool, quiet: bool) -> None:
    """Setup logging based on verbosity flags."""
    if quiet:
        level = logging.WARNING
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@click.group()
@click.version_option(version=__version__, prog_name="elkinjector")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.option("-q", "--quiet", is_flag=True, help="Suppress non-error output")
@click.pass_context
def main(ctx: click.Context, verbose: bool, quiet: bool) -> None:
    """ElkInjector - Data injection tool for Elasticsearch.

    Inject logs, metrics, and custom JSON documents into Elasticsearch
    for testing, development, and demonstration purposes.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    setup_logging(verbose, quiet)


@main.command()
@click.option(
    "-c", "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file (YAML)",
)
@click.option("-h", "--host", default="localhost", help="Elasticsearch host")
@click.option("-p", "--port", default=9200, type=int, help="Elasticsearch port")
@click.option("--scheme", default="http", type=click.Choice(["http", "https"]), help="Connection scheme")
@click.option("-u", "--username", help="Elasticsearch username")
@click.option("-P", "--password", help="Elasticsearch password")
@click.option("--api-key", help="Elasticsearch API key")
@click.option("-n", "--count", type=int, help="Total number of documents to inject")
@click.option("-b", "--batch-size", default=1000, type=int, help="Documents per batch")
@click.option("-i", "--interval", default=1.0, type=float, help="Seconds between batches")
@click.option("--continuous", is_flag=True, help="Run continuously until stopped")
@click.option("--prefix", default="elkinjector", help="Index prefix")
@click.option("--logs/--no-logs", default=True, help="Enable/disable log generation")
@click.option("--metrics/--no-metrics", default=True, help="Enable/disable metrics generation")
@click.option("--json/--no-json", default=False, help="Enable/disable JSON generation")
@click.option("--template", type=click.Path(exists=True, path_type=Path), help="JSON template file")
@click.pass_context
def inject(
    ctx: click.Context,
    config: Path | None,
    host: str,
    port: int,
    scheme: str,
    username: str | None,
    password: str | None,
    api_key: str | None,
    count: int | None,
    batch_size: int,
    interval: float,
    continuous: bool,
    prefix: str,
    logs: bool,
    metrics: bool,
    json: bool,
    template: Path | None,
) -> None:
    """Inject data into Elasticsearch.

    Examples:

        # Basic injection with defaults
        elkinjector inject -h localhost -p 9200

        # Inject 10000 documents
        elkinjector inject -n 10000

        # Continuous injection with custom interval
        elkinjector inject --continuous -i 0.5

        # Only inject logs
        elkinjector inject --logs --no-metrics

        # Use custom JSON template
        elkinjector inject --json --template my_template.json
    """
    # Load or create configuration
    if config:
        cfg = Config.from_yaml(config)
    else:
        cfg = Config()

    # Override with CLI arguments
    cfg.elasticsearch.host = host
    cfg.elasticsearch.port = port
    cfg.elasticsearch.scheme = scheme

    if username:
        cfg.elasticsearch.username = username
    if password:
        cfg.elasticsearch.password = password
    if api_key:
        cfg.elasticsearch.api_key = api_key

    cfg.injection.batch_size = batch_size
    cfg.injection.interval_seconds = interval
    cfg.injection.continuous = continuous
    cfg.injection.index_prefix = prefix

    if count:
        cfg.injection.total_documents = count

    cfg.logs.enabled = logs
    cfg.metrics.enabled = metrics
    cfg.json.enabled = json

    if template:
        cfg.json.template_file = str(template)

    # Create injector and run
    try:
        with DataInjector(cfg) as injector:
            def progress_callback(stats):
                if not ctx.obj.get("quiet"):
                    click.echo(
                        f"\r[{stats['generator']}] "
                        f"Total: {stats['total_documents']} docs, "
                        f"{stats['total_errors']} errors",
                        nl=False,
                    )

            stats = injector.run(callback=progress_callback)

            click.echo()  # New line after progress
            click.echo(
                f"Injection complete: {stats['total_documents']} documents, "
                f"{stats['total_errors']} errors"
            )

    except ConnectionError as e:
        click.echo(f"Connection error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if ctx.obj.get("verbose"):
            raise
        sys.exit(1)


@main.command()
@click.option("-h", "--host", default="localhost", help="Elasticsearch host")
@click.option("-p", "--port", default=9200, type=int, help="Elasticsearch port")
@click.option("--scheme", default="http", type=click.Choice(["http", "https"]), help="Connection scheme")
@click.option("-u", "--username", help="Elasticsearch username")
@click.option("-P", "--password", help="Elasticsearch password")
@click.option("--api-key", help="Elasticsearch API key")
def check(
    host: str,
    port: int,
    scheme: str,
    username: str | None,
    password: str | None,
    api_key: str | None,
) -> None:
    """Check Elasticsearch connection and cluster health.

    Examples:

        elkinjector check -h localhost -p 9200
        elkinjector check --scheme https -u elastic -P password
    """
    from elkinjector.client import ElasticsearchClient
    from elkinjector.config import ElasticsearchConfig

    config = ElasticsearchConfig(
        host=host,
        port=port,
        scheme=scheme,
        username=username,
        password=password,
        api_key=api_key,
    )

    client = ElasticsearchClient(config)

    try:
        client.connect()

        # Check ping
        if client.ping():
            click.echo(click.style("✓ Connection successful", fg="green"))
        else:
            click.echo(click.style("✗ Ping failed", fg="red"))
            sys.exit(1)

        # Get cluster info
        info = client.info()
        click.echo(f"\nCluster: {info['cluster_name']}")
        click.echo(f"Version: {info['version']['number']}")

        # Get cluster health
        health = client.health()
        status_color = {
            "green": "green",
            "yellow": "yellow",
            "red": "red",
        }.get(health["status"], "white")

        click.echo(f"Status: {click.style(health['status'], fg=status_color)}")
        click.echo(f"Nodes: {health['number_of_nodes']}")
        click.echo(f"Shards: {health['active_shards']}")

    except Exception as e:
        click.echo(click.style(f"✗ Connection failed: {e}", fg="red"), err=True)
        sys.exit(1)
    finally:
        client.disconnect()


@main.command("init-config")
@click.option(
    "-o", "--output",
    type=click.Path(path_type=Path),
    default="elkinjector.yaml",
    help="Output file path",
)
def init_config(output: Path) -> None:
    """Generate a sample configuration file.

    Examples:

        elkinjector init-config
        elkinjector init-config -o my_config.yaml
    """
    config = Config()
    config.save_yaml(output)
    click.echo(f"Configuration file created: {output}")


@main.command("show-placeholders")
def show_placeholders() -> None:
    """Show available JSON template placeholders.

    These placeholders can be used in JSON templates for dynamic data generation.
    """
    placeholders = JsonGenerator.get_available_placeholders()

    click.echo("Available template placeholders:\n")
    click.echo("Usage: {{placeholder}} or {{placeholder:args}}\n")

    for p in placeholders:
        if ":" in p:
            name, args = p.split(":", 1)
            click.echo(f"  {{{{{name}:{args}}}}} - {name} with arguments")
        else:
            click.echo(f"  {{{{{p}}}}}")

    click.echo("\nExample template:")
    click.echo("""
{
  "@timestamp": "{{timestamp}}",
  "user_id": "{{uuid_short}}",
  "action": "{{choice:login,logout,purchase}}",
  "amount": "{{float:0:1000}}",
  "ip": "{{ipv4}}"
}
""")


@main.command()
@click.option("-h", "--host", default="localhost", help="Elasticsearch host")
@click.option("-p", "--port", default=9200, type=int, help="Elasticsearch port")
@click.option("--scheme", default="http", type=click.Choice(["http", "https"]), help="Connection scheme")
@click.option("-u", "--username", help="Elasticsearch username")
@click.option("-P", "--password", help="Elasticsearch password")
@click.option("--prefix", default="elkinjector", help="Index prefix to clean")
@click.option("--force", is_flag=True, help="Skip confirmation")
def clean(
    host: str,
    port: int,
    scheme: str,
    username: str | None,
    password: str | None,
    prefix: str,
    force: bool,
) -> None:
    """Clean up (delete) ElkInjector indices.

    Deletes all indices matching the specified prefix.

    Examples:

        elkinjector clean --prefix elkinjector
        elkinjector clean --force
    """
    from elkinjector.client import ElasticsearchClient
    from elkinjector.config import ElasticsearchConfig

    config = ElasticsearchConfig(
        host=host,
        port=port,
        scheme=scheme,
        username=username,
        password=password,
    )

    client = ElasticsearchClient(config)

    try:
        client.connect()

        # Find matching indices
        pattern = f"{prefix}-*"

        indices = client.client.indices.get(index=pattern, ignore_unavailable=True)

        if not indices:
            click.echo(f"No indices found matching pattern: {pattern}")
            return

        index_names = list(indices.keys())
        click.echo(f"Found {len(index_names)} indices:")
        for name in index_names:
            count = client.count(name)
            click.echo(f"  - {name} ({count} documents)")

        if not force:
            if not click.confirm("\nDelete these indices?"):
                click.echo("Aborted.")
                return

        # Delete indices
        for name in index_names:
            client.delete_index(name)
            click.echo(f"Deleted: {name}")

        click.echo(click.style("\n✓ Cleanup complete", fg="green"))

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        sys.exit(1)
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
