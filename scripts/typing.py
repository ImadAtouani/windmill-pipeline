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

        if not isinstance(cleaned_data, dict):
            duration_ms = (time.time() - start_time) * 1000
            client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
            db = client["data_pipeline"]
            db.script_metrics.insert_one(
                {
                    "script": script_name,
                    "duration_ms": duration_ms,
                    "status": "error",
                    "error": "cleaned_data is not a dict",
                    "cpu_percent": get_cpu_usage(),
                    "memory_mb": get_memory_mb(),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return {
                "status": "error",
                "message": f"cleaned_data is not a dict: {type(cleaned_data)}",
                "step": "typing",
            }

        print(f"📊 Données avant typage: {json.dumps(cleaned_data, indent=2)}")
        print("=" * 60)

        typed_data = {}
        typing_stats = {
            "typed_as_date": 0,
            "typed_as_number": 0,
            "typed_as_bool": 0,
            "typed_as_enum": 0,
            "unchanged": 0,
            "errors": 0,
        }

        enum_values = ["FR", "DE", "US", "UK", "CA", "ES", "IT", "JP", "BR", "AU"]

        for key, value in cleaned_data.items():
            try:
                if key in ["date", "transaction_date", "birth_date"] and isinstance(
                    value, str
                ):
                    try:
                        typed_data[key] = datetime.strptime(
                            value, date_format
                        ).isoformat()
                        typing_stats["typed_as_date"] += 1
                        print(f"  ✅ {key}: '{value}' → date ({typed_data[key]})")
                    except ValueError:
                        typed_data[key] = value
                        typing_stats["unchanged"] += 1
                        print(f"  ⚠️ {key}: '{value}' → impossible de typer en date")

                elif key in ["amount", "price", "quantity", "value"]:
                    if isinstance(value, (int, float)):
                        typed_data[key] = float(value)
                        typing_stats["typed_as_number"] += 1
                        print(f"  ✅ {key}: {value} → nombre ({typed_data[key]})")
                    elif isinstance(value, str):
                        try:
                            clean_value = (
                                value.replace("€", "")
                                .replace("$", "")
                                .replace(",", "")
                                .strip()
                            )
                            typed_data[key] = float(clean_value)
                            typing_stats["typed_as_number"] += 1
                            print(f"  ✅ {key}: '{value}' → nombre ({typed_data[key]})")
                        except ValueError:
                            typed_data[key] = value
                            typing_stats["unchanged"] += 1
                            print(
                                f"  ⚠️ {key}: '{value}' → impossible de typer en nombre"
                            )
                    else:
                        typed_data[key] = value
                        typing_stats["unchanged"] += 1

                elif key in ["active", "enabled", "verified", "is_valid"]:
                    if isinstance(value, bool):
                        typed_data[key] = bool(value)
                        typing_stats["typed_as_bool"] += 1
                        print(f"  ✅ {key}: {value} → booléen")
                    elif isinstance(value, str):
                        if value.lower() in ["true", "yes", "1"]:
                            typed_data[key] = True
                            typing_stats["typed_as_bool"] += 1
                            print(f"  ✅ {key}: '{value}' → booléen (True)")
                        elif value.lower() in ["false", "no", "0"]:
                            typed_data[key] = False
                            typing_stats["typed_as_bool"] += 1
                            print(f"  ✅ {key}: '{value}' → booléen (False)")
                        else:
                            typed_data[key] = value
                            typing_stats["unchanged"] += 1
                    else:
                        typed_data[key] = value
                        typing_stats["unchanged"] += 1

                elif key in ["country", "country_code", "status"]:
                    if isinstance(value, str) and value in enum_values:
                        typed_data[key] = value
                        typing_stats["typed_as_enum"] += 1
                        print(f"  ✅ {key}: '{value}' → enum (valeur valide)")
                    else:
                        typed_data[key] = value
                        typing_stats["unchanged"] += 1

                else:
                    typed_data[key] = value
                    typing_stats["unchanged"] += 1

            except Exception as e:
                print(f"  ❌ Erreur lors du typage de {key}: {str(e)}")
                typing_stats["errors"] += 1
                typed_data[key] = value

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