"""
Query Executor
Safely executes validated SQL queries with timeout and result limits
"""
import time
from typing import Tuple, List, Dict, Any
from sqlalchemy import text, exc
from sqlalchemy.orm import Session

# Query timeout in seconds
QUERY_TIMEOUT = 5

def execute_query(db: Session, sql: str) -> Tuple[bool, Any]:
    """
    Execute SQL query with safety guardrails
    Returns: (success, results_or_error)
    """
    
    try:
        # Add timeout (this is advisory on SQLAlchemy level)
        start_time = time.time()
        
        # Execute query
        result = db.execute(text(sql))
        
        # Check for timeout
        if time.time() - start_time > QUERY_TIMEOUT:
            return False, f"Query timeout exceeded ({QUERY_TIMEOUT}s)"
        
        # Fetch results
        rows = result.fetchall()
        
        # Convert to list of dicts
        if rows:
            columns = result.keys()
            results = [dict(zip(columns, row)) for row in rows]
        else:
            results = []
        
        # Hard limit on results
        if len(results) > 1000:
            results = results[:1000]
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        return True, {
            "rows": results,
            "count": len(results),
            "execution_time_ms": execution_time_ms
        }
    
    except exc.DatabaseError as e:
        return False, f"Database error: {str(e)}"
    except exc.OperationalError as e:
        return False, f"Connection error: {str(e)}"
    except Exception as e:
        return False, f"Execution error: {str(e)}"

def execute_flow_query(db: Session, entity_id: int, entity_type: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Execute a flow query and structure results for visualization
    Returns: (success, structured_result)
    """
    
    # Build flow query
    sql = _build_flow_sql(entity_id, entity_type)
    
    if not sql:
        return False, {"error": "Invalid entity type for flow query"}
    
    # Execute
    success, result = execute_query(db, sql)
    
    if not success:
        return False, {"error": result}
    
    # Structure result for flow visualization
    rows = result.get("rows", [])
    
    if not rows:
        return False, {"error": "Entity not found"}
    
    row = rows[0]
    
    # Extract flow entities
    flow_data = {
        "orders": None,
        "deliveries": None,
        "invoices": None,
        "payments": None,
    }
    
    # Map columns to entities
    for key, value in row.items():
        if "order_id" in key or key in ["order_date", "total"]:
            if flow_data["orders"] is None:
                flow_data["orders"] = {}
            flow_data["orders"][key] = value
        elif "delivery_id" in key or key in ["delivery_date", "status"]:
            if flow_data["deliveries"] is None:
                flow_data["deliveries"] = {}
            flow_data["deliveries"][key] = value
        elif "invoice_id" in key or key in ["amount", "issue_date"]:
            if flow_data["invoices"] is None:
                flow_data["invoices"] = {}
            flow_data["invoices"][key] = value
        elif "payment_id" in key or key in ["payment_date"]:
            if flow_data["payments"] is None:
                flow_data["payments"] = {}
            flow_data["payments"][key] = value
    
    # Clean up None values
    flow_data = {k: v for k, v in flow_data.items() if v is not None}
    
    return True, flow_data

def _build_flow_sql(entity_id: int, entity_type: str) -> str:
    """Build SQL for flow tracing"""
    
    if entity_type == "orders":
        return f"""
        SELECT 
            o.id as order_id, o.order_date, o.total,
            d.id as delivery_id, d.delivery_date, d.status,
            i.id as invoice_id, i.amount, i.issue_date,
            p.id as payment_id, p.amount as payment_amount, p.payment_date
        FROM orders o
        LEFT JOIN deliveries d ON o.id = d.order_id
        LEFT JOIN invoices i ON d.id = i.delivery_id
        LEFT JOIN payments p ON i.id = p.invoice_id
        WHERE o.id = {entity_id}
        LIMIT 1
        """
    
    elif entity_type == "deliveries":
        return f"""
        SELECT 
            o.id as order_id, o.order_date, o.total,
            d.id as delivery_id, d.delivery_date, d.status,
            i.id as invoice_id, i.amount, i.issue_date,
            p.id as payment_id, p.amount as payment_amount, p.payment_date
        FROM deliveries d
        LEFT JOIN orders o ON d.order_id = o.id
        LEFT JOIN invoices i ON d.id = i.delivery_id
        LEFT JOIN payments p ON i.id = p.invoice_id
        WHERE d.id = {entity_id}
        LIMIT 1
        """
    
    elif entity_type == "invoices":
        return f"""
        SELECT 
            o.id as order_id, o.order_date, o.total,
            d.id as delivery_id, d.delivery_date, d.status,
            i.id as invoice_id, i.amount, i.issue_date,
            p.id as payment_id, p.amount as payment_amount, p.payment_date
        FROM invoices i
        LEFT JOIN deliveries d ON i.delivery_id = d.id
        LEFT JOIN orders o ON d.order_id = o.id
        LEFT JOIN payments p ON i.id = p.invoice_id
        WHERE i.id = {entity_id}
        LIMIT 1
        """
    
    return ""
