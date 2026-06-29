# Windmill Pipeline - Orchestration de Normalisation de Données

## 📋 Description

Ce projet implémente un pipeline complet de normalisation de données orchestré par **Windmill**, avec :
- 🔄 Pipeline ETL en 12 étapes (ingestion → enrichissement → métriques)
- 📊 Stockage dans MongoDB (raw / normalized / rejected)
- 📈 Observabilité complète avec OpenTelemetry + Prometheus + Tempo + Grafana

Le pipeline traite des données provenant de multiples sources (CSV, Excel, JSON, HTML, API, Parquet, XML) et les normalise selon un modèle cible défini.

---

## 🏗️ Architecture

```
Sources (externes)
    ↓
[Windmill - Scripts Python] 
    ├── ingestion.py          # Connecteurs sources (CSV, JSON, XML, Excel, Parquet, HTML, API, GraphQL, SQL)
    ├── profiling.py          # Analyse des types, colonnes, valeurs nulles
    ├── parsing.py            # Parsing des formats
    ├── mapping.py            # Mapping source → modèle cible
    ├── cleaning.py           # Nettoyage des données
    ├── typing.py             # Typage des champs
    ├── standardization.py    # Standardisation
    ├── dedup.py              # Déduplication
    ├── validation.py         # Règles métier + schéma
    ├── enrichment.py         # Enrichissement
    ├── mongodb_writer.py     # Écriture MongoDB
    └── send_metrics.py       # Envoi des métriques à l'OTEL Collector
    ↓                    ↓                    ↓
[MongoDB]          [MongoDB]          [MongoDB]
raw_data           normalized_data   rejected_data
    ↓                    ↓                    ↓
[OpenTelemetry Collector]
    ↓                    ↓
[Prometheus]        [Tempo]
(métriques)         (traces)
    ↓                    ↓
[Grafana - Dashboards]
```

### Étapes du Pipeline

| # | Étape | Script | Description |
|---|-------|--------|-------------|
| 1 | **Ingestion** | `ingestion.py` | Connecteurs sources (CSV, JSON, XML, Excel, Parquet, HTML, API, GraphQL, SQL) |
| 2 | **Profilage** | `profiling.py` | Analyse des types, colonnes, valeurs nulles |
| 3 | **Parsing** | `parsing.py` | Parse CSV, Excel, JSON, HTML, Parquet, XML |
| 4 | **Mapping** | `mapping.py` | Mapping champs source → modèle cible |
| 5 | **Nettoyage** | `cleaning.py` | Trim, encodage, formats |
| 6 | **Typage** | `typing.py` | Cast date, nombre, booléen, enum |
| 7 | **Standardisation** | `standardization.py` | Normalisation noms, unités, devises, pays |
| 8 | **Déduplication** | `dedup.py` | Clé métier / hash |
| 9 | **Validation** | `validation.py` | Règles métier + schéma |
| 10 | **Enrichissement** | `enrichment.py` | Métadonnées, source, horodatage |
| 11 | **Écriture** | `mongodb_writer.py` | Sauvegarde dans MongoDB |
| 12 | **Métriques** | `send_metrics.py` | Envoi des métriques à l'OTEL Collector |

---

## 📁 Structure du Projet

```
windmill-pipeline/
│
├── docker-compose.yml          # Orchestration complète
├── .env                        # Variables d'environnement
├── Caddyfile                   # Reverse proxy Windmill
│
├── otel-collector-config.yml   # Configuration OpenTelemetry
├── prometheus.yml              # Configuration Prometheus
├── tempo.yml                   # Configuration Tempo
│
├── data/                       # Fichiers de données sources
│   ├── sales_2024.csv
│   ├── products.json
│   ├── data.xml
│   ├── inventory.xlsx
│   ├── data.parquet
│   └── page.html
│
├── scripts/                    # Scripts du pipeline
│   ├── requirements.txt
│   ├── ingestion.py
│   ├── profiling.py
│   ├── parsing.py
│   ├── mapping.py
│   ├── cleaning.py
│   ├── typing.py
│   ├── standardization.py
│   ├── dedup.py
│   ├── validation.py
│   ├── enrichment.py
│   ├── mongodb_writer.py
│   └── send_metrics.py
│
├── grafana/                    # Configuration Grafana
│   ├── datasources.yml
│   ├── dashboards.yml
│   └── dashboards/
│       └── pipeline_overview.json
│
├── mongo-init/                 # Initialisation MongoDB
│   └── init.js
│
└── README.md
```

---

## 🚀 Installation et Lancement

### Prérequis
- **Docker** & **Docker Compose** (v2.0+)
- **8GB RAM** minimum
- **Ports disponibles** : 80, 27017, 3000, 9090, 3200, 4317, 4319, 55680, 8890

### 1. Créer et préparer le projet

```bash
# Créer le dossier du projet
mkdir windmill-pipeline
cd windmill-pipeline

# Créer les dossiers nécessaires
mkdir -p data scripts grafana/dashboards mongo-init
```

### 2. Configuration des fichiers

Copiez tous les fichiers suivants dans la structure indiquée :
- `docker-compose.yml`
- `.env`
- `Caddyfile`
- `otel-collector-config.yml`
- `prometheus.yml`
- `tempo.yml`
- Les fichiers de données dans `data/`
- Tous les scripts Python dans `scripts/`
- Les fichiers Grafana dans `grafana/`
- Les fichiers MongoDB dans `mongo-init/`

### 3. Lancer le stack complet

```bash
# Démarrer tous les services en arrière-plan
docker-compose up -d

# Vérifier que tous les services sont up
docker-compose ps

# Voir les logs en temps réel
docker-compose logs -f

# Voir les logs d'un service spécifique
docker-compose logs -f windmill_server
docker-compose logs -f mongodb
```

### 4. Vérifier l'état des services

```bash
# Vérifier la santé de chaque service
docker-compose ps
```

**Résultat attendu :**
```
NAME                                STATE    PORTS
windmill-caddy-1                    Up       0.0.0.0:25->25/tcp, 0.0.0.0:80->80/tcp
windmill-db-1                       Up (healthy)   5432/tcp
windmill-grafana-1                  Up       0.0.0.0:3000->3000/tcp
windmill-mongodb-1                  Up (healthy)   0.0.0.0:27017->27017/tcp
windmill-otel_collector-1           Up       0.0.0.0:4317->4317/tcp, 0.0.0.0:4319->4318/tcp, 0.0.0.0:8890->8890/tcp
windmill-prometheus-1               Up       0.0.0.0:9090->9090/tcp
windmill-tempo-1                    Up       0.0.0.0:3200->3200/tcp, 0.0.0.0:55680->55680/tcp
windmill-windmill_extra-1           Up       3000-3003/tcp, 8000/tcp
windmill-windmill_server-1          Up       2525/tcp, 8000/tcp
windmill-windmill_worker-1          Up       8000/tcp
windmill-windmill_worker-2          Up       8000/tcp
windmill-windmill_worker-3          Up       8000/tcp
windmill-windmill_worker_native-1   Up       8000/tcp
```

---

## 🔗 Accès aux Services

| Service | URL | Identifiants |
|---------|-----|--------------|
| **Windmill** | http://localhost | admin@windmill.dev / (configurer lors du premier login) |
| **MongoDB** | mongodb://admin:changeme@localhost:27017 | admin / changeme |
| **Grafana** | http://localhost:3000 | admin / admin |
| **Prometheus** | http://localhost:9090 | - |
| **Tempo** | http://localhost:3200/status | - |
| **OTEL Collector Metrics** | http://localhost:8890/metrics | - |

> **Notes :**
> - **Tempo** n'a pas d'interface web sur la racine (`/`). Utilisez `/status` ou `/ready` pour vérifier l'état du service.
> - **OTEL Collector Metrics** peut être vide au premier lancement. Les métriques apparaîtront après la première exécution du Flow Windmill.

### Premier accès à Windmill

1. Ouvrez http://localhost dans votre navigateur
2. Créez votre compte administrateur
3. Connectez-vous à l'interface

---

## 🧪 Tester le Pipeline

### Vérification de santé des services

```bash
# Tester que tous les services répondent
curl -I http://localhost:8890/metrics   # OTEL Collector (200 OK)
curl http://localhost:3200/status       # Tempo ({"status":"running"})
curl http://localhost:3200/ready        # Tempo (ready)
curl http://localhost:9090/api/v1/query?query=up  # Prometheus
curl http://localhost:3000              # Grafana
```

### Méthode 1 : Via l'interface Windmill (Recommandé)

#### Étape 1 : Créer un Flow

1. Connectez-vous à Windmill (http://localhost)
2. Dans le menu, allez dans **"Flows"** → **"Create Flow"**
3. Nommez votre flow : `Pipeline Normalisation`
4. Ajoutez les scripts dans l'ordre suivant :

```
1. ingestion
2. profiling
3. parsing
4. mapping
5. cleaning
6. typing
7. standardization
8. dedup
9. validation
10. enrichment
11. mongodb_writer
12. send_metrics
```

#### Étape 2 : Configurer les branches conditionnelles

1. Après l'étape `validation`, ajoutez une **branch conditionnelle**
2. **Condition** : `result.status == "valid"`
   - **True** → `mongodb_writer` avec `collection="normalized_data"`
   - **False** → `mongodb_writer` avec `collection="rejected_data"`

#### Étape 3 : Input Schema du Flow

```json
{
  "type": "object",
  "properties": {
    "source_type": {
      "type": "string",
      "description": "Type de source de données",
      "enum": ["csv", "json", "xml", "excel", "parquet", "html", "api", "graphql", "sql"],
      "default": "csv"
    },
    "source_path": {
      "type": "string",
      "description": "Chemin du fichier, URL de l'API, ou chaîne de connexion SQL",
      "default": "/data/sales_2024.csv"
    },
    "method": {
      "type": "string",
      "description": "Méthode HTTP pour API REST",
      "enum": ["GET", "POST", "PUT", "DELETE"],
      "default": "GET"
    },
    "headers": {
      "type": "string",
      "description": "Headers HTTP (format JSON)",
      "default": "{}"
    },
    "params": {
      "type": "string",
      "description": "Paramètres de requête (format JSON)",
      "default": "{}"
    },
    "data": {
      "type": "string",
      "description": "Corps de la requête (format JSON) pour API POST/PUT",
      "default": "{}"
    },
    "query": {
      "type": "string",
      "description": "Requête GraphQL ou SQL",
      "default": ""
    },
    "variables": {
      "type": "string",
      "description": "Variables GraphQL (format JSON)",
      "default": "{}"
    }
  },
  "required": ["source_type", "source_path"]
}
```

#### Étape 4 : Exécuter le Flow avec différents inputs

| Source | Input JSON |
|--------|------------|
| **CSV** | `{"source_type":"csv","source_path":"/data/sales_2024.csv"}` |
| **JSON** | `{"source_type":"json","source_path":"/data/products.json"}` |
| **XML** | `{"source_type":"xml","source_path":"/data/data.xml"}` |
| **Excel** | `{"source_type":"excel","source_path":"/data/inventory.xlsx"}` |
| **Parquet** | `{"source_type":"parquet","source_path":"/data/data.parquet"}` |
| **HTML** | `{"source_type":"html","source_path":"/data/page.html"}` |
| **API GET** | `{"source_type":"api","source_path":"https://jsonplaceholder.typicode.com/users/1","method":"GET"}` |
| **API GET avec params** | `{"source_type":"api","source_path":"https://jsonplaceholder.typicode.com/posts","method":"GET","params":"{\"userId\":1}"}` |
| **API POST** | `{"source_type":"api","source_path":"https://jsonplaceholder.typicode.com/posts","method":"POST","headers":"{\"Content-Type\":\"application/json\"}","data":"{\"title\":\"Test\",\"body\":\"Test content\",\"userId\":1}"}` |
| **GraphQL** | `{"source_type":"graphql","source_path":"https://rickandmortyapi.com/graphql","query":"query { characters(page:1) { results { id name status species } } }"}` |
| **SQL** | `{"source_type":"sql","source_path":"postgresql://user:password@localhost:5432/mydb","query":"SELECT * FROM users LIMIT 5"}` |

#### Étape 5 : Vérifier les résultats

```bash
# Connexion à MongoDB
docker exec -it windmill-mongodb-1 mongosh -u admin -p changeme

# Dans le shell MongoDB
use data_pipeline

# Voir les données brutes
db.raw_data.find().pretty()

# Voir les données normalisées
db.normalized_data.find().pretty()

# Voir les données rejetées
db.rejected_data.find().pretty()
```

#### Étape 6 : Vérifier les métriques

```bash
# Voir les métriques du pipeline
curl -s http://localhost:8890/metrics | grep "pipeline"

# Résultat attendu :
# windmill_pipeline_raw_data_total_ratio 5
# windmill_pipeline_normalized_data_total_ratio 5
# windmill_pipeline_rejected_data_total_ratio 0
# windmill_pipeline_raw_pending_total_ratio 0
# windmill_pipeline_raw_processing_total_ratio 0
# windmill_pipeline_raw_by_source_ratio{source_type="api"} 1
# windmill_pipeline_raw_by_source_ratio{source_type="csv"} 1
# windmill_pipeline_raw_by_source_ratio{source_type="excel"} 1
# windmill_pipeline_raw_by_source_ratio{source_type="html"} 1
# windmill_pipeline_raw_by_source_ratio{source_type="json"} 1
# windmill_pipeline_latency_last_milliseconds{script="ingestion"} 13.92
# windmill_pipeline_cpu_percent{script="ingestion"} 6.64
# windmill_pipeline_memory_mb_MB{script="ingestion"} 28.86
# windmill_pipeline_error_rate_percent{script="ingestion"} 0
```

### Méthode 2 : Avec les données de test

```bash
# Réinsérer les données de test
docker exec -it windmill-mongodb-1 mongosh -u admin -p changeme --eval '
use data_pipeline;

db.raw_data.insertMany([
    {
        source_type: "csv",
        source_path: "/data/sales_2024.csv",
        ingested_at: new Date(),
        step: "ingestion",
        raw_payload: {
            data: {
                id: "001",
                name: "John Doe",
                amount: "1250.50",
                date: "2024-01-15",
                country: "FR",
                email: "john.doe@example.com"
            }
        },
        status: "pending"
    },
    {
        source_type: "json",
        source_path: "/data/products.json",
        ingested_at: new Date(),
        step: "ingestion",
        raw_payload: {
            data: {
                id: "P001",
                name: "Laptop Pro",
                price: 1299.99,
                category: "Electronics",
                stock: 45,
                supplier: "TechCorp",
                date: "2024-06-01",
                country: "US",
                email: "contact@techcorp.com"
            }
        },
        status: "pending"
    },
    {
        source_type: "xml",
        source_path: "/data/data.xml",
        ingested_at: new Date(),
        step: "ingestion",
        raw_payload: {
            data: {
                id: "E001",
                name: "Marie Dupont",
                position: "Data Engineer",
                salary: "45000.00",
                department: "IT",
                hire_date: "2023-09-01",
                country: "FR",
                email: "marie.dupont@company.com"
            }
        },
        status: "pending"
    },
    {
        source_type: "excel",
        source_path: "/data/inventory.xlsx",
        ingested_at: new Date(),
        step: "ingestion",
        raw_payload: {
            data: {
                product_id: "INV001",
                product_name: "Office Chair",
                quantity: 150,
                price: 89.99,
                category: "Furniture",
                supplier: "Ergonomics Inc",
                last_restock: "2024-05-15"
            }
        },
        status: "pending"
    },
    {
        source_type: "html",
        source_path: "/data/page.html",
        ingested_at: new Date(),
        step: "ingestion",
        raw_payload: {
            data: {
                titles: ["Electronics Store"],
                paragraphs: ["Welcome to our electronics store."],
                tables: [
                    ["Product", "Price", "Stock"],
                    ["Laptop Pro", "$1,299.99", "45"]
                ]
            }
        },
        status: "pending"
    }
]);

print("✅ Données de test insérées: " + db.raw_data.count() + " documents");
'
```

---

## 📊 Observabilité

### Métriques disponibles

| Métrique | Description | Unité |
|----------|-------------|-------|
| `windmill_pipeline_raw_data_total_ratio` | Nombre total de données brutes | 1 |
| `windmill_pipeline_normalized_data_total_ratio` | Nombre total de données normalisées | 1 |
| `windmill_pipeline_rejected_data_total_ratio` | Nombre total de données rejetées | 1 |
| `windmill_pipeline_raw_by_source_ratio` | Répartition des données par source | 1 |
| `windmill_pipeline_latency_last_milliseconds` | Dernière durée d'exécution par script | ms |
| `windmill_pipeline_latency_avg_milliseconds` | Durée moyenne d'exécution par script | ms |
| `windmill_pipeline_cpu_percent` | CPU par script | % |
| `windmill_pipeline_cpu_avg_percent` | CPU moyenne par script | % |
| `windmill_pipeline_memory_mb_MB` | Mémoire par script | MB |
| `windmill_pipeline_memory_avg_MB` | Mémoire moyenne par script | MB |
| `windmill_pipeline_errors_total_ratio` | Nombre d'erreurs par script | 1 |
| `windmill_pipeline_success_total_ratio` | Nombre de succès par script | 1 |
| `windmill_pipeline_error_rate_percent` | Taux d'erreur par script | % |

### Dashboards Grafana

1. Connectez-vous à Grafana (http://localhost:3000)
   - User: `admin`
   - Password: `admin`

2. Allez dans **"Dashboards"** → **"Browse"**
3. Sélectionnez **"Pipeline de Normalisation - Vue Globale"**

Le dashboard affiche :
- **Statistiques** : Données brutes, normalisées, rejetées
- **Évolution des données** : Graphique temporel des 3 métriques principales
- **Répartition par source** : Diagramme circulaire des sources de données
- **Latence par tâche** : Dernière exécution et moyenne
- **Taux d'erreur** : Par script
- **CPU par tâche** : Utilisation CPU par script
- **Mémoire par tâche** : Utilisation mémoire par script

---

## 🧪 Tester l'Observabilité

### Tester l'OTEL Collector

```bash
# Voir toutes les métriques
curl -s http://localhost:8890/metrics | grep "pipeline"

# Métriques de comptage
curl -s http://localhost:8890/metrics | grep "_data_total_ratio"

# Métriques de latence
curl -s http://localhost:8890/metrics | grep "latency"

# Métriques CPU
curl -s http://localhost:8890/metrics | grep "cpu"

# Métriques Mémoire
curl -s http://localhost:8890/metrics | grep "memory"

# Métriques d'erreurs
curl -s http://localhost:8890/metrics | grep "error"
```

### Tester Prometheus

```bash
# Données brutes
curl -s 'http://localhost:9090/api/v1/query?query=windmill_pipeline_raw_data_total_ratio'

# Données normalisées
curl -s 'http://localhost:9090/api/v1/query?query=windmill_pipeline_normalized_data_total_ratio'

# Données rejetées
curl -s 'http://localhost:9090/api/v1/query?query=windmill_pipeline_rejected_data_total_ratio'

# Latence
curl -s 'http://localhost:9090/api/v1/query?query=windmill_pipeline_latency_last_milliseconds'

# CPU
curl -s 'http://localhost:9090/api/v1/query?query=windmill_pipeline_cpu_percent'

# Mémoire
curl -s 'http://localhost:9090/api/v1/query?query=windmill_pipeline_memory_mb_MB'

# Taux d'erreur
curl -s 'http://localhost:9090/api/v1/query?query=windmill_pipeline_error_rate_percent'
```

**Dans le navigateur :** http://localhost:9090
- Aller dans **"Graph"** → rechercher les métriques
- Aller dans **"Targets"** → vérifier que tous sont **UP**

### Tester Tempo

```bash
# Vérifier l'état
curl -s http://localhost:3200/status
# Résultat : {"status":"running"}

# Vérifier le ready
curl -s http://localhost:3200/ready
# Résultat : ready
```

**Dans le navigateur :** http://localhost:3200/status

### Tester Grafana

1. Ouvrir http://localhost:3000
2. User: `admin` / Password: `admin`
3. Menu → **"Data Sources"** → Vérifier Prometheus et Tempo
4. Menu → **"Explore"** → Tester les requêtes
5. Menu → **"Dashboards"** → **"Pipeline de Normalisation - Vue Globale"**

---

## 🔧 Personnalisation du Pipeline

### Ajouter une nouvelle source de données

Modifier `scripts/ingestion.py` :
```python
def read_new_format_file(file_path):
    """Lit un nouveau format de fichier"""
    # Implémentation
    return data

# Ajouter dans read_data_from_source()
elif source_type == 'new_format':
    return read_new_format_file(actual_path)
```

### Modifier les règles de validation

Éditer `scripts/validation.py` :

```python
def main(deduplicated_data: dict):
    errors = []
    
    # Règle 1 : Champ obligatoire
    if "user_id" not in deduplicated_data:
        errors.append("Missing required field: user_id")
    
    # Règle 2 : Plage de valeurs
    if "amount" in deduplicated_data:
        if deduplicated_data["amount"] < 0:
            errors.append("Amount must be positive")
        if deduplicated_data["amount"] > 100000:
            errors.append("Amount exceeds maximum limit")
    
    # Règle 3 : Format email
    if "email" in deduplicated_data:
        if "@" not in deduplicated_data["email"]:
            errors.append("Invalid email format")
    
    is_valid = len(errors) == 0
    
    return {
        "status": "valid" if is_valid else "rejected",
        "validated_data": deduplicated_data if is_valid else None,
        "errors": errors,
        "step": "validation"
    }
```

---

## 🐛 Dépannage

### Windmill ne démarre pas

```bash
# Vérifier les logs
docker-compose logs windmill_server

# Vérifier que PostgreSQL est healthy
docker-compose ps db

# Redémarrer PostgreSQL si nécessaire
docker-compose restart db
```

### MongoDB connexion refusée

```bash
# Vérifier que MongoDB est démarré
docker-compose ps mongodb

# Vérifier les logs
docker-compose logs mongodb

# Vérifier les identifiants dans mongodb_writer.py
```

### Aucune métrique dans l'OTEL Collector

```bash
# 1. Vérifier que send_metrics.py est bien dans le Flow
# 2. Réexécuter le Flow
# 3. Vérifier les métriques
curl -s http://localhost:8890/metrics | grep "pipeline"
```

### Fichier non trouvé dans /data/

```bash
# Copier les fichiers dans le conteneur
docker cp data/. windmill-windmill_server-1:/data/

# Vérifier
docker exec -it windmill-windmill_server-1 ls -la /data/
```

### Nettoyer les données et recommencer

```bash
# Nettoyer MongoDB
docker exec -it windmill-mongodb-1 mongosh -u admin -p changeme --eval '
use data_pipeline;
db.raw_data.deleteMany({});
db.normalized_data.deleteMany({});
db.rejected_data.deleteMany({});
db.script_metrics.deleteMany({});
print("✅ Nettoyé");
'
```

### Problèmes de ports

```bash
# Voir les ports occupés
netstat -ano | findstr "4317 4318 4319 8890 9090 3000 3200 55680"

# Relancer proprement
docker-compose down && docker-compose up -d
```

---

## 📊 Commandes Utiles

### Gestion des conteneurs

```bash
# Démarrer tous les services
docker-compose up -d

# Arrêter tous les services
docker-compose down

# Redémarrer un service
docker-compose restart windmill_server

# Voir les logs d'un service
docker-compose logs -f mongodb
```

### Base de données

```bash
# Connexion à MongoDB
docker exec -it windmill-mongodb-1 mongosh -u admin -p changeme

use data_pipeline
show collections

# Compter les documents
db.raw_data.count()
db.normalized_data.count()
db.rejected_data.count()
db.script_metrics.count()
```

### Observabilité

```bash
# Voir les métriques OpenTelemetry
curl -s http://localhost:8890/metrics | grep "pipeline"

# Voir les métriques Prometheus
curl -s 'http://localhost:9090/api/v1/query?query=windmill_pipeline_raw_data_total_ratio'

# Vérifier l'état de Tempo
curl -s http://localhost:3200/status
curl -s http://localhost:3200/ready

# Supprimer les métriques Prometheus
curl -X POST -g 'http://localhost:9090/api/v1/admin/tsdb/delete_series?match[]={__name__=~"windmill_pipeline.*"}'
curl -X POST 'http://localhost:9090/api/v1/admin/tsdb/clean_tombstones'
```

### Nettoyage complet des données

```bash
docker exec -it windmill-mongodb-1 mongosh -u admin -p changeme --eval '
use data_pipeline;
db.raw_data.deleteMany({});
db.normalized_data.deleteMany({});
db.rejected_data.deleteMany({});
db.script_metrics.deleteMany({});
db.resource_metrics.deleteMany({});
print("✅ Toutes les données supprimées");
'
```

---

## 📦 Dépendances

### Versions des images Docker

| Service | Image | Version |
|---------|-------|---------|
| Windmill | `ghcr.io/windmill-labs/windmill` | main |
| PostgreSQL | `postgres` | 16 |
| MongoDB | `mongo` | 7 |
| OpenTelemetry Collector | `otel/opentelemetry-collector-contrib` | latest |
| Prometheus | `prom/prometheus` | latest |
| Tempo | `grafana/tempo` | latest |
| Grafana | `grafana/grafana` | latest |

### Dépendances Python

```txt
pymongo==4.6.1
python-dateutil==2.8.2
pandas==2.2.0
openpyxl==3.1.2
requests==2.31.0
beautifulsoup4==4.12.2
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pyarrow==14.0.1
```

---

## 📊 Tableau des Ports

| Service | Port Externe | Port Interne | Usage |
|---------|--------------|--------------|-------|
| Windmill | 80 | 80 | Interface Web |
| MongoDB | 27017 | 27017 | Base de données |
| Grafana | 3000 | 3000 | Interface Grafana |
| Prometheus | 9090 | 9090 | Interface Prometheus |
| OTEL Collector gRPC | 4317 | 4317 | Réception OTLP gRPC |
| OTEL Collector HTTP | 4319 | 4318 | Réception OTLP HTTP |
| OTEL Collector Metrics | 8890 | 8890 | Exposition métriques |
| Tempo UI | 3200 | 3200 | Interface Tempo |
| Tempo OTLP | 55680 | 55680 | Réception OTLP gRPC |

---

## 📚 Documentation Liée

- [Windmill Documentation](https://www.windmill.dev/docs)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Tempo Documentation](https://grafana.com/docs/tempo/latest/)

---

## 📄 Licence

MIT

---

## 🔄 Historique des Versions

| Version | Date | Description |
|---------|------|-------------|
| v1.0.0 | 2026-06-29 | Version finale |
| | | - Pipeline 12 étapes complet |
| | | - Support CSV, JSON, XML, Excel, Parquet, HTML, API, GraphQL, SQL |
| | | - MongoDB multi-collections (raw/normalized/rejected) |
| | | - Stack OTEL + Prometheus + Tempo + Grafana |
| | | - Dashboard Grafana complet avec toutes les métriques |
| | | - Données de test intégrées dans dossier `data/` |
| | | - Métriques de latence, CPU, Mémoire, Erreurs |
| | | - Ports optimisés : OTEL Metrics sur 8890, Tempo sur 55680 |
| | | - Métriques personnalisées via `send_metrics.py` |

---

## 💡 Bonnes Pratiques

1. **Sécurité** : Changez les mots de passe par défaut dans `.env` et `docker-compose.yml`
2. **Performances** : Ajustez les ressources CPU/Mémoire dans `docker-compose.yml`
3. **Logs** : Configurez la rotation des logs via les variables d'environnement
4. **Backup** : Sauvegardez régulièrement les volumes Docker
5. **Monitoring** : Utilisez les dashboards Grafana pour surveiller la santé du pipeline
6. **Tests** : Après chaque modification, exécutez le pipeline et vérifiez les métriques

---

**Prêt à utiliser !** 🚀 Lancez `docker-compose up -d` et commencez à orchestrer vos données avec Windmill.