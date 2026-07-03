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


_RECORD_LIST_KEYS = [
    "rejected_data",
    "validated_data",
    "standardized_data",
    "deduplicated_data",
    "cleaned_data",
    "typed_data",
    "mapped_data",
    "parsed_data",
    "enriched_data",
    "records",
    "data",
]


def _maybe_parse_json(data):
    """If data is a JSON-encoded string/bytes, parse it. Otherwise return as-is."""
    if data is None:
        return None
        
    if isinstance(data, bytes):
        try:
            data = data.decode("utf-8")
        except Exception:
            return data

    if isinstance(data, str):
        stripped = data.strip()
        if stripped[:1] in ("{", "["):
            try:
                return json.loads(stripped)
            except (json.JSONDecodeError, ValueError):
                return data

    return data


def _find_record_list(data, depth=0, max_depth=4):
    """Recursively search a (possibly nested) dict for a known record-list key."""
    if not isinstance(data, dict) or depth > max_depth:
        return None

    # 1) Direct match at this level.
    for key in _RECORD_LIST_KEYS:
        value = data.get(key)
        if isinstance(value, list) and value:
            return value
        if isinstance(value, dict) and key in ("data", "records"):
            return [value]

    # 2) Recurse into nested dict values
    for value in data.values():
        if isinstance(value, dict):
            found = _find_record_list(value, depth + 1, max_depth)
            if found is not None:
                return found

    return None


def extract_records(data):
    """Extract a batch of records from common wrapper shapes."""
    if data is None:
        return []
        
    data = _maybe_parse_json(data)
    
    if data is None:
        return []

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        found = _find_record_list(data)
        if found is not None:
            return found
        
        # Si c'est un dictionnaire qui pourrait être un seul enregistrement
        # mais éviter les métadonnées de table
        table_keys = ["table_name", "table_schema", "table_catalog", "table_type"]
        if any(key in data for key in table_keys):
            return []
            
        return [data]

    return [{"value": data}]


def normalize_records(data):
    records = extract_records(data)
    if not records:
        return [], False
    return [item if isinstance(item, dict) else {"data": item} for item in records], isinstance(records, list)


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
    data: Dict[str, Any] = None,
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
        
        # Vérifier si data est None
        if data is None:
            print("❌ ERREUR: data est None!")
            print("=" * 60)
            return {
                "status": "error",
                "message": "data is None - no data received from previous step",
                "step": "mongodb_write"
            }
            
        print(f"  - Clés de data: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        
        # Afficher le contenu des clés importantes
        if isinstance(data, dict):
            for key in ["rejected_data", "validated_data", "data", "records"]:
                if key in data:
                    value = data[key]
                    print(f"  - {key}: type={type(value)}")
                    if isinstance(value, list):
                        print(f"    - length={len(value)}")
                        if len(value) > 0:
                            print(f"    - first item type={type(value[0])}")
        print("=" * 60)
        
        # Extraire les records
        record_list, was_list = normalize_records(data)
        
        # Si record_list est vide, essayer des approches alternatives
        if len(record_list) == 0 and isinstance(data, dict):
            # Cas spécial: les données pourraient être directement dans rejected_data
            for key in ["rejected_data", "validated_data"]:
                if key in data and isinstance(data[key], list) and data[key]:
                    record_list = data[key]
                    was_list = True
                    print(f"✅ Utilisation directe de {key}: {len(record_list)} enregistrements")
                    break
        
        if len(record_list) == 0:
            print("❌ Aucun enregistrement à écrire")
            return {
                "status": "error",
                "message": "No records to write - could not extract data from input",
                "step": "mongodb_write"
            }

        print(f"📊 {len(record_list)} enregistrements à écrire dans {collection}")
        print("=" * 60)

        client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
        db = client["data_pipeline"]
        coll = db[collection]

        # Écrire tous les documents
        results = []
        for i, record in enumerate(record_list):
            try:
                result = write_document(coll, record)
                results.append(result)
                print(f"  ✅ Document {i+1}/{len(record_list)} écrit - ID: {result['inserted_id']}")
            except Exception as e:
                print(f"  ❌ Erreur document {i+1}: {e}")
                results.append({"error": str(e)})
        
        print("=" * 60)
        print(f"✅ {len([r for r in results if 'error' not in r])} documents écrits avec succès")
        
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
            "inserted_ids": [r.get("inserted_id") for r in results if "error" not in r],
            "collection": collection,
            "record_count": len(record_list),
            "written_count": len([r for r in results if "error" not in r]),
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