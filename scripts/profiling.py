import time
import json
import os
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

def main(raw_data: dict):
    """
    Profilage - Analyse des types, colonnes, valeurs nulles
    """
    start_time = time.time()
    script_name = "profiling"
    
    try:
        print("=" * 60)
        print("📥 Données reçues dans profiling:")
        print(f"  - Type: {type(raw_data)}")
        print(f"  - Clés: {list(raw_data.keys()) if isinstance(raw_data, dict) else 'Not a dict'}")
        print("=" * 60)
        
        if not isinstance(raw_data, dict):
            duration_ms = (time.time() - start_time) * 1000
            client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
            db = client["data_pipeline"]
            db.script_metrics.insert_one({
                "script": script_name,
                "duration_ms": duration_ms,
                "status": "error",
                "error": "raw_data is not a dict",
                "cpu_percent": get_cpu_usage(),
                "memory_mb": get_memory_mb(),
                "timestamp": datetime.now().isoformat()
            })
            return {
                "status": "error",
                "message": f"raw_data is not a dict: {type(raw_data)}",
                "step": "profiling"
            }
        
        data = raw_data
        
        print(f"📊 Données à profiler: {json.dumps(data, indent=2)}")
        print("=" * 60)
        
        column_count = len(data)
        data_types = {k: type(v).__name__ for k, v in data.items()}
        null_values = {k: v is None for k, v in data.items()}
        
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
            "profile": {
                "column_count": column_count,
                "data_types": data_types,
                "null_values": null_values,
                "columns": list(data.keys())
            },
            "duration_ms": round(duration_ms, 2),
            "cpu_percent": get_cpu_usage(),
            "memory_mb": get_memory_mb(),
            "step": "profiling"
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
            "step": "profiling"
        }