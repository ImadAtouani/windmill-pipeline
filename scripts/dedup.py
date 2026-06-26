import time
import hashlib
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

def main(standardized_data: dict):
    """
    Déduplication - clé métier / hash
    """
    start_time = time.time()
    script_name = "dedup"
    
    try:
        print("=" * 60)
        print("📥 Données reçues dans dedup:")
        print(f"  - Type: {type(standardized_data)}")
        print(f"  - Clés: {list(standardized_data.keys()) if isinstance(standardized_data, dict) else 'Not a dict'}")
        print("=" * 60)
        
        if not isinstance(standardized_data, dict):
            duration_ms = (time.time() - start_time) * 1000
            client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
            db = client["data_pipeline"]
            db.script_metrics.insert_one({
                "script": script_name,
                "duration_ms": duration_ms,
                "status": "error",
                "error": "standardized_data is not a dict",
                "cpu_percent": get_cpu_usage(),
                "memory_mb": get_memory_mb(),
                "timestamp": datetime.now().isoformat()
            })
            return {
                "status": "error",
                "message": f"standardized_data is not a dict: {type(standardized_data)}",
                "step": "dedup"
            }
        
        data_string = str(sorted(standardized_data.items()))
        timestamp = datetime.now().isoformat()
        unique_string = f"{data_string}_{timestamp}_{id(standardized_data)}"
        dedup_key = hashlib.md5(unique_string.encode()).hexdigest()
        
        standardized_data_with_key = standardized_data.copy()
        standardized_data_with_key["dedup_key"] = dedup_key
        
        print(f"🔑 Clé de déduplication générée: {dedup_key}")
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
            "deduplicated_data": standardized_data_with_key,
            "dedup_key": dedup_key,
            "duration_ms": round(duration_ms, 2),
            "cpu_percent": get_cpu_usage(),
            "memory_mb": get_memory_mb(),
            "step": "dedup"
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
            "step": "dedup"
        }