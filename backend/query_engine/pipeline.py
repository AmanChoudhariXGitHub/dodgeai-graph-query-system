"""
Main Query Pipeline
Orchestrates the entire query processing flow:
Domain Filter → Intent Classification → SQL Generation → Validation → Execution
"""
from typing import Tuple, Dict, Any
from sqlalchemy.orm import Session
from query_engine.validator import is_domain_query, validate_sql, extract_table_names
from query_engine.intent import classify_intent, QueryIntent
from query_engine.generator import generate_sql_from_nl
from query_engine.executor import execute_query, execute_flow_query
from graph.relations import get_flow_sequence

def process_query(db: Session, user_query: str) -> Dict[str, Any]:
    """
    Process user query through the complete pipeline
    Returns structured response with results and metadata
    """
    
    response = {
        "query": user_query,
        "success": False,
        "intent": None,
        "sql": None,
        "result": None,
        "error": None,
        "flow_path": None,
        "execution_time_ms": 0,
        "steps": []
    }
    
    # STEP 1: Domain Filter
    is_domain, domain_msg = is_domain_query(user_query)
    response["steps"].append({"step": "domain_filter", "passed": is_domain, "message": domain_msg})
    
    if not is_domain:
        response["error"] = domain_msg
        return response
    
    # STEP 2: Intent Classification
    intent, keywords = classify_intent(user_query)
    response["intent"] = intent
    response["steps"].append({"step": "intent_classification", "intent": intent.value, "keywords": keywords})
    
    # STEP 3: Special handling for FLOW queries
    if intent == QueryIntent.FLOW and keywords:
        try:
            entity_id = int(keywords[0])
            # Try to guess entity type or use "orders" as default
            entity_type = "orders"
            success, flow_result = execute_flow_query(db, entity_id, entity_type)
            
            if success:
                response["success"] = True
                response["result"] = flow_result
                response["flow_path"] = ["orders", "deliveries", "invoices", "payments"]
                response["steps"].append({"step": "flow_execution", "passed": True})
                return response
        except (ValueError, IndexError):
            pass
    
    # STEP 3b: SQL Generation (using LLM)
    success, sql_or_error = generate_sql_from_nl(user_query, intent)
    
    if not success:
        response["error"] = f"SQL generation failed: {sql_or_error}"
        response["steps"].append({"step": "sql_generation", "passed": False, "error": sql_or_error})
        return response
    
    sql = sql_or_error
    response["sql"] = sql
    response["steps"].append({"step": "sql_generation", "passed": True, "generated_sql": sql})
    
    # STEP 4: SQL Validation
    is_valid, validated_sql_or_error = validate_sql(sql)
    
    if not is_valid:
        response["error"] = f"SQL validation failed: {validated_sql_or_error}"
        response["steps"].append({"step": "sql_validation", "passed": False, "error": validated_sql_or_error})
        return response
    
    sql = validated_sql_or_error
    response["sql"] = sql
    response["steps"].append({"step": "sql_validation", "passed": True})
    
    # Extract tables for flow analysis
    tables = extract_table_names(sql)
    if tables:
        start_table = list(tables)[0]
        end_table = list(tables)[-1] if len(tables) > 1 else start_table
        flow_path = get_flow_sequence(start_table, end_table)
        if flow_path:
            response["flow_path"] = flow_path
    
    # STEP 5: Execution
    exec_success, exec_result = execute_query(db, sql)
    
    if not exec_success:
        response["error"] = f"Query execution failed: {exec_result}"
        response["steps"].append({"step": "execution", "passed": False, "error": exec_result})
        return response
    
    response["success"] = True
    response["result"] = exec_result
    response["execution_time_ms"] = exec_result.get("execution_time_ms", 0)
    response["steps"].append({"step": "execution", "passed": True, "rows_returned": exec_result.get("count", 0)})
    
    return response

def process_flow_trace(db: Session, entity_id: int, entity_type: str = "orders") -> Dict[str, Any]:
    """
    Process a flow trace request
    Returns structured response showing the flow from entity through the system
    """
    
    response = {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "success": False,
        "flow_path": [],
        "result": None,
        "error": None,
        "flow_path": ["orders", "deliveries", "invoices", "payments"]
    }
    
    success, flow_result = execute_flow_query(db, entity_id, entity_type)
    
    if success:
        response["success"] = True
        response["result"] = flow_result
    else:
        response["error"] = flow_result.get("error", "Unknown error")
    
    return response
