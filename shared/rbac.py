"""Role-based access control demo, shared by the Streamlit UI and the Global Orchestrator."""
ROLES = {
    "Global Administrator": {"views": {"global", "manufacturer", "shipping", "distribution", "supplier", "governance"},
                             "approve": True, "simulate": True, "key": "key-global-admin", "tabs": "all"},
    "Manufacturer Manager": {"views": {"global", "manufacturer"}, "approve": True, "simulate": True,
                             "key": "key-manufacturer-portal", "tabs": "all"},
    "Marketing Planner": {"views": {"manufacturer"}, "approve": False, "simulate": False,
                          "key": "key-manufacturer-portal", "tabs": {"Executive", "Marketing", "Forecasting", "Packing Plants", "Agents"}},
    "Operations Planner": {"views": {"manufacturer"}, "approve": False, "simulate": False,
                           "key": "key-manufacturer-portal", "tabs": {"Executive", "Operations", "Silo Monitoring", "Packing Plants", "Stock-out", "Agents", "Decision History"}},
    "Shipping Manager": {"views": {"global", "shipping"}, "approve": True, "simulate": True,
                         "key": "key-shipping-portal", "tabs": "all"},
    "Distributor Manager": {"views": {"distribution"}, "approve": False, "simulate": False,
                            "key": "key-distribution-portal", "tabs": "all"},
    "Supplier Manager": {"views": {"supplier"}, "approve": False, "simulate": False,
                         "key": "key-supplier-portal", "tabs": "all"},
}


def can(role: str, what: str) -> bool:
    return bool(ROLES.get(role, {}).get(what))
