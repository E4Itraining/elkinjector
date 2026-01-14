"""Log data generator for ElkInjector."""

import random
import traceback
from typing import Any

from faker import Faker

from elkinjector.config import LogGeneratorConfig
from elkinjector.generators.base import BaseGenerator


class LogGenerator(BaseGenerator):
    """Generator for application and system logs."""

    # Sample log message templates by level
    LOG_TEMPLATES = {
        "DEBUG": [
            "Processing request with parameters: {params}",
            "Cache lookup for key: {key}",
            "Database query executed in {duration}ms",
            "Memory usage: {memory}MB",
            "Thread {thread_id} started processing",
            "Configuration loaded: {config}",
        ],
        "INFO": [
            "User {user_id} logged in successfully",
            "Request completed: {method} {path} - {status_code}",
            "Service started on port {port}",
            "Scheduled job '{job_name}' completed",
            "Connection established to {host}:{port}",
            "Processing batch of {count} items",
            "Health check passed for {service}",
        ],
        "WARNING": [
            "High memory usage detected: {memory}%",
            "Slow query detected: {duration}ms",
            "Rate limit approaching for user {user_id}",
            "Deprecated API endpoint called: {endpoint}",
            "Connection pool running low: {available}/{total}",
            "Retry attempt {attempt} for {operation}",
            "Certificate expires in {days} days",
        ],
        "ERROR": [
            "Failed to connect to database: {error}",
            "Authentication failed for user {user_id}",
            "Request timeout after {duration}ms",
            "Invalid input received: {details}",
            "Service {service} is unreachable",
            "Failed to process message: {message_id}",
            "Disk space critical: {available}GB remaining",
        ],
        "CRITICAL": [
            "Database connection lost - initiating failover",
            "Out of memory - system unstable",
            "Security breach detected from IP {ip}",
            "Data corruption detected in {table}",
            "Service crashed - automatic restart initiated",
            "Cluster node {node} has failed",
        ],
    }

    # Sample exception types for stack traces
    EXCEPTION_TYPES = [
        "ConnectionError",
        "TimeoutError",
        "ValueError",
        "KeyError",
        "RuntimeError",
        "IOError",
        "PermissionError",
        "DatabaseError",
        "AuthenticationError",
        "ValidationError",
    ]

    def __init__(
        self,
        config: LogGeneratorConfig | None = None,
        index_prefix: str = "elkinjector",
    ):
        """Initialize the log generator.

        Args:
            config: Log generator configuration
            index_prefix: Prefix for the index name
        """
        self.config = config or LogGeneratorConfig()
        super().__init__(self.config.index_name, index_prefix)
        self.faker = Faker()

    def _generate_message(self, level: str) -> str:
        """Generate a log message for the given level."""
        templates = self.LOG_TEMPLATES.get(level, self.LOG_TEMPLATES["INFO"])
        template = random.choice(templates)

        # Generate placeholder values
        placeholders = {
            "params": str({"id": self.faker.uuid4()[:8], "action": self.faker.word()}),
            "key": f"cache:{self.faker.uuid4()[:8]}",
            "duration": random.randint(1, 5000),
            "memory": random.randint(100, 8000),
            "thread_id": random.randint(1, 100),
            "config": self.faker.file_name(extension="yaml"),
            "user_id": self.faker.uuid4()[:8],
            "method": random.choice(["GET", "POST", "PUT", "DELETE", "PATCH"]),
            "path": self.faker.uri_path(),
            "status_code": random.choice([200, 201, 204, 400, 401, 403, 404, 500]),
            "port": random.choice([8080, 8443, 3000, 5000, 9200]),
            "job_name": self.faker.word() + "_job",
            "host": self.faker.hostname(),
            "count": random.randint(10, 10000),
            "service": random.choice(self.config.services),
            "endpoint": f"/api/v{random.randint(1, 3)}/{self.faker.word()}",
            "available": random.randint(1, 50),
            "total": 100,
            "attempt": random.randint(1, 5),
            "operation": random.choice(["database_write", "api_call", "file_upload"]),
            "days": random.randint(1, 30),
            "error": random.choice(self.EXCEPTION_TYPES),
            "details": self.faker.sentence(),
            "message_id": self.faker.uuid4()[:12],
            "ip": self.faker.ipv4(),
            "table": self.faker.word() + "_table",
            "node": f"node-{random.randint(1, 10)}",
        }

        try:
            return template.format(**placeholders)
        except KeyError:
            return template

    def _generate_stack_trace(self) -> str:
        """Generate a fake stack trace."""
        exception_type = random.choice(self.EXCEPTION_TYPES)
        message = self.faker.sentence()

        # Generate fake stack frames
        frames = []
        num_frames = random.randint(3, 8)
        for _ in range(num_frames):
            file_path = f"/app/{self.faker.file_path(depth=random.randint(1, 4), extension='py')}"
            line_no = random.randint(10, 500)
            func_name = self.faker.word() + "_" + random.choice(["handler", "process", "execute"])
            frames.append(f'  File "{file_path}", line {line_no}, in {func_name}')

        stack = "Traceback (most recent call last):\n"
        stack += "\n".join(frames)
        stack += f"\n{exception_type}: {message}"

        return stack

    def generate_one(self) -> dict[str, Any]:
        """Generate a single log document."""
        # Select log level based on weights
        level = random.choices(
            self.config.log_levels,
            weights=self.config.log_level_weights[: len(self.config.log_levels)],
            k=1,
        )[0]

        # Base log document
        document = {
            "@timestamp": self.utc_now(),
            "level": level,
            "logger": f"com.app.{self.faker.word()}.{self.faker.word().capitalize()}",
            "message": self._generate_message(level),
            "service": {
                "name": random.choice(self.config.services),
                "version": f"{random.randint(1, 5)}.{random.randint(0, 20)}.{random.randint(0, 100)}",
                "environment": random.choice(["production", "staging", "development"]),
            },
            "host": {
                "name": self.faker.hostname(),
                "ip": self.faker.ipv4(),
            },
            "process": {
                "pid": random.randint(1000, 65535),
                "thread": {
                    "id": random.randint(1, 100),
                    "name": f"worker-{random.randint(1, 20)}",
                },
            },
            "trace": {
                "id": self.faker.uuid4().replace("-", ""),
                "span_id": self.faker.hexify(text="^^^^^^^^^^^^^^^^"),
            },
        }

        # Add stack trace for errors with configured probability
        if (
            self.config.include_stack_trace
            and level in ["ERROR", "CRITICAL"]
            and random.random() < self.config.stack_trace_probability
        ):
            document["error"] = {
                "type": random.choice(self.EXCEPTION_TYPES),
                "message": document["message"],
                "stack_trace": self._generate_stack_trace(),
            }

        return document
