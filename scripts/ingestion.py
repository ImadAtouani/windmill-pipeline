import time
from pymongo import MongoClient
from datetime import datetime
import json
import os

def get_cpu_usage():
    """Récupère l'utilisation CPU depuis /proc/stat"""
    try:
        with open('/proc/stat', 'r') as f:
            line = f.readline()
            parts = line.split()
            user = int(parts[1])
            nice = int(parts[2])
            system = int(parts[3])
            idle = int(parts[4])
            total = user + nice + system + idle
            return round(((total - idle) / total) * 100, 2) if total > 0 else 0
    except:
        return 0

def get_memory_mb():
    """Récupère la mémoire utilisée en MB depuis /proc/self/status"""
    try:
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    kb = int(line.split()[1])
                    return round(kb / 1024, 2)
    except:
        return 0

def main(source_type: str = None, source_path: str = None):
    """
    Ingestion - Récupère UNIQUEMENT les données correspondant aux filtres
    """
    start_time = time.time()
    script_name = "ingestion"

    try:
        client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
        db = client["data_pipeline"]

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

            duration_ms = (time.time() - start_time) * 1000
            db.script_metrics.insert_one({
                "script": script_name,
                "duration_ms": duration_ms,
                "status": "error",
                "error": "No pending data found",
                "cpu_percent": get_cpu_usage(),
                "memory_mb": get_memory_mb(),
                "timestamp": datetime.now().isoformat()
            })

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

        duration_ms = (time.time() - start_time) * 1000
        db.script_metrics.insert_one({
            "script": script_name,
            "duration_ms": duration_ms,
            "status": "success",
            "cpu_percent": get_cpu_usage(),
            "memory_mb": get_memory_mb(),
            "timestamp": datetime.now().isoformat()
        })

        return {
            "status": "success",
            "raw_payload": raw_payload,
            "document_id": str(raw_document["_id"]),
            "source_type": raw_document.get("source_type"),
            "source_path": raw_document.get("source_path"),
            "filters_used": query,
            "duration_ms": round(duration_ms, 2),
            "cpu_percent": get_cpu_usage(),
            "memory_mb": get_memory_mb(),
            "step": "ingestion",
        }

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        try:
            client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
            db = client["data_pipeline"]
            db.script_metrics.insert_one({
                "script": script_name,
                "duration_ms": duration_ms,
                "status": "error",
                "error": str(e)[:100],
                "cpu_percent": get_cpu_usage(),
                "memory_mb": get_memory_mb(),
                "timestamp": datetime.now().isoformat()
            })
        except:
            pass

        return {"status": "error", "message": str(e), "step": "ingestion"}