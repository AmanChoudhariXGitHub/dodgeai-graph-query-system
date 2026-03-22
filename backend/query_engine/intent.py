"""
Intent Classification
Determines query type to route to appropriate handler
"""
from enum import Enum
from typing import Tuple

class QueryIntent(str, Enum):
    FLOW = "FLOW"              # Trace, path, flow queries
    AGGREGATION = "AGGREGATION"  # Count, sum, total, highest, lowest
    LOOKUP = "LOOKUP"          # Find, show, list, get, what is
    GENERAL = "GENERAL"        # Everything else
    COMPARISON = "COMPARISON"  # Compare, difference, vs

def classify_intent(query: str) -> Tuple[QueryIntent, list]:
    """
    Classify query intent and extract key entities
    Returns: (intent, keywords)
    """
    query_lower = query.lower()
    
    # FLOW keywords
    flow_keywords = ["trace", "flow", "path", "follow", "journey", "from", "to", "through", "track"]
    if any(kw in query_lower for kw in flow_keywords):
        # Extract order/entity numbers if present
        import re
        numbers = re.findall(r"#?(\d+)", query)
        return QueryIntent.FLOW, numbers if numbers else []
    
    # AGGREGATION keywords
    aggregation_keywords = [
        "count", "total", "sum", "average", "highest", "lowest", "most", "least",
        "maximum", "minimum", "how many", "how much", "aggregate"
    ]
    if any(kw in query_lower for kw in aggregation_keywords):
        return QueryIntent.AGGREGATION, []
    
    # COMPARISON keywords
    comparison_keywords = ["compare", "difference", "vs", "versus", "better", "worse", "more", "less"]
    if any(kw in query_lower for kw in comparison_keywords):
        return QueryIntent.COMPARISON, []
    
    # LOOKUP keywords
    lookup_keywords = ["find", "show", "list", "get", "what", "which", "who", "where", "when"]
    if any(kw in query_lower for kw in lookup_keywords):
        return QueryIntent.LOOKUP, []
    
    # Default to GENERAL
    return QueryIntent.GENERAL, []

def get_intent_handler_prompt(intent: QueryIntent, query: str) -> str:
    """
    Get the system prompt for LLM based on intent
    This guides the LLM to generate appropriate SQL
    """
    base_prompt = """You are a SQL expert for an ERP order-to-payment system.

RULES:
- Only generate SELECT queries
- Use only provided schema tables
- No hallucinated columns or tables
- Keep queries efficient (LIMIT 50)
- Join tables only via foreign keys
- Always use meaningful WHERE conditions when possible

SCHEMA AND RELATIONSHIPS:
- customers: id, name, email
- orders: id (PK), customer_id (FK→customers), order_date, total, status
- order_items: id (PK), order_id (FK→orders), product_id (FK→products), quantity
- products: id (PK), name, price
- deliveries: id (PK), order_id (FK→orders), delivery_date, status
- invoices: id (PK), delivery_id (FK→deliveries), amount, issue_date
- payments: id (PK), invoice_id (FK→invoices), amount, payment_date, status

VALID JOIN PATHS:
- orders → customers (ON orders.customer_id = customers.id)
- orders → order_items (ON orders.id = order_items.order_id)
- order_items → products (ON order_items.product_id = products.id)
- orders → deliveries (ON orders.id = deliveries.order_id)
- deliveries → invoices (ON deliveries.id = invoices.delivery_id)
- invoices → payments (ON invoices.id = payments.invoice_id)"""
    
    if intent == QueryIntent.FLOW:
        return base_prompt + "\n\nINTENT: FLOW (trace entity through system)\nFocus on: Return entities from each table that connects this item through the order-delivery-invoice-payment flow.\n"
    
    elif intent == QueryIntent.AGGREGATION:
        return base_prompt + "\n\nINTENT: AGGREGATION (count, sum, metrics)\nFocus on: Use GROUP BY and aggregate functions appropriately.\n"
    
    elif intent == QueryIntent.COMPARISON:
        return base_prompt + "\n\nINTENT: COMPARISON (compare values)\nFocus on: Return comparable results with clear fields for comparison.\n"
    
    elif intent == QueryIntent.LOOKUP:
        return base_prompt + "\n\nINTENT: LOOKUP (find specific entities)\nFocus on: Return relevant entity details with related information.\n"
    
    else:
        return base_prompt + "\n\nGenerate appropriate SELECT query for the user's question.\n"
