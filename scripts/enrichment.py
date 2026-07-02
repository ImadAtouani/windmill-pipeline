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


def normalize_records(data):
    if isinstance(data, list):
        return [item if isinstance(item, dict) else {"value": item} for item in data], True
    if isinstance(data, dict):
        return [data], False
    return [{"value": data}], False


def enrich_record(record):
    enriched = record.copy()
    enriched.update(
        {
            "enriched_at": datetime.now().isoformat(),
            "pipeline_version": "1.0.0",
            "source_system": "windmill_pipeline",
            "processing_timestamp": datetime.now().timestamp(),
        }
    )
    return enriched


def main(validated_data: dict):
    """
    Enrichissement - métadonnées, source, horodatage
    """
    start_time = time.time()
    script_name = "enrichment"

    try:
        print("=" * 60)
        print("📥 Données reçues dans enrichment:")
        print(f"  - Type: {type(validated_data)}")
        print(
            f"  - Clés: {list(validated_data.keys()) if isinstance(validated_data, dict) else 'Not a dict'}"
        )
        print("=" * 60)

        record_list, was_list = normalize_records(validated_data)

        if len(record_list) == 0:
            return {
                "status": "error",
                "message": "validated_data is empty",
                "step": "enrichment",
            }

        enriched_records = [enrich_record(record) for record in record_list]
        enriched = enriched_records if was_list else enriched_records[0]

        print(f"📊 Données enrichies avec:")
        if isinstance(enriched, list):
            first_record = enriched[0] if enriched else {}
            print(f"  - records: {len(enriched)}")
            if first_record:
                print(f"  - enriched_at: {first_record.get('enriched_at')}")
                print(f"  - pipeline_version: {first_record.get('pipeline_version')}")
                print(f"  - source_system: {first_record.get('source_system')}")
        else:
            print(f"  - enriched_at: {enriched['enriched_at']}")
            print(f"  - pipeline_version: {enriched['pipeline_version']}")
            print(f"  - source_system: {enriched['source_system']}")
        print("=" * 60)

        duration_ms = (time.time() - start_time) * 1000
        try:
            client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
            db = client["data_pipeline"]
            db.script_metrics.insert_one(
                {
                    "script": script_name,
                    "duration_ms": duration_ms,
                    "status": "success",
                    "cpu_percent": get_cpu_usage(),
                    "memory_mb": get_memory_mb(),
                    "timestamp": datetime.now().isoformat(),
                }
            )
        except Exception:
            pass

        return {
            "status": "success",
            "enriched_data": enriched,
            "record_count": len(enriched_records),
            "duration_ms": round(duration_ms, 2),
            "cpu_percent": get_cpu_usage(),
            "memory_mb": get_memory_mb(),
            "step": "enrichment",
        }

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        try:
            client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
            db = client["data_pipeline"]
            db.script_metrics.insert_one(
                {
                    "script": script_name,
                    "duration_ms": duration_ms,
                    "status": "error",
                    "error": str(e)[:100],
                    "cpu_percent": get_cpu_usage(),
                    "memory_mb": get_memory_mb(),
                    "timestamp": datetime.now().isoformat(),
                }
            )
        except:
            pass
        return {"status": "error", "message": str(e), "step": "enrichment"}