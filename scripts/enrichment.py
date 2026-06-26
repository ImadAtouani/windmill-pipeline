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

        if not isinstance(validated_data, dict):
            duration_ms = (time.time() - start_time) * 1000
            client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
            db = client["data_pipeline"]
            db.script_metrics.insert_one(
                {
                    "script": script_name,
                    "duration_ms": duration_ms,
                    "status": "error",
                    "error": "validated_data is not a dict",
                    "cpu_percent": get_cpu_usage(),
                    "memory_mb": get_memory_mb(),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return {
                "status": "error",
                "message": f"validated_data is not a dict: {type(validated_data)}",
                "step": "enrichment",
            }

        enriched = validated_data.copy()
        enriched.update(
            {
                "enriched_at": datetime.now().isoformat(),
                "pipeline_version": "1.0.0",
                "source_system": "windmill_pipeline",
                "processing_timestamp": datetime.now().timestamp(),
            }
        )

        print(f"📊 Données enrichies avec:")
        print(f"  - enriched_at: {enriched['enriched_at']}")
        print(f"  - pipeline_version: {enriched['pipeline_version']}")
        print(f"  - source_system: {enriched['source_system']}")
        print("=" * 60)

        duration_ms = (time.time() - start_time) * 1000
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

        return {
            "status": "success",
            "enriched_data": enriched,
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