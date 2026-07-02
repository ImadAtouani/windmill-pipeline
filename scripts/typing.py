import time
import json
import os
from typing import Literal, Dict, Any
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


def type_record(cleaned_record, date_format):
    typed_record = {}
    typing_stats = {
        "typed_as_date": 0,
        "typed_as_number": 0,
        "typed_as_bool": 0,
        "typed_as_enum": 0,
        "unchanged": 0,
        "errors": 0,
    }

    enum_values = ["FR", "DE", "US", "UK", "CA", "ES", "IT", "JP", "BR", "AU"]

    for key, value in cleaned_record.items():
        try:
            if key in ["date", "transaction_date", "birth_date"] and isinstance(value, str):
                try:
                    typed_record[key] = datetime.strptime(value, date_format).isoformat()
                    typing_stats["typed_as_date"] += 1
                except ValueError:
                    typed_record[key] = value
                    typing_stats["unchanged"] += 1
            elif key in ["amount", "price", "quantity", "value"]:
                if isinstance(value, (int, float)):
                    typed_record[key] = float(value)
                    typing_stats["typed_as_number"] += 1
                elif isinstance(value, str):
                    try:
                        clean_value = value.replace("€", "").replace("$", "").replace(",", "").strip()
                        typed_record[key] = float(clean_value)
                        typing_stats["typed_as_number"] += 1
                    except ValueError:
                        typed_record[key] = value
                        typing_stats["unchanged"] += 1
                else:
                    typed_record[key] = value
                    typing_stats["unchanged"] += 1
            elif key in ["active", "enabled", "verified", "is_valid"]:
                if isinstance(value, bool):
                    typed_record[key] = bool(value)
                    typing_stats["typed_as_bool"] += 1
                elif isinstance(value, str):
                    if value.lower() in ["true", "yes", "1"]:
                        typed_record[key] = True
                        typing_stats["typed_as_bool"] += 1
                    elif value.lower() in ["false", "no", "0"]:
                        typed_record[key] = False
                        typing_stats["typed_as_bool"] += 1
                    else:
                        typed_record[key] = value
                        typing_stats["unchanged"] += 1
                else:
                    typed_record[key] = value
                    typing_stats["unchanged"] += 1
            elif key in ["country", "country_code", "status"]:
                if isinstance(value, str) and value in enum_values:
                    typed_record[key] = value
                    typing_stats["typed_as_enum"] += 1
                else:
                    typed_record[key] = value
                    typing_stats["unchanged"] += 1
            else:
                typed_record[key] = value
                typing_stats["unchanged"] += 1
        except Exception:
            typing_stats["errors"] += 1
            typed_record[key] = value

    return typed_record, typing_stats


def main(cleaned_data: Dict[str, Any], date_format: str = "%Y-%m-%d"):
    """
    Typage - date, nombre, booléen, enum
    """
    start_time = time.time()
    script_name = "typing"

    try:
        print("=" * 60)
        print("📥 Données reçues dans typing:")
        print(f"  - Type: {type(cleaned_data)}")
        print(
            f"  - Clés: {list(cleaned_data.keys()) if isinstance(cleaned_data, dict) else 'Not a dict'}"
        )
        print(f"  - date_format: {date_format}")
        print("=" * 60)

        record_list, was_list = normalize_records(cleaned_data)

        if len(record_list) == 0:
            return {
                "status": "error",
                "message": "cleaned_data is empty",
                "step": "typing",
            }

        print(f"📊 Données avant typage: {json.dumps(cleaned_data, indent=2)}")
        print("=" * 60)

        typed_records = []
        typing_stats = {
            "typed_as_date": 0,
            "typed_as_number": 0,
            "typed_as_bool": 0,
            "typed_as_enum": 0,
            "unchanged": 0,
            "errors": 0,
        }
        for record in record_list:
            typed_record, record_stats = type_record(record, date_format)
            typed_records.append(typed_record)
            for stat_key in typing_stats:
                typing_stats[stat_key] += record_stats[stat_key]

        typed_data = typed_records if was_list else typed_records[0]

        print("=" * 60)
        print(f"📊 Statistiques de typage: {json.dumps(typing_stats, indent=2)}")
        print(f"📊 Données après typage: {json.dumps(typed_data, indent=2)}")
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
            "status": "success" if typing_stats["errors"] == 0 else "partial",
            "typed_data": typed_data,
            "record_count": len(typed_records),
            "typing_stats": typing_stats,
            "duration_ms": round(duration_ms, 2),
            "cpu_percent": get_cpu_usage(),
            "memory_mb": get_memory_mb(),
            "step": "typing",
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
        return {"status": "error", "message": str(e), "step": "typing"}