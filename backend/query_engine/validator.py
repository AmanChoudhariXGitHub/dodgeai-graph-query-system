"""
SQL Validator and Safety Guards
Ensures queries are safe, domain-relevant, and efficient
"""
import re
import sqlparse
from typing import Tuple

# Allowed tables
ALLOWED_TABLES = {"orders", "deliveries", "invoices", "payments", "customers", "products", "order_items"}

# Domain keywords
DOMAIN_KEYWORDS = {
    "order", "invoice", "delivery", "payment", "customer", "product",
    "billing", "shipped", "trace", "flow", "path", "purchased", "sold",
    "receipt", "amount", "status", "date", "delivery", "pending", "completed"
}

def is_domain_query(query: str) -> Tuple[bool, str]:
    """
    Check if query is about allowed domain (orders, invoices, deliveries, payments, etc.)
    Returns: (is_valid, message)
    """
    query_lower = query.lower()
    
    # Check for domain keywords
    has_domain_keyword = any(keyword in query_lower for keyword in DOMAIN_KEYWORDS)
    
    if not has_domain_keyword:
        return False, "Query must be about orders, invoices, deliveries, payments, customers, or products."
    
    # Reject out-of-domain topics
    rejected_topics = ["weather", "sports", "movies", "politics", "recipe", "math", "history"]
    if any(topic in query_lower for topic in rejected_topics):
        return False, "This query is outside the allowed domain. Ask only about ERP data."
    
    return True, "Query is in domain"

def validate_sql(sql: str) -> Tuple[bool, str]:
    """
    Validate SQL query for safety and correctness
    Returns: (is_valid, message_or_sql)
    """
    
    # Must be SELECT only
    sql_upper = sql.upper().strip()
    if not sql_upper.startswith("SELECT"):
        return False, "Only SELECT queries are allowed."
    
    # Forbid dangerous operations
    forbidden_keywords = ["DELETE", "DROP", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "EXEC", "EXECUTE"]
    for keyword in forbidden_keywords:
        if keyword in sql_upper:
            return False, f"Operation '{keyword}' is not allowed."
    
    # Check for SQL injection patterns
    dangerous_patterns = [
        r"--|/\*|\*/",  # Comments
        r";\s*\w+",      # Multiple statements
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, sql, re.IGNORECASE):
            return False, "Query contains potentially dangerous patterns."
    
    # Parse SQL and extract table names
    try:
        parsed = sqlparse.parse(sql)
        if not parsed:
            return False, "Could not parse SQL query."
        
        stmt = parsed[0]
        
        # Extract table names
        tables = set()
        from_seen = False
        for token in stmt.tokens:
            if token.ttype is None and token.value.upper() in ["FROM", "JOIN"]:
                from_seen = True
            elif from_seen and token.ttype is None:
                table_name = token.value.split()[0].lower()
                if table_name and not table_name in ["on", "using", "inner", "left", "right", "full", "cross", "where", "and", "or", "order", "group", "limit"]:
                    tables.add(table_name)
                    from_seen = False
        
        # Check if all tables are allowed
        unauthorized_tables = tables - ALLOWED_TABLES
        if unauthorized_tables:
            return False, f"Unauthorized tables: {', '.join(unauthorized_tables)}"
        
    except Exception as e:
        return False, f"Error parsing SQL: {str(e)}"
    
    # Enforce limit
    if "LIMIT" not in sql_upper:
        sql = sql.rstrip(";") + " LIMIT 50"
    else:
        # Ensure limit is reasonable (<=1000)
        limit_match = re.search(r"LIMIT\s+(\d+)", sql_upper)
        if limit_match:
            limit_val = int(limit_match.group(1))
            if limit_val > 1000:
                sql = re.sub(r"LIMIT\s+\d+", "LIMIT 1000", sql, flags=re.IGNORECASE)
    
    return True, sql

def extract_table_names(sql: str) -> set:
    """Extract table names from SQL query"""
    tables = set()
    try:
        parsed = sqlparse.parse(sql)
        if parsed:
            stmt = parsed[0]
            for token in stmt.tokens:
                if hasattr(token, 'tokens'):
                    for subtoken in token.tokens:
                        if subtoken.ttype is None and subtoken.value.lower() in ALLOWED_TABLES:
                            tables.add(subtoken.value.lower())
                elif token.ttype is None and token.value.lower() in ALLOWED_TABLES:
                    tables.add(token.value.lower())
    except:
        pass
    return tables
