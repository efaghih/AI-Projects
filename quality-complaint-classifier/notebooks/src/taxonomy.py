# src/taxonomy.py

GENERAL_CATEGORIES = {
    "documentation": "Documentation or information issue",
    "performance": "Product or service performance issue",
    "process_delay": "Process delay issue",
    "customer_service": "Customer service issue",
    "account_error": "Account or record error",
    "billing": "Unexpected charge or cost issue",
    "safety_risk": "Safety or high-risk issue",
    "other": "Other",
}

ISSUE_TO_GENERAL = {
    "Incorrect information on your report": "documentation",
    "Improper use of your report": "documentation",
    "Problem with a company's investigation into an existing problem": "process_delay",
    "Attempts to collect debt not owed": "account_error",
    "Managing an account": "account_error",
    "Problem with a purchase shown on your statement": "billing",
    "False statements or representation": "documentation",
    "Written notification about debt": "customer_service",
    "Trouble during payment process": "billing",
    "Took or threatened to take negative or legal action": "safety_risk",
}

GENERAL_TO_MANUFACTURING = {
    "documentation": "Mislabeling / documentation error",
    "performance": "Runnability / performance issue",
    "process_delay": "Process control / service delay",
    "customer_service": "Customer handling issue",
    "account_error": "Lot / traceability / record error",
    "billing": "Billing or specification mismatch",
    "safety_risk": "Urgent quality / safety risk",
    "other": "Unclassified / other",
}

def map_issue_to_general(issue_label: str) -> str:
    key = ISSUE_TO_GENERAL.get(issue_label)
    if key is None:
        return GENERAL_CATEGORIES["other"]
    return GENERAL_CATEGORIES[key]

def map_issue_to_manufacturing(issue_label: str) -> str:
    key = ISSUE_TO_GENERAL.get(issue_label, "other")
    return GENERAL_TO_MANUFACTURING[key]

def map_general_key_to_label(general_key: str) -> str:
    return GENERAL_CATEGORIES.get(general_key, GENERAL_CATEGORIES["other"])