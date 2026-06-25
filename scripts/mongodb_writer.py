from typing import Literal, Dict, Any

def main(
    data: Dict[str, Any],
    collection: Literal["raw_data", "normalized_data", "rejected_data"] = "normalized_data"
):
    """
    Écriture dans MongoDB
    """
    from pymongo import MongoClient
    from datetime import datetime
    
    # Connexion à MongoDB
    client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
    db = client["data_pipeline"]
    coll = db[collection]
    
    # Ajout d'horodatage
    document = data.copy()
    document["written_at"] = datetime.now().isoformat()
    
    # Insertion
    result = coll.insert_one(document)
    
    return {
        "status": "success",
        "inserted_id": str(result.inserted_id),
        "collection": collection,
        "step": "mongodb_write"
    }