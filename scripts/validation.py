def main(deduplicated_data: dict):
    """
    Validation - règles métier + schéma
    """
    import json
    
    try:
        print("=" * 60)
        print("📥 Données reçues dans validation:")
        print(f"  - Type: {type(deduplicated_data)}")
        print(f"  - Clés: {list(deduplicated_data.keys()) if isinstance(deduplicated_data, dict) else 'Not a dict'}")
        print("=" * 60)
        
        if not isinstance(deduplicated_data, dict):
            return {
                "status": "error",
                "message": f"deduplicated_data is not a dict: {type(deduplicated_data)}",
                "step": "validation"
            }
        
        errors = []
        warnings = []
        
        # Règle 1 : Champ obligatoire "user_id"
        if "user_id" not in deduplicated_data:
            errors.append("Missing required field: user_id")
        else:
            print(f"  ✅ user_id présent: {deduplicated_data['user_id']}")
        
        # Règle 2 : Champ obligatoire "email_address"
        if "email_address" not in deduplicated_data:
            errors.append("Missing required field: email_address")
        else:
            print(f"  ✅ email_address présent: {deduplicated_data['email_address']}")
        
        # Règle 3 : Montant positif
        if "amount" in deduplicated_data:
            if deduplicated_data["amount"] < 0:
                errors.append(f"Amount must be positive: {deduplicated_data['amount']}")
            elif deduplicated_data["amount"] > 10000:
                warnings.append(f"Amount is very high: {deduplicated_data['amount']}")
            else:
                print(f"  ✅ amount valide: {deduplicated_data['amount']}")
        
        # Règle 4 : Format email
        if "email_address" in deduplicated_data:
            email = deduplicated_data["email_address"]
            if "@" not in email or "." not in email:
                errors.append(f"Invalid email format: {email}")
            else:
                print(f"  ✅ email valide: {email}")
        
        # Règle 5 : Code pays valide
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
        
        return {
            "status": "valid" if is_valid else "rejected",
            "validated_data": deduplicated_data if is_valid else None,
            "errors": errors,
            "warnings": warnings,
            "is_valid": is_valid,
            "step": "validation"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "step": "validation"
        }