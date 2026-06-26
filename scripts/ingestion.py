def main(source_type: str = None, source_path: str = None):
    """
    Ingestion - Récupère les données depuis MongoDB
    """
    from pymongo import MongoClient
    from datetime import datetime
    import json
    
    # Connexion à MongoDB
    client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
    db = client["data_pipeline"]
    
    # Construire la requête
    query = {}
    if source_type:
        query["source_type"] = source_type
    if source_path:
        query["source_path"] = source_path
    
    # Récupérer les données en attente de traitement
    pending_data = list(db.raw_data.find({"status": "pending"}).limit(1))
    
    if not pending_data:
        return {
            "status": "error",
            "message": "No pending data found in raw_data",
            "step": "ingestion"
        }
    
    # Prendre la première donnée en attente
    raw_document = pending_data[0]
    
    # Extraire les données
    raw_payload = raw_document.get("raw_payload", {})
    raw_payload["ingested_at"] = datetime.now().isoformat()
    raw_payload["source_type"] = raw_document.get("source_type")
    raw_payload["source_path"] = raw_document.get("source_path")
    
    # Marquer comme traité
    db.raw_data.update_one(
        {"_id": raw_document["_id"]},
        {"$set": {"status": "processing"}}
    )
    
    return {
        "status": "success",
        "raw_payload": raw_payload,
        "document_id": str(raw_document["_id"]),
        "source_type": raw_document.get("source_type"),
        "source_path": raw_document.get("source_path"),
        "step": "ingestion"
    }