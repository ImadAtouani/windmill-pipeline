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

def main(deduplicated_data: dict):
    """
    Validation - règles métier + schéma
    """
    start_time = time.time()
    script_name = "validation"
    
    try:
        print("=" * 60)
        print("📥 Données reçues dans validation:")
        print(f"  - Type: {type(deduplicated_data)}")
        print(f"  - Clés: {list(deduplicated_data.keys()) if isinstance(deduplicated_data, dict) else 'Not a dict'}")
        print("=" * 60)
        
        if not isinstance(deduplicated_data, dict):
            duration_ms = (time.time() - start_time) * 1000
            client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
            db = client["data_pipeline"]
            db.script_metrics.insert_one({
                "script": script_name,
                "duration_ms": duration_ms,
                "status": "error",
                "error": "deduplicated_data is not a dict",
                "cpu_percent": get_cpu_usage(),
                "memory_mb": get_memory_mb(),
                "timestamp": datetime.now().isoformat()
            })
            return {
                "status": "error",
                "message": f"deduplicated_data is not a dict: {type(deduplicated_data)}",
                "step": "validation"
            }
        
        errors = []
        warnings = []
        
        if "user_id" not in deduplicated_data:
            errors.append("Missing required field: user_id")
        else:
            print(f"  ✅ user_id présent: {deduplicated_data['user_id']}")
        
        if "email_address" not in deduplicated_data:
            errors.append("Missing required field: email_address")
        else:
            print(f"  ✅ email_address présent: {deduplicated_data['email_address']}")
        
        if "amount" in deduplicated_data:
            if deduplicated_data["amount"] < 0:
                errors.append(f"Amount must be positive: {deduplicated_data['amount']}")
            elif deduplicated_data["amount"] > 10000:
                warnings.append(f"Amount is very high: {deduplicated_data['amount']}")
            else:
                print(f"  ✅ amount valide: {deduplicated_data['amount']}")
        
        if "email_address" in deduplicated_data:
            email = deduplicated_data["email_address"]
            if "@" not in email or "." not in email:
                errors.append(f"Invalid email format: {email}")
            else:
                print(f"  ✅ email valide: {email}")
        
        if "country_code" in deduplicated_data:
            valid_countries = ["FR", "DE", "US", "UK", "CA", "ES", "IT", "JP", "BR", "AU"]
            if deduplicated_data["country_code"] not in valid_countries:
                warnings.append(f"Unknown country code: {deduplicated_data['country_code']}")
            else:
                print(f"  ✅ country_code valide: {deduplicated_data['country_code']}")
        
        is_valid = len(errors) == 0
        
        print("=" * 60)
        print(f"📊 Résultat de la validation:")
        print(f"  - Statut: {'✅ VALIDE' if is_valid else '❌ REJETÉ'}")
        print(f"  - Erreurs: {len(errors)}")
        print(f"  - Avertissements: {len(warnings)}")
        if errors:
            print(f"  - Détails erreurs: {json.dumps(errors, indent=2)}")
        if warnings:
            print(f"  - Détails avertissements: {json.dumps(warnings, indent=2)}")
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
            "status": "valid" if is_valid else "rejected",
            "validated_data": deduplicated_data if is_valid else None,
            "errors": errors,
            "warnings": warnings,
            "is_valid": is_valid,
            "duration_ms": round(duration_ms, 2),
            "cpu_percent": get_cpu_usage(),
            "memory_mb": get_memory_mb(),
            "step": "validation"
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
            "step": "validation"
        }