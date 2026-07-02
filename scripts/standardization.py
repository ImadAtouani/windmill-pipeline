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


def parse_amount(value):
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace("€", "").replace("$", "").replace(",", "").strip())
        except ValueError:
            return None
    return None


def standardize_record(record, country_mapping):
    standardized = record.copy()
    record_stats = {
        "countries_normalized": 0,
        "currencies_converted": 0,
        "units_normalized": 0,
    }

    country_value = standardized.get("country_code", standardized.get("country"))
    if isinstance(country_value, str):
        country_code = country_value.upper()
        if country_code in country_mapping:
            standardized["country_code"] = country_code
            standardized["country_name"] = country_mapping[country_code]
            record_stats["countries_normalized"] += 1
        elif "country" in standardized:
            standardized["country"] = country_code

    if "amount" in standardized:
        amount_numeric = parse_amount(standardized["amount"])
        if amount_numeric is not None:
            standardized["amount"] = amount_numeric
            standardized["amount_usd"] = round(amount_numeric * 1.08, 2)
            record_stats["currencies_converted"] += 1

    return standardized, record_stats


def main(typed_data: dict):
    """
    Standardisation - noms, unités, devises, pays
    """
    start_time = time.time()
    script_name = "standardization"

    try:
        print("=" * 60)
        print("📥 Données reçues dans standardization:")
        print(f"  - Type: {type(typed_data)}")
        print(
            f"  - Clés: {list(typed_data.keys()) if isinstance(typed_data, dict) else 'Not a dict'}"
        )
        print("=" * 60)

        record_list, was_list = normalize_records(typed_data)

        if len(record_list) == 0:
            return {
                "status": "error",
                "message": "typed_data is empty",
                "step": "standardization",
            }

        print(f"📊 Données avant standardisation: {json.dumps(typed_data, indent=2)}")
        print("=" * 60)

        std_stats = {
            "countries_normalized": 0,
            "currencies_converted": 0,
            "units_normalized": 0,
        }

        country_mapping = {
            "FR": "France",
            "DE": "Germany",
            "US": "United States",
            "UK": "United Kingdom",
            "CA": "Canada",
            "ES": "Spain",
            "IT": "Italy",
            "JP": "Japan",
            "BR": "Brazil",
            "AU": "Australia",
        }

        standardized_records = []
        for record in record_list:
            standardized_record, record_stats = standardize_record(record, country_mapping)
            standardized_records.append(standardized_record)
            for stat_key in std_stats:
                std_stats[stat_key] += record_stats[stat_key]

        standardized = standardized_records if was_list else standardized_records[0]

        print("=" * 60)
        print(f"📊 Statistiques de standardisation: {json.dumps(std_stats, indent=2)}")
        print(f"📊 Données après standardisation: {json.dumps(standardized, indent=2)}")
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
            "standardized_data": standardized,
            "record_count": len(standardized_records),
            "standardization_stats": std_stats,
            "duration_ms": round(duration_ms, 2),
            "cpu_percent": get_cpu_usage(),
            "memory_mb": get_memory_mb(),
            "step": "standardization",
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
        return {"status": "error", "message": str(e), "step": "standardization"}