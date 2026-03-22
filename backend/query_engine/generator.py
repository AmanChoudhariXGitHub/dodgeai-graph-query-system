"""
LLM-Based SQL Generator with Hardened Constraints
Uses Google Gemini to generate SQL queries from natural language
With strict schema grounding, SQL sanitization, and validation
"""
import os
import re
from typing import Tuple
import google.generativeai as genai
from query_engine.intent import QueryIntent, get_intent_handler_prompt

# Initialize Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# STRICT SYSTEM PROMPT - Schema Constrained
BASE_SYSTEM_PROMPT = """
You are a strict SQL generator for an ERP order-to-cash dataset.

CRITICAL RULES:
1. ONLY generate SELECT queries
2. NEVER use DELETE, UPDATE, INSERT, DROP, CREATE, ALTER, or EXEC
3. ONLY use tables and columns listed below
4. ALWAYS include LIMIT 50 unless aggregation function is used
5. DO NOT hallucinate columns, tables, or schema elements
6. Use explicit JOIN conditions (no implicit joins)
7. Prefer simple queries over complex nested subqueries
8. If query cannot be answered with schema below → return: INVALID_QUERY

ALLOWED TABLES & COLUMNS:
- orders(id, customer_id, order_date, total)
- order_items(id, order_id, product_id, quantity)
- deliveries(id, order_id, delivery_date, status)
- invoices(id, delivery_id, amount, issue_date)
- payments(id, invoice_id, amount, payment_date)
- customers(id, name, email)
- products(id, name, price)

ALLOWED RELATIONSHIPS:
- orders.customer_id → customers.id
- order_items.order_id → orders.id
- order_items.product_id → products.id
- deliveries.order_id → orders.id
- invoices.delivery_id → deliveries.id
- payments.invoice_id → invoices.id

OUTPUT: Return ONLY valid SQL. No explanations. No markdown.
"""

# Few-shot examples for improved reliability
FEW_SHOT_EXAMPLES = """
EXAMPLES:
Q1: Which products have the most invoices?
A1: SELECT p.name, COUNT(i.id) as invoice_count FROM products p JOIN order_items oi ON p.id = oi.product_id JOIN orders o ON oi.order_id = o.id JOIN deliveries d ON o.id = d.order_id JOIN invoices i ON d.id = i.delivery_id GROUP BY p.name ORDER BY invoice_count DESC LIMIT 10;

Q2: Find orders without deliveries
A2: SELECT o.id FROM orders o LEFT JOIN deliveries d ON o.id = d.order_id WHERE d.id IS NULL LIMIT 50;

Q3: Trace order flow (Order → Delivery → Invoice → Payment)
A3: SELECT o.id as order_id, o.order_date, d.id as delivery_id, d.delivery_date, i.id as invoice_id, i.issue_date, p.id as payment_id, p.payment_date FROM orders o LEFT JOIN deliveries d ON o.id = d.order_id LEFT JOIN invoices i ON d.id = i.delivery_id LEFT JOIN payments p ON i.id = p.invoice_id LIMIT 50;

Q4: Unknown schema query
A4: INVALID_QUERY
"""

def generate_sql_from_nl(query: str, intent: QueryIntent) -> Tuple[bool, str]:
    """
    Generate SQL from natural language query using Gemini with strict constraints
    Returns: (success, sql_or_error)
    """
    
    if not GEMINI_API_KEY:
        return False, "GEMINI_API_KEY not set. Cannot generate SQL."
    
    try:
        # Normalize query
        query = normalize_query(query)
        
        # Get intent-specific enhancement
        intent_enhancement = get_intent_enhancement(intent)
        
        # Build constrained prompt
        full_prompt = (
            BASE_SYSTEM_PROMPT + 
            FEW_SHOT_EXAMPLES +
            intent_enhancement +
            f"\n\nUser question: {query}\n\n" +
            "Generate SQL query:"
        )
        
        # Call Gemini with strict parameters
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=500,
                temperature=0.1,  # Very low temperature for deterministic output
            )
        )
        
        if not response.text:
            return False, "No response from LLM"
        
        # Extract and sanitize SQL
        sql = response.text.strip()
        
        # Check for invalid query marker
        if "INVALID_QUERY" in sql.upper():
            return False, "Query is outside the dataset scope"
        
        # Remove markdown blocks
        sql = re.sub(r"```sql\n?", "", sql, flags=re.IGNORECASE)
        sql = re.sub(r"```\n?", "", sql)
        sql = sql.strip().rstrip(";")
        
        # Validate it's a SELECT query
        if not sql.upper().startswith("SELECT"):
            return False, "Generated query must be SELECT statement"
        
        # Sanitize and validate SQL
        sql = sanitize_sql(sql)
        
        return True, sql
        
    except Exception as e:
        return False, f"Error generating SQL: {str(e)}"

def get_intent_enhancement(intent: QueryIntent) -> str:
    """Get intent-specific prompt enhancement"""
    if intent == QueryIntent.FLOW:
        return "\nFor FLOW queries: Focus on tracing relationships step-by-step through order → delivery → invoice → payment progression."
    elif intent == QueryIntent.AGGREGATION:
        return "\nFor AGGREGATION queries: Use GROUP BY and aggregation functions (COUNT, SUM, AVG, MAX, MIN)."
    elif intent == QueryIntent.GENERAL:
        return "\nFor GENERAL queries: Keep queries simple and readable."
    return ""

def normalize_query(query: str) -> str:
    """Normalize user query"""
    return query.lower().strip()

def sanitize_sql(sql: str) -> str:
    """
    Post-generation SQL sanitization
    Enforces limits and prevents abuse
    """
    
    # Ensure LIMIT clause for non-aggregation queries
    if "GROUP BY" not in sql.upper() and "LIMIT" not in sql.upper():
        sql += " LIMIT 50"
    
    # Prevent multiple independent statements
    if sql.count(";") > 1:
        return ""  # Reject
    
    # Whitelist allowed keywords (prevent injection)
    dangerous_keywords = ["DELETE", "UPDATE", "INSERT", "DROP", "CREATE", "ALTER", "EXEC", "EXECUTE"]
    for keyword in dangerous_keywords:
        if keyword in sql.upper():
            return ""  # Reject
    
    return sql.strip()

def generate_flow_query(entity_id: int, start_table: str) -> str:
    """
    Generate a hardcoded flow query for tracing (deterministic fallback)
    Used when LLM generation fails - ensures consistent behavior
    """
    if start_table == "orders":
        return f"SELECT o.id as order_id, o.order_date, o.total, d.id as delivery_id, d.delivery_date, d.status, i.id as invoice_id, i.amount, i.issue_date, p.id as payment_id, p.amount as payment_amount, p.payment_date FROM orders o LEFT JOIN deliveries d ON o.id = d.order_id LEFT JOIN invoices i ON d.id = i.delivery_id LEFT JOIN payments p ON i.id = p.invoice_id WHERE o.id = {entity_id} LIMIT 1"
    
    elif start_table == "deliveries":
        return f"SELECT o.id as order_id, o.order_date, o.total, d.id as delivery_id, d.delivery_date, d.status, i.id as invoice_id, i.amount, i.issue_date, p.id as payment_id, p.amount as payment_amount, p.payment_date FROM deliveries d LEFT JOIN orders o ON d.order_id = o.id LEFT JOIN invoices i ON d.id = i.delivery_id LEFT JOIN payments p ON i.id = p.invoice_id WHERE d.id = {entity_id} LIMIT 1"
    
    elif start_table == "invoices":
        return f"SELECT o.id as order_id, o.order_date, o.total, d.id as delivery_id, d.delivery_date, d.status, i.id as invoice_id, i.amount, i.issue_date, p.id as payment_id, p.amount as payment_amount, p.payment_date FROM invoices i LEFT JOIN deliveries d ON i.delivery_id = d.id LEFT JOIN orders o ON d.order_id = o.id LEFT JOIN payments p ON i.id = p.invoice_id WHERE i.id = {entity_id} LIMIT 1"
    
    return ""
