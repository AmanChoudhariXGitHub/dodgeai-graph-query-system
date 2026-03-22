# ERP Graph Query System

A production-ready natural language query system for exploring ERP order-to-cash flows with strict safety guardrails.

## Quick Start

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql://user:pass@localhost:5432/erp"
export GEMINI_API_KEY="your_key"
python -m uvicorn main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Opens at http://localhost:5173

## System Architecture

**Three-Layer Design**: React Frontend → FastAPI Backend → PostgreSQL Database

**Query Pipeline** (5 stages with strict validation):
1. Domain Filter - Rejects out-of-domain questions
2. Intent Classification - FLOW | AGGREGATION | GENERAL
3. LLM-Based SQL Generation - Schema-constrained prompting  
4. SQL Validation - Prevents injection, enforces limits
5. Execution - Timeout + result limits

## Key Decisions & Tradeoffs

### Why PostgreSQL Over Neo4j?
**Decision**: Single database with logical graph abstraction

**Rationale**:
- **Faster iteration**: SQL generation is more reliable with LLMs than Cypher
- **Better LLM compatibility**: Gemini excels at SQL generation vs graph query languages
- **Reduced complexity**: Single system = clearer error paths and easier debugging
- **Sufficient for scope**: All required traversals (Order → Delivery → Invoice → Payment) are standard SQL joins

**Tradeoff**: Less efficient for deep recursive traversals (20+ levels). For this ERP domain with max 4-level flows, negligible.

### Why Gemini Over Other LLMs?
**Decision**: Google Gemini with constrained prompting

**Advantages**:
- Free tier: 60 requests/minute
- Fast response times (<1s)
- Superior SQL generation vs Cypher

### Why REST Over GraphQL?
**Decision**: Simple REST endpoints

**Rationale**: Fewer abstractions = clearer debugging of LLM→API→Database flow

## Design Highlights

### 1. Schema-Constrained LLM Prompting
System prompt explicitly defines:
- Allowed tables and columns
- Valid relationships
- Forbidden keywords (DELETE, UPDATE, DROP)
- Required clauses (LIMIT enforcement)

This prevents hallucination and injection at generation time, not just validation.

### 2. Flow Tracing (Differentiator)
Highlights order-to-payment journey with animated graph:
```
Order #5 → Delivery #12 → Invoice #8 → Payment #3
```
Nodes in flow path turn red with glow effect. Edges animate.

### 3. Multi-Layer Safety
- **Input**: Domain filter blocks off-topic queries
- **Generation**: LLM constrained with schema + forbidden keywords
- **SQL**: Validator blocks unknown tables, enforces LIMIT, detects injection
- **Execution**: 5-second timeout, 1000-row limit, parameterized queries

## Features

| Feature | Implementation |
|---------|---|
| **Natural Language Queries** | Gemini with schema-constrained prompting |
| **Flow Visualization** | React Flow with intelligent highlighting |
| **SQL Transparency** | Generated SQL displayed with copy button |
| **Query Classification** | Badge shows FLOW/AGGREGATION/GENERAL type |
| **Error Clarity** | Explains why queries fail (domain, syntax, schema) |
| **Quick Queries** | Pre-made examples for instant testing |
| **Dataset Overview** | Shows entity coverage |

## Test Queries

**Flow Tracing** (highlights nodes):
- "Trace order #1 through the entire flow"
- "Show the path from delivery #5 to payment"

**Aggregations**:
- "Total revenue by customer"
- "How many incomplete orders?"

**Lookups**:
- "List all products"
- "Show customers named 'ACME'"

**Rejected** (should fail gracefully):
- "What is 2+2?" (out of domain)
- "Delete all orders" (dangerous)
- "SELECT * FROM unknown_table" (schema violation)

## Deployment

### Local
```bash
./start.sh
```

### Docker
```bash
docker-compose up -d
# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

### Production (Neon + Render + Vercel)
Environment variables in SETUP.md

## Why This Design Matters

**For the FDE Role**, this demonstrates:

1. **Engineering Judgment** - Chose pragmatic solutions (single DB) over complex architectures
2. **LLM Safety** - Multi-stage validation pipeline, not just endpoint checks
3. **Full-Stack** - Backend, frontend, database, DevOps (Docker + deploy configs)
4. **Production Thinking** - Timeouts, limits, parameterized queries, error handling
5. **Explainability** - System design is simple to reason about and defend

This mirrors real SAP/Oracle ERP deployments where order-to-cash flows drive business critical operations.

## Environment

### Backend
```
DATABASE_URL=postgresql://user:pass@host:5432/erp_db
GEMINI_API_KEY=your_api_key
```

### Frontend
```
VITE_API_URL=http://localhost:8000
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "GEMINI_API_KEY not set" | Get key from https://makersuite.google.com/app/apikeys |
| "Database connection failed" | Check DATABASE_URL and run `psql $DATABASE_URL -c "SELECT 1"` |
| "Query timeout" | Queries limited to 5s by design |

## Code Structure

**Backend** (`backend/`):
- `main.py` - FastAPI app
- `query_engine/` - Pipeline stages (validator, intent, generator, executor)
- `graph/` - Relationship definitions
- `models.py` - SQLAlchemy ORM

**Frontend** (`frontend/src/`):
- `App.jsx` - Main layout
- `components/` - Graph, Query, Results panels
- `services/api.js` - Backend client

---

Built for Dodge AI Forward Deployed Engineer assessment. Demonstrates pragmatic architecture, LLM safety, and full-stack capabilities.
