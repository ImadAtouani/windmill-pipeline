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


def main(mapped_data: dict):
    """
    Nettoyage - trim, encodage, formats
    """
    start_time = time.time()
    script_name = "cleaning"

    try:
        print("=" * 60)
        print("📥 Données reçues dans cleaning:")
        print(f"  - Type: {type(mapped_data)}")
        print(
            f"  - Clés: {list(mapped_data.keys()) if isinstance(mapped_data, dict) else 'Not a dict'}"
        )
        print("=" * 60)

        if not isinstance(mapped_data, dict):
            duration_ms = (time.time() - start_time) * 1000
            client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
            db = client["data_pipeline"]
            db.script_metrics.insert_one(
                {
                    "script": script_name,
                    "duration_ms": duration_ms,
                    "status": "error",
                    "error": "mapped_data is not a dict",
                    "cpu_percent": get_cpu_usage(),
                    "memory_mb": get_memory_mb(),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return {
                "status": "error",
                "message": f"mapped_data is not a dict: {type(mapped_data)}",
                "step": "cleaning",
            }

        print(f"📊 Données avant nettoyage: {json.dumps(mapped_data, indent=2)}")
        print("=" * 60)

        cleaned = {}
        cleaning_stats = {"trimmed": 0, "encoded": 0, "unchanged": 0}

        for key, value in mapped_data.items():
            if isinstance(value, str):
                trimmed = value.strip()
                if trimmed != value:
                    cleaning_stats["trimmed"] += 1

                encoded = trimmed.encode("utf-8").decode("utf-8")
                if encoded != trimmed:
                    cleaning_stats["encoded"] += 1
                else:
                    cleaning_stats["unchanged"] += 1

                cleaned[key] = encoded
            else:
                cleaned[key] = value
                cleaning_stats["unchanged"] += 1

        print(f"📊 Statistiques de nettoyage: {json.dumps(cleaning_stats, indent=2)}")
        print(f"📊 Données après nettoyage: {json.dumps(cleaned, indent=2)}")
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
            "cleaned_data": cleaned,
            "cleaning_stats": cleaning_stats,
            "duration_ms": round(duration_ms, 2),
            "cpu_percent": get_cpu_usage(),
            "memory_mb": get_memory_mb(),
            "step": "cleaning",
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
        return {"status": "error", "message": str(e), "step": "cleaning"}