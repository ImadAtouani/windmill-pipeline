from typing import Literal, Dict, Any
from datetime import datetime
import json

def main(
    cleaned_data: Dict[str, Any],
    date_format: str = "%Y-%m-%d"
):
    """
    Typage - date, nombre, booléen, enum
    """
    
    try:
        print("=" * 60)
        print("📥 Données reçues dans typing:")
        print(f"  - Type: {type(cleaned_data)}")
        print(f"  - Clés: {list(cleaned_data.keys()) if isinstance(cleaned_data, dict) else 'Not a dict'}")
        print(f"  - date_format: {date_format}")
        print("=" * 60)
        
        if not isinstance(cleaned_data, dict):
            return {
                "status": "error",
                "message": f"cleaned_data is not a dict: {type(cleaned_data)}",
                "step": "typing"
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
            "errors": 0
        }
        
        # Liste des enums possibles (exemple)
        enum_values = ["FR", "DE", "US", "UK", "CA", "ES", "IT", "JP", "BR", "AU"]
        
        for key, value in cleaned_data.items():
            try:
                # Typage des dates
                if key in ["date", "transaction_date", "birth_date"] and isinstance(value, str):
                    try:
                        typed_data[key] = datetime.strptime(value, date_format).isoformat()
                        typing_stats["typed_as_date"] += 1
                        print(f"  ✅ {key}: '{value}' → date ({typed_data[key]})")
                    except ValueError:
                        typed_data[key] = value
                        typing_stats["unchanged"] += 1
                        print(f"  ⚠️ {key}: '{value}' → impossible de typer en date")
                
                # Typage des nombres
                elif key in ["amount", "price", "quantity", "value"]:
                    if isinstance(value, (int, float)):
                        typed_data[key] = float(value)
                        typing_stats["typed_as_number"] += 1
                        print(f"  ✅ {key}: {value} → nombre ({typed_data[key]})")
                    elif isinstance(value, str):
                        try:
                            # Nettoyer la chaîne (enlever les symboles €, $, etc.)
                            clean_value = value.replace('€', '').replace('$', '').replace(',', '').strip()
                            typed_data[key] = float(clean_value)
                            typing_stats["typed_as_number"] += 1
                            print(f"  ✅ {key}: '{value}' → nombre ({typed_data[key]})")
                        except ValueError:
                            typed_data[key] = value
                            typing_stats["unchanged"] += 1
                            print(f"  ⚠️ {key}: '{value}' → impossible de typer en nombre")
                    else:
                        typed_data[key] = value
                        typing_stats["unchanged"] += 1
                
                # Typage des booléens
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
                
                # Typage des enums (ex: pays)
                elif key in ["country", "country_code", "status"]:
                    if isinstance(value, str) and value in enum_values:
                        typed_data[key] = value
                        typing_stats["typed_as_enum"] += 1
                        print(f"  ✅ {key}: '{value}' → enum (valeur valide)")
                    else:
                        typed_data[key] = value
                        typing_stats["unchanged"] += 1
                
                # Autres champs
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
        
        return {
            "status": "success" if typing_stats["errors"] == 0 else "partial",
            "typed_data": typed_data,
            "typing_stats": typing_stats,
            "step": "typing"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "step": "typing"
        }