import time
import json
import os
from datetime import datetime
from pymongo import MongoClient

def get_cpu_usage():
    try:
        with open("/proc/stat", "r") as f:
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
        with open("/proc/self/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    kb = int(line.split()[1])
                    return round(kb / 1024, 2)
    except:
        return 0


def normalize_records(records):
    if isinstance(records, list):
        return [record if isinstance(record, dict) else {"value": record} for record in records], True
    if isinstance(records, dict):
        return [records], False
    return [{"value": records}], False


def map_record(record):
    mapped = {}

    if "id" in record:
        mapped["user_id"] = record["id"]
    if "name" in record:
        mapped["full_name"] = record["name"]
    if "amount" in record:
        mapped["amount"] = record["amount"]
    elif "price" in record:
        mapped["amount"] = record["price"]
    elif "salary" in record:
        mapped["amount"] = record["salary"]
    if "date" in record:
        mapped["transaction_date"] = record["date"]
    if "email" in record:
        mapped["email_address"] = record["email"]

    country_value = record.get("country_code", record.get("country"))
    if country_value is not None:
        mapped["country_code"] = country_value

    for key, value in record.items():
        if key not in ["id", "name", "amount", "price", "salary", "date", "email", "country", "country_code"]:
            mapped[key] = value

    return mapped

def main(parsed_data: dict):
    """
    Mapping - champs source → modèle cible
    """
    start_time = time.time()
    script_name = "mapping"

    try:
        print("=" * 60)
        print("📥 Données reçues dans mapping:")
        print(f"  - parsed_data keys: {list(parsed_data.keys()) if isinstance(parsed_data, dict) else 'Not a dict'}")
        print("=" * 60)

        # Récupération des records
        if isinstance(parsed_data, dict) and "records" in parsed_data:
            records = parsed_data["records"]
            print(f"✅ Utilisation de parsed_data['records']")
        else:
            records = parsed_data
            print(f"✅ Utilisation de parsed_data directement")

        record_list, was_list = normalize_records(records)
        if len(record_list) == 0:
            return {
                "status": "error",
                "message": "Records list is empty",
                "step": "mapping"
            }

        if not all(isinstance(record, dict) for record in record_list):
            duration_ms = (time.time() - start_time) * 1000
            client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
            db = client["data_pipeline"]
            db.script_metrics.insert_one({
                "script": script_name,
                "duration_ms": duration_ms,
                "status": "error",
                "error": "records is not a dict",
                "cpu_percent": get_cpu_usage(),
                "memory_mb": get_memory_mb(),
                "timestamp": datetime.now().isoformat()
            })
            return {
                "status": "error",
                "message": f"records is not a dict: {type(records)}",
                "step": "mapping"
            }

        mapped_records = [map_record(record) for record in record_list]
        mapped_data = mapped_records if was_list else mapped_records[0]

        print(f"📊 Données mappées: {json.dumps(mapped_data, indent=2)}")
        print("=" * 60)

        duration_ms = (time.time() - start_time) * 1000
        client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
        db = client["data_pipeline"]
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
            "mapped_data": mapped_data,
            "record_count": len(mapped_records),
            "duration_ms": round(duration_ms, 2),
            "cpu_percent": get_cpu_usage(),
            "memory_mb": get_memory_mb(),
            "step": "mapping"
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
        return {"status": "error", "message": str(e), "step": "mapping"}