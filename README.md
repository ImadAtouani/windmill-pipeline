# Windmill Pipeline - Orchestration de Normalisation de Données

## 📋 Description

Ce projet implémente un pipeline complet de normalisation de données orchestré par **Windmill**, avec :
- 🔄 Pipeline ETL en 12 étapes (ingestion → enrichissement → métriques)
- 📊 Stockage dans MongoDB (raw / normalized / rejected)
- 📈 Observabilité complète avec OpenTelemetry + Prometheus + Tempo + Grafana

Le pipeline traite des données provenant de multiples sources (CSV, Excel, JSON, HTML, API, Parquet) et les normalise selon un modèle cible défini.

---

## 🏗️ Architecture

```
Sources (externes)
    ↓
[Windmill - Scripts Python] 
    ├── ingestion.py          # Connecteurs sources
    ├── profiling.py          # Analyse des données
    ├── parsing.py            # Parsing des formats
    ├── mapping.py            # Mapping source → cible
    ├── cleaning.py           # Nettoyage des données
    ├── typing.py             # Typage des champs
    ├── standardization.py    # Standardisation
    ├── dedup.py              # Déduplication
    ├── validation.py         # Règles métier
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
| 1 | **Ingestion** | `ingestion.py` | Connecteurs sources (API, CSV, Excel, JSON, HTML, Parquet) |
| 2 | **Profilage** | `profiling.py` | Analyse des types, colonnes, valeurs nulles |
| 3 | **Parsing** | `parsing.py` | Parse CSV, Excel, JSON, HTML, Parquet |
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
│   ├── init.js
│   └── seed_test_data.js
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
mkdir -p scripts grafana/dashboards mongo-init
```

### 2. Configuration des fichiers

Copiez tous les fichiers suivants dans la structure indiquée :
- `docker-compose.yml`
- `.env`
- `Caddyfile`
- `otel-collector-config.yml`
- `prometheus.yml`
- `tempo.yml`
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

#### Étape 3 : Exécuter le Flow

1. Cliquez sur **"Run"**
2. Entrez les paramètres :
   ```json
   {
     "source_type": "csv",
     "source_path": "/data/sales_2024.csv",
     "format": "csv"
   }
   ```
3. Cliquez sur **"Run Now"**
4. Observez l'exécution en temps réel

#### Étape 4 : Vérifier les résultats

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

#### Étape 5 : Vérifier les métriques

```bash
# Voir les métriques du pipeline
curl http://localhost:8890/metrics | grep "windmill_pipeline"

# Résultat attendu :
# windmill_pipeline_raw_data_total_ratio 5
# windmill_pipeline_normalized_data_total_ratio 5
# windmill_pipeline_rejected_data_total_ratio 0
# windmill_pipeline_raw_pending_total_ratio 0
# windmill_pipeline_raw_processing_total_ratio 5
# windmill_pipeline_raw_by_source_ratio{source_type="api"} 1
# windmill_pipeline_raw_by_source_ratio{source_type="csv"} 1
# windmill_pipeline_raw_by_source_ratio{source_type="excel"} 1
# windmill_pipeline_raw_by_source_ratio{source_type="html"} 1
# windmill_pipeline_raw_by_source_ratio{source_type="json"} 1
```

### Méthode 2 : Avec les données de test

Les données de test ont été automatiquement insérées dans MongoDB lors du premier démarrage :

```javascript
// Voir les données de test
db.raw_data.find({ "status": "pending" }).pretty()
```

---

## 📊 Observabilité

### Métriques disponibles

| Métrique | Description |
|----------|-------------|
| `windmill_pipeline_raw_data_total_ratio` | Nombre total de données brutes |
| `windmill_pipeline_normalized_data_total_ratio` | Nombre total de données normalisées |
| `windmill_pipeline_rejected_data_total_ratio` | Nombre total de données rejetées |
| `windmill_pipeline_raw_pending_total_ratio` | Nombre de données en attente |
| `windmill_pipeline_raw_processing_total_ratio` | Nombre de données en traitement |
| `windmill_pipeline_raw_by_source_ratio` | Répartition des données par source |

### Dashboards Grafana

1. Connectez-vous à Grafana (http://localhost:3000)
   - User: `admin`
   - Password: `admin`

2. Allez dans **"Dashboards"** → **"Browse"**
3. Sélectionnez **"Pipeline de Normalisation - Vue Globale"**

Le dashboard affiche :
- **Statistiques** : Données brutes, normalisées, rejetées, en attente, en traitement
- **Évolution des données** : Graphique temporel des 3 métriques principales
- **Répartition par source** : Diagramme circulaire des sources de données

---

## 🔧 Personnalisation du Pipeline

### Ajouter une nouvelle source de données

1. Modifier `scripts/ingestion.py` :
   ```python
   def main(source_type: str, source_path: str):
       if source_type == "parquet":
           import pandas as pd
           df = pd.read_parquet(source_path)
           # ...
   ```

2. Mettre à jour `scripts/parsing.py` :
   ```python
   def main(raw_data: Dict[str, Any], format: Literal["csv", "excel", "json", "html", "parquet"] = "json"):
       if format == "parquet":
           # Ajouter le parsing Parquet
           # ...
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
curl http://localhost:8890/metrics | grep "windmill_pipeline"
```

### Problèmes de ports

```bash
# Voir les ports occupés
netstat -ano | findstr "4317 4318 4319 8890 9090 3000 3200 55680"

# Relancer proprement
docker-compose down && docker-compose up -d
```

### Volume "file exists" error

```bash
# Cette erreur n'est pas bloquante. Si vous voulez la résoudre :
docker-compose down -v
docker volume rm windmill_worker_dependency_cache 2>/dev/null || true
docker-compose up -d
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
```

### Observabilité

```bash
# Voir les métriques OpenTelemetry
curl http://localhost:8890/metrics | grep "windmill_pipeline"

# Voir les métriques Prometheus
curl 'http://localhost:9090/api/v1/query?query=windmill_pipeline_raw_data_total_ratio'

# Vérifier l'état de Tempo
curl http://localhost:3200/status
curl http://localhost:3200/ready
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
| v1.0.0 | 2026-06-25 | Version initiale |
| | | - Pipeline 12 étapes complet |
| | | - MongoDB multi-collections (raw/normalized/rejected) |
| | | - Stack OTEL + Prometheus + Tempo + Grafana |
| | | - Dashboard Grafana prêt à l'emploi |
| | | - Données de test intégrées |
| | | - Ports optimisés : OTEL Metrics sur 8890, Tempo sur 55680 |
| | | - Métriques personnalisées via `send_metrics.py` |

---

## 💡 Bonnes Pratiques

1. **Sécurité** : Changez les mots de passe par défaut dans `.env` et `docker-compose.yml`
2. **Performances** : Ajustez les ressources CPU/Mémoire dans `docker-compose.yml`
3. **Logs** : Configurez la rotation des logs via les variables d'environnement
4. **Backup** : Sauvegardez régulièrement les volumes Docker
5. **Monitoring** : Utilisez les dashboards Grafana pour surveiller la santé du pipeline

---

**Prêt à utiliser !** 🚀 Lancez `docker-compose up -d` et commencez à orchestrer vos données avec Windmill.