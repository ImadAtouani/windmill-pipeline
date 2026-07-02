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


def main(raw_data):
    """
    Profilage - Analyse des types, colonnes, valeurs nulles
    """
    start_time = time.time()
    script_name = "profiling"

    try:
        print("=" * 60)
        print("📥 Données reçues dans profiling:")
        print(f"  - Type: {type(raw_data)}")

        if isinstance(raw_data, dict):
            print(f"  - Clés: {list(raw_data.keys())}")
        elif isinstance(raw_data, list):
            print(f"  - Longueur de la liste: {len(raw_data)}")
            if len(raw_data) > 0:
                print(f"  - Premier élément type: {type(raw_data[0])}")
                if isinstance(raw_data[0], dict):
                    print(f"  - Clés du premier élément: {list(raw_data[0].keys())}")
        print("=" * 60)

        # Gestion des différents types de données
        if isinstance(raw_data, list):
            if len(raw_data) > 0 and all(isinstance(item, dict) for item in raw_data):
                data = raw_data
                print(f"📊 Liste de {len(raw_data)} éléments conservée pour profilage")
            else:
                data = {"items": raw_data, "count": len(raw_data)}
        elif isinstance(raw_data, dict):
            data = raw_data
        else:
            data = {"value": raw_data}

        print(f"📊 Données à profiler: {json.dumps(data, indent=2)}")
        print("=" * 60)

        # Profilage
        if isinstance(data, dict):
            column_count = len(data)
            data_types = {k: type(v).__name__ for k, v in data.items()}
            null_values = {k: v is None for k, v in data.items()}
            columns = list(data.keys())
        elif isinstance(data, list):
            columns = sorted({key for item in data if isinstance(item, dict) for key in item.keys()})
            column_count = len(columns)
            data_types = {}
            null_values = {}
            for column in columns:
                first_value = next((item.get(column) for item in data if isinstance(item, dict) and item.get(column) is not None), None)
                data_types[column] = type(first_value).__name__ if first_value is not None else "NoneType"
                null_values[column] = any(isinstance(item, dict) and item.get(column) is None for item in data)
        else:
            column_count = 1
            data_types = {"value_type": type(data).__name__}
            null_values = {"is_null": data is None}
            columns = ["value"]

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
            "profile": {
                "column_count": column_count,
                "data_types": data_types,
                "null_values": null_values,
                "columns": columns,
            },
            "duration_ms": round(duration_ms, 2),
            "cpu_percent": get_cpu_usage(),
            "memory_mb": get_memory_mb(),
            "step": "profiling",
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
        return {"status": "error", "message": str(e), "step": "profiling"}