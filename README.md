# Elasticsearch v8 Data Injector

Injecteur de donnees en continu pour Elasticsearch v8.x, entierement containerise avec Docker.

## Fonctionnalites

- Compatible **uniquement** avec Elasticsearch v8.x
- Support HTTPS et authentification (securite v8)
- Generation de donnees synthetiques (logs, metriques, evenements)
- Injection en bulk optimisee pour les performances
- Configuration flexible via variables d'environnement
- Arret gracieux avec gestion des signaux SIGTERM/SIGINT
- Health checks integres
- Mode simple (sans securite) pour le developpement local

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
├── src/
│   └── injector.py          # Code principal de l'injecteur
├── Dockerfile               # Image Docker optimisee
├── docker-compose.yml       # Stack complete avec securite
├── docker-compose-simple.yml # Stack simplifiee pour dev
├── requirements.txt         # Dependances Python
├── .env.example            # Template de configuration
└── README.md               # Documentation
```

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

# Installer les dependances
pip install -r requirements.txt

# Configurer les variables
export ES_HOST=http://localhost:9200
export ES_VERIFY_CERTS=false

# Lancer l'injecteur
python src/injector.py
```

### Build de l'image Docker

```bash
docker build -t es-injector:latest .
```

## Licence

Voir le fichier [LICENSE](LICENSE) pour plus de details.
