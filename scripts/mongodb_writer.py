from typing import Literal, Dict, Any
from datetime import datetime
import json

def main(
    data: Dict[str, Any],
    collection: Literal["raw_data", "normalized_data", "rejected_data"] = "normalized_data"
):
    """
    Écriture dans MongoDB
    """
    try:
        from pymongo import MongoClient
        
        print("=" * 60)
        print("📥 Données reçues dans mongodb_writer:")
        print(f"  - collection: {collection}")
        print(f"  - Type de data: {type(data)}")
        print(f"  - Clés de data: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        print("=" * 60)
        
        # Connexion à MongoDB
        client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
        db = client["data_pipeline"]
        coll = db[collection]
        
        # Ajout d'horodatage
        document = data.copy() if isinstance(data, dict) else {"data": data}
        document["written_at"] = datetime.now().isoformat()
        document["_collection"] = collection
        
        # Si dedup_key est null ou n'existe pas, générer une clé unique
        if "dedup_key" not in document or not document["dedup_key"]:
            import hashlib
            import json
            # Générer une clé unique basée sur les données + timestamp
            data_string = json.dumps(document, sort_keys=True, default=str)
            unique_string = f"{data_string}_{datetime.now().isoformat()}"
            document["dedup_key"] = hashlib.md5(unique_string.encode()).hexdigest()
            print(f"🔑 Nouvelle dedup_key générée: {document['dedup_key']}")
        
        # Vérifier si un document avec ce dedup_key existe déjà
        existing = coll.find_one({"dedup_key": document["dedup_key"]})
        if existing:
            print(f"⚠️ Document avec dedup_key déjà existant: {document['dedup_key']}")
            print("🔄 Mise à jour du document existant")
            
            # Mettre à jour le document existant
            result = coll.update_one(
                {"dedup_key": document["dedup_key"]},
                {"$set": document}
            )
            
            return {
                "status": "success",
                "inserted_id": str(existing["_id"]),
                "collection": collection,
                "updated": True,
                "step": "mongodb_write"
            }
        
        # Insertion normale
        result = coll.insert_one(document)
        
        print(f"✅ Données insérées dans '{collection}'")
        print(f"  - ID: {result.inserted_id}")
        print(f"  - dedup_key: {document['dedup_key']}")
        print("=" * 60)
        
        return {
            "status": "success",
            "inserted_id": str(result.inserted_id),
            "collection": collection,
            "updated": False,
            "dedup_key": document["dedup_key"],
            "step": "mongodb_write"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "step": "mongodb_write"
        }