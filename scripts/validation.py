def main(deduplicated_data: dict):
    """
    Validation - règles métier + schéma
    """
    errors = []
    
    # Règles de validation
    if "user_id" not in deduplicated_data:
        errors.append("Missing required field: user_id")
    
    if "amount" in deduplicated_data and deduplicated_data["amount"] < 0:
        errors.append("Amount must be positive")
    
    is_valid = len(errors) == 0
    
    return {
        "status": "valid" if is_valid else "rejected",
        "validated_data": deduplicated_data if is_valid else None,
        "errors": errors,
        "step": "validation"
    }