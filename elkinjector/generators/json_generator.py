"""JSON document generator for ElkInjector."""

import json
import random
import re
from pathlib import Path
from typing import Any

from faker import Faker

from elkinjector.config import JsonGeneratorConfig
from elkinjector.generators.base import BaseGenerator


class JsonGenerator(BaseGenerator):
    """Generator for custom JSON documents based on templates."""

    # Default template if none provided
    DEFAULT_TEMPLATE = {
        "@timestamp": "{{timestamp}}",
        "event": {
            "id": "{{uuid}}",
            "type": "{{choice:page_view,click,purchase,signup,login}}",
            "category": "{{choice:web,mobile,api}}",
        },
        "user": {
            "id": "{{uuid_short}}",
            "name": "{{name}}",
            "email": "{{email}}",
            "ip": "{{ipv4}}",
        },
        "session": {
            "id": "{{uuid}}",
            "duration_seconds": "{{int:1:3600}}",
        },
        "page": {
            "url": "{{url}}",
            "referrer": "{{url}}",
            "title": "{{sentence}}",
        },
        "device": {
            "type": "{{choice:desktop,mobile,tablet}}",
            "os": "{{choice:Windows,macOS,Linux,iOS,Android}}",
            "browser": "{{choice:Chrome,Firefox,Safari,Edge}}",
        },
        "geo": {
            "country": "{{country}}",
            "city": "{{city}}",
            "latitude": "{{latitude}}",
            "longitude": "{{longitude}}",
        },
    }

    # Pattern to match template placeholders
    PLACEHOLDER_PATTERN = re.compile(r"\{\{(\w+)(?::([^}]+))?\}\}")

    def __init__(
        self,
        config: JsonGeneratorConfig | None = None,
        index_prefix: str = "elkinjector",
    ):
        """Initialize the JSON generator.

        Args:
            config: JSON generator configuration
            index_prefix: Prefix for the index name
        """
        self.config = config or JsonGeneratorConfig()
        super().__init__(self.config.index_name, index_prefix)
        self.faker = Faker()
        self._load_template()

    def _load_template(self) -> None:
        """Load the template from config or file."""
        if self.config.template:
            self.template = self.config.template
        elif self.config.template_file:
            template_path = Path(self.config.template_file)
            if template_path.exists():
                with open(template_path) as f:
                    self.template = json.load(f)
            else:
                raise FileNotFoundError(f"Template file not found: {template_path}")
        else:
            self.template = self.DEFAULT_TEMPLATE

    def _resolve_placeholder(self, placeholder: str, args: str | None) -> Any:
        """Resolve a template placeholder to a value.

        Supported placeholders:
        - {{timestamp}}: Current UTC timestamp
        - {{uuid}}: Full UUID
        - {{uuid_short}}: Short UUID (8 chars)
        - {{int:min:max}}: Random integer in range
        - {{float:min:max}}: Random float in range
        - {{choice:a,b,c}}: Random choice from list
        - {{name}}: Random name
        - {{email}}: Random email
        - {{ipv4}}: Random IPv4 address
        - {{url}}: Random URL
        - {{sentence}}: Random sentence
        - {{word}}: Random word
        - {{country}}: Random country
        - {{city}}: Random city
        - {{latitude}}: Random latitude
        - {{longitude}}: Random longitude
        - {{company}}: Random company name
        - {{job}}: Random job title
        - {{phone}}: Random phone number
        - {{date}}: Random date
        - {{bool}}: Random boolean
        """
        if placeholder == "timestamp":
            return self.utc_now()
        elif placeholder == "uuid":
            return self.faker.uuid4()
        elif placeholder == "uuid_short":
            return self.faker.uuid4()[:8]
        elif placeholder == "int":
            if args:
                parts = args.split(":")
                min_val = int(parts[0]) if len(parts) > 0 else 0
                max_val = int(parts[1]) if len(parts) > 1 else 100
                return random.randint(min_val, max_val)
            return random.randint(0, 100)
        elif placeholder == "float":
            if args:
                parts = args.split(":")
                min_val = float(parts[0]) if len(parts) > 0 else 0.0
                max_val = float(parts[1]) if len(parts) > 1 else 1.0
                return round(random.uniform(min_val, max_val), 2)
            return round(random.random(), 2)
        elif placeholder == "choice":
            if args:
                choices = [c.strip() for c in args.split(",")]
                return random.choice(choices)
            return ""
        elif placeholder == "name":
            return self.faker.name()
        elif placeholder == "email":
            return self.faker.email()
        elif placeholder == "ipv4":
            return self.faker.ipv4()
        elif placeholder == "ipv6":
            return self.faker.ipv6()
        elif placeholder == "url":
            return self.faker.url()
        elif placeholder == "sentence":
            return self.faker.sentence()
        elif placeholder == "paragraph":
            return self.faker.paragraph()
        elif placeholder == "word":
            return self.faker.word()
        elif placeholder == "country":
            return self.faker.country()
        elif placeholder == "city":
            return self.faker.city()
        elif placeholder == "latitude":
            return float(self.faker.latitude())
        elif placeholder == "longitude":
            return float(self.faker.longitude())
        elif placeholder == "company":
            return self.faker.company()
        elif placeholder == "job":
            return self.faker.job()
        elif placeholder == "phone":
            return self.faker.phone_number()
        elif placeholder == "date":
            return self.faker.date()
        elif placeholder == "datetime":
            return self.faker.date_time().isoformat()
        elif placeholder == "bool":
            return random.choice([True, False])
        elif placeholder == "hostname":
            return self.faker.hostname()
        elif placeholder == "mac":
            return self.faker.mac_address()
        elif placeholder == "user_agent":
            return self.faker.user_agent()
        elif placeholder == "file_path":
            return self.faker.file_path()
        elif placeholder == "file_name":
            return self.faker.file_name()
        else:
            return f"{{{{unknown:{placeholder}}}}}"

    def _process_value(self, value: Any) -> Any:
        """Process a value, resolving any placeholders."""
        if isinstance(value, str):
            # Check if the entire string is a placeholder
            match = self.PLACEHOLDER_PATTERN.fullmatch(value)
            if match:
                placeholder = match.group(1)
                args = match.group(2)
                return self._resolve_placeholder(placeholder, args)

            # Replace all placeholders in the string
            def replace_match(m):
                result = self._resolve_placeholder(m.group(1), m.group(2))
                return str(result)

            return self.PLACEHOLDER_PATTERN.sub(replace_match, value)

        elif isinstance(value, dict):
            return {k: self._process_value(v) for k, v in value.items()}

        elif isinstance(value, list):
            return [self._process_value(item) for item in value]

        return value

    def generate_one(self) -> dict[str, Any]:
        """Generate a single JSON document from the template."""
        return self._process_value(self.template)

    def set_template(self, template: dict[str, Any]) -> None:
        """Set a new template.

        Args:
            template: The new template dictionary
        """
        self.template = template

    def load_template_from_file(self, path: str | Path) -> None:
        """Load a template from a JSON file.

        Args:
            path: Path to the template file
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Template file not found: {path}")

        with open(path) as f:
            self.template = json.load(f)

    @classmethod
    def get_available_placeholders(cls) -> list[str]:
        """Get list of available placeholder types."""
        return [
            "timestamp",
            "uuid",
            "uuid_short",
            "int:min:max",
            "float:min:max",
            "choice:a,b,c",
            "name",
            "email",
            "ipv4",
            "ipv6",
            "url",
            "sentence",
            "paragraph",
            "word",
            "country",
            "city",
            "latitude",
            "longitude",
            "company",
            "job",
            "phone",
            "date",
            "datetime",
            "bool",
            "hostname",
            "mac",
            "user_agent",
            "file_path",
            "file_name",
        ]
