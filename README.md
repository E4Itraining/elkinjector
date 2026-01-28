# Elasticsearch v8 Data Injector

Injecteur de donnees en continu pour Elasticsearch v8.x, entierement containerise avec Docker.

## Fonctionnalites

- Compatible **uniquement** avec Elasticsearch v8.x
- Support HTTPS et authentification (securite v8)
- Generation de donnees synthetiques (logs, metriques, evenements)
- Injection en bulk optimisee pour les performances
- Configuration flexible via variables d'environnement, YAML ou CLI
- Arret gracieux avec gestion des signaux SIGTERM/SIGINT
- Health checks integres
- Mode simple (sans securite) pour le developpement local
- Templates JSON personnalisables avec 30+ placeholders
- Suite de tests unitaires complete

## Types de donnees generes

### Logs
```json
{
  "@timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "api-gateway",
  "message": "Request completed successfully: GET /api/v1/users",
  "environment": "production",
  "region": "eu-west-1",
  "host": "api-gateway-1.internal",
  "trace_id": "abc123...",
  "span_id": "def456..."
}
```

### Metriques
```json
{
  "@timestamp": "2024-01-15T10:30:00Z",
  "metric_name": "cpu",
  "metric_value": 45.23,
  "unit": "percent",
  "service": "user-service",
  "environment": "production",
  "region": "us-east-1",
  "host": "user-service-2.internal"
}
```

### Evenements
```json
{
  "@timestamp": "2024-01-15T10:30:00Z",
  "event_type": "purchase",
  "event_data": {
    "user_id": "user_12345",
    "amount": 99.99,
    "currency": "EUR"
  },
  "service": "payment-service",
  "environment": "production"
}
```

## Demarrage rapide

### Mode simple (developpement local)

Le mode simple desactive la securite Elasticsearch pour faciliter les tests :

```bash
# Demarrer Elasticsearch + Injecteur
docker-compose -f docker-compose-simple.yml up -d

# Avec Kibana (optionnel)
docker-compose -f docker-compose-simple.yml --profile with-kibana up -d

# Voir les logs de l'injecteur
docker logs -f data-injector-simple

# Verifier les donnees dans Elasticsearch
curl http://localhost:9200/injector-data/_count
```

### Mode securise (production)

Le mode complet utilise HTTPS et l'authentification :

```bash
# Copier et configurer les variables d'environnement
cp .env.example .env
# Editer .env avec vos parametres

# Demarrer la stack complete
docker-compose up -d

# Avec Kibana
docker-compose --profile with-kibana up -d

# Voir les logs
docker logs -f data-injector
```

## Configuration

### Variables d'environnement

| Variable | Description | Valeur par defaut |
|----------|-------------|-------------------|
| `ES_HOST` | URL Elasticsearch | `https://elasticsearch:9200` |
| `ES_USER` | Utilisateur | `elastic` |
| `ES_PASSWORD` | Mot de passe | `changeme` |
| `ES_INDEX` | Nom de l'index | `injector-data` |
| `ES_VERIFY_CERTS` | Verifier certificats SSL | `false` |
| `ES_CA_CERTS` | Chemin certificat CA | - |
| `BATCH_SIZE` | Taille du batch | `100` |
| `INJECTION_INTERVAL` | Intervalle entre batches (sec) | `1.0` |
| `DATA_TYPE` | Type de donnees (`logs`, `metrics`, `events`) | `logs` |
| `MAX_RETRIES` | Tentatives de connexion | `5` |
| `RETRY_DELAY` | Delai entre tentatives (sec) | `5.0` |

### Exemples de configuration

**Injection haute frequence :**
```bash
BATCH_SIZE=500
INJECTION_INTERVAL=0.5
```

**Injection de metriques :**
```bash
DATA_TYPE=metrics
ES_INDEX=app-metrics
```

## Architecture

```
elkinjector/
├── elkinjector/                 # Package Python principal
│   ├── __init__.py             # Exports du package
│   ├── cli.py                  # Interface CLI (Click)
│   ├── client.py               # Client Elasticsearch
│   ├── config.py               # Gestion de la configuration
│   ├── injector.py             # Orchestrateur d'injection
│   └── generators/             # Generateurs de donnees
│       ├── base.py             # Classe abstraite BaseGenerator
│       ├── logs.py             # Generateur de logs
│       ├── metrics.py          # Generateur de metriques
│       └── json_generator.py   # Generateur JSON personnalise
├── tests/                       # Suite de tests
│   ├── conftest.py             # Fixtures partagees
│   ├── test_config.py          # Tests de configuration
│   ├── test_client.py          # Tests du client ES
│   ├── test_generators.py      # Tests des generateurs
│   ├── test_injector.py        # Tests de l'injecteur
│   └── test_cli.py             # Tests de l'interface CLI
├── src/
│   └── injector.py             # Injecteur legacy (Docker)
├── Dockerfile                   # Image Docker de production
├── Dockerfile.test              # Image Docker pour les tests
├── docker-compose.yml           # Stack complete avec securite
├── docker-compose-simple.yml    # Stack simplifiee pour dev
├── docker-compose-test.yml      # Stack de tests (Docker)
├── run_tests.py                 # Script de lancement des tests
├── Makefile                     # Commandes Make
├── pyproject.toml               # Configuration du projet Python
├── requirements.txt             # Dependances Python
├── config.example.yaml          # Exemple de configuration YAML
├── .env.example                 # Template de configuration
└── README.md                    # Documentation
```

## Tests

ElkInjector dispose d'une suite de tests unitaires couvrant la configuration, les generateurs de donnees, le client Elasticsearch, l'injecteur et l'interface CLI.

### Pre-requis pour les tests

```bash
# Installer les dependances de developpement
pip install -e ".[dev]"
```

### Executer les tests localement (Python)

```bash
# Lancer tous les tests
python run_tests.py

# Avec rapport de couverture
python run_tests.py --cov

# Avec rapport HTML de couverture
python run_tests.py --cov --html

# Tester un fichier specifique
python run_tests.py --file tests/test_generators.py

# Filtrer par nom de test
python run_tests.py -k TestLogGenerator

# Ou directement avec pytest
pytest tests/ -v
pytest tests/ -v --cov=elkinjector --cov-report=term-missing
```

### Executer les tests via Docker

Les tests peuvent etre executes dans un conteneur Docker, sans aucune dependance locale :

```bash
# Tests unitaires via Docker
docker compose -f docker-compose-test.yml up --build --abort-on-container-exit test-unit

# Tests d'integration avec Elasticsearch
docker compose -f docker-compose-test.yml --profile integration up --build --abort-on-container-exit test-integration
```

### Executer les tests via Make

```bash
# Tests unitaires locaux
make test

# Tests avec couverture
make test-cov

# Tests avec rapport HTML
make test-html

# Tests unitaires via Docker
make test-docker

# Tests d'integration via Docker (avec Elasticsearch)
make test-docker-integration
```

### Structure des tests

| Fichier | Description |
|---------|-------------|
| `tests/conftest.py` | Fixtures pytest partagees (configurations de test) |
| `tests/test_config.py` | Tests des dataclasses de configuration, chargement YAML, variables d'environnement |
| `tests/test_client.py` | Tests du client Elasticsearch (mock), connexion, ping, bulk, CRUD index |
| `tests/test_generators.py` | Tests des generateurs (logs, metriques, JSON), placeholders, templates |
| `tests/test_injector.py` | Tests de l'orchestrateur d'injection, batch, callbacks, signaux |
| `tests/test_cli.py` | Tests de l'interface CLI (commandes, options, aide) |

## Surveillance

### Verifier le nombre de documents

```bash
# Mode simple
curl http://localhost:9200/injector-data/_count

# Mode securise
curl -k -u elastic:changeme https://localhost:9200/injector-data/_count
```

### Voir les derniers documents

```bash
# Mode simple
curl http://localhost:9200/injector-data/_search?size=5&sort=@timestamp:desc

# Mode securise
curl -k -u elastic:changeme "https://localhost:9200/injector-data/_search?size=5&sort=@timestamp:desc"
```

### Statistiques de l'index

```bash
curl http://localhost:9200/injector-data/_stats
```

## Arreter les services

```bash
# Mode simple
docker-compose -f docker-compose-simple.yml down

# Avec suppression des volumes
docker-compose -f docker-compose-simple.yml down -v

# Mode securise
docker-compose down -v
```

## Compatibilite

Cet injecteur est compatible **uniquement** avec Elasticsearch v8.x.

La verification de version est effectuee au demarrage :
- Si Elasticsearch n'est pas en v8.x, l'injecteur s'arrete avec une erreur
- Les fonctionnalites specifiques a v8 (nouveau client, bulk API) sont utilisees

## Developpement

### Executer localement (sans Docker)

```bash
# Creer un environnement virtuel
python -m venv venv
source venv/bin/activate

# Installer les dependances (production + dev)
pip install -e ".[dev]"

# Configurer les variables
export ES_HOST=http://localhost:9200
export ES_VERIFY_CERTS=false

# Lancer l'injecteur
elkinjector inject -h localhost -p 9200

# Ou avec le script legacy
python src/injector.py
```

### Build de l'image Docker

```bash
docker build -t es-injector:latest .
```

### Commandes CLI disponibles

```bash
# Injection de donnees
elkinjector inject -h localhost -p 9200 -n 10000

# Verifier la connexion
elkinjector check -h localhost -p 9200

# Supprimer les index
elkinjector clean --prefix elkinjector --force

# Generer un fichier de configuration
elkinjector init-config -o elkinjector.yaml

# Afficher les placeholders disponibles
elkinjector show-placeholders
```

## Licence

Voir le fichier [LICENSE](LICENSE) pour plus de details.
