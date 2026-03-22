"""
LLM-Based SQL Generator
Uses Google Gemini to generate SQL queries from natural language
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

def generate_sql_from_nl(query: str, intent: QueryIntent) -> Tuple[bool, str]:
    """
    Generate SQL from natural language query using Gemini
    Returns: (success, sql_or_error)
    """
    
    if not GEMINI_API_KEY:
        return False, "GEMINI_API_KEY not set. Cannot generate SQL."
    
    try:
        # Get intent-specific prompt
        system_prompt = get_intent_handler_prompt(intent, query)
        
        # Add special handling for FLOW queries
        flow_suffix = ""
        if intent == QueryIntent.FLOW:
            flow_suffix = "\n\nFor flow/trace queries, try to return data from connected tables showing the progression: order → delivery → invoice → payment"
        
        full_prompt = system_prompt + flow_suffix + f"\n\nUser question: {query}\n\nGenerate ONLY the SQL query, no explanation or markdown formatting. Start directly with SELECT."
        
        # Call Gemini API
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(full_prompt)
        
        if not response.text:
            return False, "No response from LLM"
        
        # Extract SQL from response
        sql = response.text.strip()
        
        # Remove markdown code blocks if present
        sql = re.sub(r"```sql\n?", "", sql, flags=re.IGNORECASE)
        sql = re.sub(r"```\n?", "", sql)
        
        # Clean up
        sql = sql.strip().rstrip(";")
        
        if not sql.upper().startswith("SELECT"):
            return False, "LLM did not generate a valid SELECT query"
        
        return True, sql
        
    except Exception as e:
        return False, f"Error generating SQL: {str(e)}"

def generate_flow_query(entity_id: int, start_table: str) -> str:
    """
    Generate a hardcoded flow query for tracing
    Used as fallback when LLM fails
    """
    if start_table == "orders":
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
    
    elif start_table == "deliveries":
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
    
    elif start_table == "invoices":
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
    
    else:
        return ""
