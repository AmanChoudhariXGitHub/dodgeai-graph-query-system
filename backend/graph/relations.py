"""
Graph Relations - Logical abstraction layer for the ERP data model
Maps relationships between entities for flow tracing and neighbor exploration
"""

# Core relationship definition
GRAPH_RELATIONS = {
    "orders": {
        "customers": {"table": "customers", "via": "customer_id"},
        "deliveries": {"table": "deliveries", "via": "order_id"},
        "order_items": {"table": "order_items", "via": "order_id"},
    },
    "customers": {
        "orders": {"table": "orders", "via": "customer_id"},
    },
    "order_items": {
        "orders": {"table": "orders", "via": "order_id"},
        "products": {"table": "products", "via": "product_id"},
    },
    "products": {
        "order_items": {"table": "order_items", "via": "product_id"},
    },
    "deliveries": {
        "orders": {"table": "orders", "via": "order_id"},
        "invoices": {"table": "invoices", "via": "delivery_id"},
    },
    "invoices": {
        "deliveries": {"table": "deliveries", "via": "delivery_id"},
        "payments": {"table": "payments", "via": "invoice_id"},
    },
    "payments": {
        "invoices": {"table": "invoices", "via": "invoice_id"},
    },
}

# Main flow path (Order to Payment)
FLOW_PATH = ["orders", "deliveries", "invoices", "payments"]

# Entity colors for visualization
ENTITY_COLORS = {
    "orders": "#3B82F6",      # Blue
    "customers": "#8B5CF6",   # Purple
    "deliveries": "#F59E0B",  # Amber
    "invoices": "#EC4899",    # Pink
    "payments": "#10B981",    # Emerald
    "products": "#6366F1",    # Indigo
    "order_items": "#14B8A6", # Teal
}

# Entity icons
ENTITY_ICONS = {
    "orders": "📦",
    "customers": "👤",
    "deliveries": "🚚",
    "invoices": "📄",
    "payments": "💳",
    "products": "🏷️",
    "order_items": "📋",
}

def get_neighbors(entity_type: str) -> dict:
    """Get all connected entities for a given entity type"""
    return GRAPH_RELATIONS.get(entity_type, {})

def get_entity_color(entity_type: str) -> str:
    """Get color for entity type in visualization"""
    return ENTITY_COLORS.get(entity_type, "#6B7280")

def get_entity_icon(entity_type: str) -> str:
    """Get icon for entity type"""
    return ENTITY_ICONS.get(entity_type, "📌")

def is_valid_relationship(from_table: str, to_table: str) -> bool:
    """Check if relationship exists in graph"""
    relations = GRAPH_RELATIONS.get(from_table, {})
    return to_table in relations

def get_flow_sequence(start_table: str, end_table: str) -> list:
    """Get the path sequence between two tables in the flow"""
    try:
        start_idx = FLOW_PATH.index(start_table)
        end_idx = FLOW_PATH.index(end_table)
        if start_idx <= end_idx:
            return FLOW_PATH[start_idx:end_idx+1]
    except ValueError:
        pass
    return []
