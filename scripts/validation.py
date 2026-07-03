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


def normalize_records(data):
    if isinstance(data, list):
        return [item if isinstance(item, dict) else {"value": item} for item in data], True
    if isinstance(data, dict):
        return [data], False
    return [{"value": data}], False


def validate_record(record):
    errors = []
    warnings = []

    if "user_id" not in record:
        errors.append("Missing required field: user_id")

    if "email_address" not in record:
        errors.append("Missing required field: email_address")

    if "amount" in record:
        if record["amount"] < 0:
            errors.append(f"Amount must be positive: {record['amount']}")
        elif record["amount"] > 10000:
            warnings.append(f"Amount is very high: {record['amount']}")

    if "email_address" in record:
        email = record["email_address"]
        if "@" not in email or "." not in email:
            errors.append(f"Invalid email format: {email}")

    if "country_code" in record:
        valid_countries = ["FR", "DE", "US", "UK", "CA", "ES", "IT", "JP", "BR", "AU"]
        if record["country_code"] not in valid_countries:
            warnings.append(f"Unknown country code: {record['country_code']}")

    return errors, warnings

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
        
        record_list, was_list = normalize_records(deduplicated_data)

        if len(record_list) == 0:
            return {
                "status": "error",
                "message": "deduplicated_data is empty",
                "step": "validation"
            }

        all_errors = []
        all_warnings = []
        valid_records = []
        rejected_records = []

        for record in record_list:
            record_errors, record_warnings = validate_record(record)
            if not record_errors:
                valid_records.append(record)
            else:
                rejected_records.append(record)
            all_errors.extend(record_errors)
            all_warnings.extend(record_warnings)

        is_valid = len(all_errors) == 0
        validated_output = valid_records if was_list else (valid_records[0] if valid_records else None)
        rejected_output = rejected_records if was_list else (rejected_records[0] if rejected_records else None)
        
        print("=" * 60)
        print(f"📊 Résultat de la validation:")
        print(f"  - Statut: {'✅ VALIDE' if is_valid else '❌ REJETÉ'}")
        print(f"  - Erreurs: {len(all_errors)}")
        print(f"  - Avertissements: {len(all_warnings)}")
        if all_errors:
            print(f"  - Détails erreurs: {json.dumps(all_errors, indent=2)}")
        if all_warnings:
            print(f"  - Détails avertissements: {json.dumps(all_warnings, indent=2)}")
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
            "validated_data": validated_output if is_valid else None,
            "rejected_data": rejected_output,
            "errors": all_errors,
            "warnings": all_warnings,
            "is_valid": is_valid,
            "record_count": len(record_list),
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