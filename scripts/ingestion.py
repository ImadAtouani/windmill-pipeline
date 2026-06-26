from pymongo import MongoClient
from datetime import datetime
import json


def main(source_type: str = None, source_path: str = None):
    """
    Ingestion - Récupère UNIQUEMENT les données correspondant aux filtres
    """

    try:
        # Connexion à MongoDB
        client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
        db = client["data_pipeline"]

        # --- Construire la requête ---
        query = {"status": "pending"}

        if source_type:
            query["source_type"] = source_type
        if source_path:
            query["source_path"] = source_path

        print(f"🔍 Filtres appliqués: {json.dumps(query, indent=2)}")

        pending_data = list(db.raw_data.find(query).limit(1))

        if not pending_data:
            stats = list(
                db.raw_data.aggregate(
                    [
                        {"$match": {"status": "pending"}},
                        {"$group": {"_id": "$source_type", "count": {"$sum": 1}}},
                    ]
                )
            )
            available = ", ".join([f"{s['_id']}: {s['count']}" for s in stats])

            return {
                "status": "error",
                "message": f"No pending data found with filters: {query}",
                "available_data": available or "No pending data at all",
                "filters_used": query,
                "step": "ingestion",
            }

        raw_document = pending_data[0]

        raw_payload = raw_document.get("raw_payload", {})
        raw_payload["ingested_at"] = datetime.now().isoformat()
        raw_payload["source_type"] = raw_document.get("source_type")
        raw_payload["source_path"] = raw_document.get("source_path")

        db.raw_data.update_one(
            {"_id": raw_document["_id"]}, {"$set": {"status": "processing"}}
        )

        return {
            "status": "success",
            "raw_payload": raw_payload,
            "document_id": str(raw_document["_id"]),
            "source_type": raw_document.get("source_type"),
            "source_path": raw_document.get("source_path"),
            "filters_used": query,
            "step": "ingestion",
        }

    except Exception as e:
        return {"status": "error", "message": str(e), "step": "ingestion"}