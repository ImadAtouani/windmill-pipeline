import time
import json
import os
from typing import Literal, Dict, Any
from datetime import datetime
from pymongo import MongoClient

def get_cpu_usage():
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
    try:
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    kb = int(line.split()[1])
                    return round(kb / 1024, 2)
    except:
        return 0


def normalize_records(data):
    if isinstance(data, list):
        return [item if isinstance(item, dict) else {"data": item} for item in data], True
    if isinstance(data, dict):
        return [data], False
    return [{"data": data}], False


def write_document(collection, document):
    document_to_write = document.copy() if isinstance(document, dict) else {"data": document}
    document_to_write["written_at"] = datetime.now().isoformat()
    document_to_write["_collection"] = collection.name

    if "dedup_key" not in document_to_write or not document_to_write["dedup_key"]:
        import hashlib
        data_string = json.dumps(document_to_write, sort_keys=True, default=str)
        unique_string = f"{data_string}_{datetime.now().isoformat()}"
        document_to_write["dedup_key"] = hashlib.md5(unique_string.encode()).hexdigest()

    existing = collection.find_one({"dedup_key": document_to_write["dedup_key"]})
    if existing:
        collection.update_one({"dedup_key": document_to_write["dedup_key"]}, {"$set": document_to_write})
        return {"inserted_id": str(existing["_id"]), "updated": True, "dedup_key": document_to_write["dedup_key"]}

    result = collection.insert_one(document_to_write)
    return {"inserted_id": str(result.inserted_id), "updated": False, "dedup_key": document_to_write["dedup_key"]}

def main(
    data: Dict[str, Any],
    collection: Literal["raw_data", "normalized_data", "rejected_data"] = "normalized_data"
):
    """
    Écriture dans MongoDB
    """
    start_time = time.time()
    script_name = "mongodb_writer"
    
    try:
        print("=" * 60)
        print("📥 Données reçues dans mongodb_writer:")
        print(f"  - collection: {collection}")
        print(f"  - Type de data: {type(data)}")
        print(f"  - Clés de data: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        print("=" * 60)
        
        record_list, was_list = normalize_records(data)

        client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
        db = client["data_pipeline"]
        coll = db[collection]

        results = [write_document(coll, record) for record in record_list]
        if len(results) == 1:
            print(f"✅ Données insérées dans '{collection}'")
            print(f"  - ID: {results[0]['inserted_id']}")
            print(f"  - dedup_key: {results[0]['dedup_key']}")
        else:
            print(f"✅ {len(results)} documents traités dans '{collection}'")
        print("=" * 60)
        
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
            "inserted_id": results[0]["inserted_id"] if results else None,
            "inserted_ids": [result["inserted_id"] for result in results],
            "collection": collection,
            "updated": results[0]["updated"] if results else False,
            "dedup_key": results[0]["dedup_key"] if results else None,
            "record_count": len(record_list),
            "duration_ms": round(duration_ms, 2),
            "cpu_percent": get_cpu_usage(),
            "memory_mb": get_memory_mb(),
            "step": "mongodb_write"
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
        return {
            "status": "error",
            "message": str(e),
            "step": "mongodb_write"
        }