// Création de la base de données
db = db.getSiblingDB('data_pipeline');

// Création des collections
db.createCollection('raw_data');
db.createCollection('normalized_data');
db.createCollection('rejected_data');

// Création des index pour raw_data
db.raw_data.createIndex({ "ingested_at": -1 });
db.raw_data.createIndex({ "source_type": 1 });
db.raw_data.createIndex({ "source_path": 1 });
db.raw_data.createIndex({ "step": 1 });

// Création des index pour normalized_data
db.normalized_data.createIndex({ "enriched_at": -1 });
db.normalized_data.createIndex({ "source_system": 1 });
db.normalized_data.createIndex({ "pipeline_version": 1 });
db.normalized_data.createIndex({ "dedup_key": 1 }, { unique: true });

// Création des index pour rejected_data
db.rejected_data.createIndex({ "ingested_at": -1 });
db.rejected_data.createIndex({ "step": 1 });
db.rejected_data.createIndex({ "errors": 1 });

// Création d'un utilisateur pour l'application
db.createUser({
    user: "app_user",
    pwd: "app_password",
    roles: [
        { role: "readWrite", db: "data_pipeline" }
    ]
});

// Création d'un utilisateur pour l'observabilité (lecture seule)
db.createUser({
    user: "monitoring_user",
    pwd: "monitoring_password",
    roles: [
        { role: "read", db: "data_pipeline" }
    ]
});

print("✅ MongoDB initialisé avec succès !");
print("📊 Collections créées : raw_data, normalized_data, rejected_data");
print("👤 Utilisateurs créés : app_user, monitoring_user");