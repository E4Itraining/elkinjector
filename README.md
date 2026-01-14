# ElkInjector

Outil d'injection de données pour Elasticsearch - logs, métriques et documents JSON personnalisés.

## Fonctionnalités

- **Génération de logs** : Logs d'application réalistes avec différents niveaux (DEBUG, INFO, WARNING, ERROR, CRITICAL), stack traces, et métadonnées de service
- **Génération de métriques** : Métriques système (CPU, mémoire, disque, réseau) et applicatives (latence, JVM, base de données)
- **Documents JSON personnalisés** : Templates avec placeholders dynamiques pour générer des documents sur mesure
- **Injection en masse** : Support du bulk indexing pour des performances optimales
- **Mode continu** : Injection continue de données pour les tests de charge
- **Configuration flexible** : Fichiers YAML, variables d'environnement, ou arguments CLI

## Installation

```bash
# Cloner le repository
git clone https://github.com/E4Itraining/elkinjector.git
cd elkinjector

# Installer avec pip
pip install -e .

# Ou installer les dépendances de développement
pip install -e ".[dev]"
```

## Utilisation rapide

### Vérifier la connexion

```bash
elkinjector check -h localhost -p 9200
```

### Injecter des données

```bash
# Injection basique (logs + métriques)
elkinjector inject -h localhost -p 9200

# Injecter 10000 documents
elkinjector inject -n 10000

# Mode continu avec intervalle de 0.5s
elkinjector inject --continuous -i 0.5

# Seulement les logs
elkinjector inject --logs --no-metrics

# Avec authentification
elkinjector inject -u elastic -P password --scheme https
```

### Générer un fichier de configuration

```bash
elkinjector init-config -o config.yaml
```

### Nettoyer les indices

```bash
elkinjector clean --prefix elkinjector
```

## Configuration

### Fichier YAML

```yaml
elasticsearch:
  host: localhost
  port: 9200
  scheme: http
  username: null
  password: null
  timeout: 30

injection:
  batch_size: 1000
  interval_seconds: 1.0
  total_documents: null
  continuous: false
  index_prefix: elkinjector

logs:
  enabled: true
  index_name: logs
  log_levels: [DEBUG, INFO, WARNING, ERROR, CRITICAL]
  services: [api-gateway, auth-service, user-service]

metrics:
  enabled: true
  index_name: metrics
  metric_types: [cpu, memory, disk, network, request_latency]
  hosts: [server-01, server-02, server-03]

json:
  enabled: false
  index_name: documents
  template: null
  template_file: null
```

### Variables d'environnement

```bash
export ES_HOST=localhost
export ES_PORT=9200
export ES_USERNAME=elastic
export ES_PASSWORD=password
export ES_SCHEME=https
export INJECTION_BATCH_SIZE=500
export INJECTION_INTERVAL=0.5
```

## Templates JSON personnalisés

Créez des documents personnalisés avec des placeholders dynamiques :

```json
{
  "@timestamp": "{{timestamp}}",
  "user": {
    "id": "{{uuid_short}}",
    "name": "{{name}}",
    "email": "{{email}}"
  },
  "event": {
    "type": "{{choice:login,logout,purchase,view}}",
    "value": "{{float:0:1000}}"
  },
  "geo": {
    "ip": "{{ipv4}}",
    "country": "{{country}}",
    "city": "{{city}}"
  }
}
```

### Placeholders disponibles

| Placeholder | Description |
|------------|-------------|
| `{{timestamp}}` | Timestamp UTC actuel |
| `{{uuid}}` | UUID complet |
| `{{uuid_short}}` | UUID court (8 caractères) |
| `{{int:min:max}}` | Entier aléatoire |
| `{{float:min:max}}` | Décimal aléatoire |
| `{{choice:a,b,c}}` | Choix aléatoire |
| `{{name}}` | Nom de personne |
| `{{email}}` | Adresse email |
| `{{ipv4}}` | Adresse IPv4 |
| `{{url}}` | URL |
| `{{country}}` | Pays |
| `{{city}}` | Ville |
| `{{company}}` | Nom d'entreprise |
| `{{sentence}}` | Phrase |
| `{{bool}}` | Booléen |

Voir tous les placeholders : `elkinjector show-placeholders`

## Utilisation programmatique

```python
from elkinjector import Config, DataInjector

# Configuration
config = Config()
config.elasticsearch.host = "localhost"
config.elasticsearch.port = 9200
config.injection.batch_size = 500

# Injection
with DataInjector(config) as injector:
    # Injecter un batch
    success, errors = injector.inject_batch("logs", batch_size=100)

    # Ou lancer l'injection continue
    stats = injector.run(total_documents=10000)
    print(f"Injecté: {stats['total_documents']} documents")
```

### Générateurs individuels

```python
from elkinjector.generators import LogGenerator, MetricsGenerator, JsonGenerator

# Logs
log_gen = LogGenerator()
log_doc = log_gen.generate_one()
log_batch = log_gen.generate_batch(100)

# Métriques
metrics_gen = MetricsGenerator()
metrics_doc = metrics_gen.generate_one()

# JSON personnalisé
json_gen = JsonGenerator()
json_gen.set_template({
    "@timestamp": "{{timestamp}}",
    "user_id": "{{uuid_short}}",
    "action": "{{choice:click,view,purchase}}"
})
custom_doc = json_gen.generate_one()
```

## Structure des indices

Les indices créés suivent le pattern `{prefix}-{type}` :

- `elkinjector-logs` : Logs d'application
- `elkinjector-metrics` : Métriques système
- `elkinjector-documents` : Documents JSON personnalisés

## Développement

```bash
# Installer les dépendances de dev
pip install -e ".[dev]"

# Lancer les tests
pytest

# Formater le code
black elkinjector
ruff check elkinjector
```

## Licence

GPL-3.0 - Voir [LICENSE](LICENSE) pour plus de détails.
