"""
FastAPI Application
Main entry point for the Graph Query System backend
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uvicorn
from db import SessionLocal, init_db, get_db
from query_engine.pipeline import process_query, process_flow_trace
from graph.relations import GRAPH_RELATIONS, get_entity_color, get_entity_icon
import os

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="Graph Query System",
    description="Natural language query interface for ERP data",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class QueryRequest(BaseModel):
    query: str

class FlowTraceRequest(BaseModel):
    entity_id: int
    entity_type: str = "orders"

class QueryResponse(BaseModel):
    query: str
    success: bool
    intent: str = None
    sql: str = None
    result: Dict[str, Any] = None
    error: str = None
    flow_path: List[str] = None
    execution_time_ms: int = 0
    steps: List[Dict[str, Any]] = []

@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Graph Query System",
        "version": "1.0.0"
    }

@app.get("/health")
def health():
    """Health check"""
    return {"status": "ok"}

@app.post("/api/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest, db: Session = Depends(get_db)):
    """
    Process natural language query
    
    Example: "Show me all orders from Acme Corp"
    """
    if not request.query or len(request.query.strip()) == 0:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        result = process_query(db, request.query)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.post("/api/trace")
def trace_endpoint(request: FlowTraceRequest, db: Session = Depends(get_db)):
    """
    Trace an entity through the order-delivery-invoice-payment flow
    
    Example: Trace order #5 to payment
    """
    if request.entity_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid entity ID")
    
    try:
        result = process_flow_trace(db, request.entity_id, request.entity_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracing entity: {str(e)}")

@app.get("/api/graph")
def graph_endpoint():
    """
    Get complete graph structure
    Returns nodes and edges for visualization
    """
    nodes = []
    edges = []
    
    # Create nodes
    for entity_type in GRAPH_RELATIONS.keys():
        node = {
            "id": entity_type,
            "label": entity_type.replace("_", " ").title(),
            "color": get_entity_color(entity_type),
            "icon": get_entity_icon(entity_type),
            "type": "entity"
        }
        nodes.append(node)
    
    # Create edges
    edge_id = 0
    for from_entity, neighbors in GRAPH_RELATIONS.items():
        for to_entity in neighbors.keys():
            edge = {
                "id": f"edge-{edge_id}",
                "source": from_entity,
                "target": to_entity,
                "type": "bidirectional"
            }
            edges.append(edge)
            edge_id += 1
    
    return {
        "nodes": nodes,
        "edges": edges,
        "total_entities": len(nodes),
        "total_relationships": len(edges)
    }

@app.get("/api/graph/neighbors/{entity_type}")
def neighbors_endpoint(entity_type: str):
    """
    Get neighbors of a specific entity type
    """
    entity_type = entity_type.lower()
    
    if entity_type not in GRAPH_RELATIONS:
        raise HTTPException(status_code=404, detail=f"Entity type '{entity_type}' not found")
    
    neighbors = GRAPH_RELATIONS[entity_type]
    
    result = {
        "entity": entity_type,
        "neighbors": []
    }
    
    for neighbor_type, neighbor_info in neighbors.items():
        result["neighbors"].append({
            "type": neighbor_type,
            "color": get_entity_color(neighbor_type),
            "via": neighbor_info.get("via", "unknown")
        })
    
    return result

@app.get("/api/schema")
def schema_endpoint():
    """
    Get database schema information
    """
    schema = {
        "tables": {
            "customers": {
                "columns": ["id", "name", "email"],
                "primary_key": "id"
            },
            "products": {
                "columns": ["id", "name", "price"],
                "primary_key": "id"
            },
            "orders": {
                "columns": ["id", "customer_id", "order_date", "total", "status"],
                "primary_key": "id",
                "foreign_keys": ["customer_id → customers.id"]
            },
            "order_items": {
                "columns": ["id", "order_id", "product_id", "quantity"],
                "primary_key": "id",
                "foreign_keys": ["order_id → orders.id", "product_id → products.id"]
            },
            "deliveries": {
                "columns": ["id", "order_id", "delivery_date", "status"],
                "primary_key": "id",
                "foreign_keys": ["order_id → orders.id"]
            },
            "invoices": {
                "columns": ["id", "delivery_id", "amount", "issue_date"],
                "primary_key": "id",
                "foreign_keys": ["delivery_id → deliveries.id"]
            },
            "payments": {
                "columns": ["id", "invoice_id", "amount", "payment_date", "status"],
                "primary_key": "id",
                "foreign_keys": ["invoice_id → invoices.id"]
            }
        },
        "relationships": GRAPH_RELATIONS,
        "flow_path": ["orders", "deliveries", "invoices", "payments"]
    }
    return schema

@app.post("/api/init-data")
def init_data_endpoint(db: Session = Depends(get_db)):
    """
    Initialize sample data (for development)
    WARNING: This will clear existing data
    """
    try:
        from ingest import ingest_sample_data
        ingest_sample_data()
        return {"status": "success", "message": "Sample data loaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing data: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
