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
- **Better LLM compatibility**: Gemini has superior SQL generation vs graph QL generation
- **Reduced complexity**: Fewer systems = faster debugging and deployment
- **Sufficient for this scope**: All required traversals (Order → Delivery → Invoice → Payment) are standard SQL joins

**Tradeoff**: Less efficient for deep recursive traversals (20+ levels). For this ERP domain with max 4-level flows, negligible impact.

### Why Gemini Over Other LLMs?
**Decision**: Google Gemini with constrained prompting

**Advantages**:
- Free tier with 60 requests/minute
- Fast response times
- Strong at SQL generation with explicit schema

### Why REST API Over GraphQL?
**Decision**: Simple REST endpoints

**Rationale**:
- Fewer abstractions = clearer error handling
- Easier to debug LLM→API→Database flow
- Query caching simpler with REST

## Design Highlights

### 1. Schema-Constrained LLM Prompting
The system prompt explicitly lists:
- Allowed tables and columns
- Valid relationships
- Forbidden keywords (DELETE, UPDATE, DROP)
- Required clauses (LIMIT enforcement)

This prevents hallucination and injection attempts at generation time.

### 2. Flow Tracing (Killer Feature)
Automatically highlights the order-to-payment journey:
```
Order #5
  ↓ (LEFT JOIN)
Delivery #12
  ↓ (LEFT JOIN)
Invoice #8
  ↓ (LEFT JOIN)
Payment #3
```

Nodes in the flow path highlight in red on the graph with animated edges.

### 3. Multi-Layer Safety
- **Input**: Domain filter blocks off-topic queries
- **Generation**: LLM constrained with schema and forbidden keywords
- **SQL**: Validator blocks unknown tables, enforces LIMIT, detects injection
- **Execution**: 5-second timeout, 1000-row limit, parameterized queries

## Feature Showcase

| Feature | Implementation |
|---------|---|
| **Natural Language Queries** | Gemini LLM with schema-constrained prompting |
| **Flow Visualization** | React Flow with path highlighting |
| **SQL Transparency** | Generated SQL shown in results panel with copy button |
| **Query Type Badge** | Shows FLOW/AGGREGATION/GENERAL classification |
| **Error States** | Clear feedback on why queries fail (domain, syntax, etc) |
| **Quick Queries** | Pre-made examples for instant testing |
| **Dataset Info** | Shows entity coverage and relationships |

## Deployment

### Local Development
```bash
./start.sh
# Opens http://localhost:5173
```

### Docker
```bash
docker-compose up -d
# Backend: http://localhost:8000
# Frontend: http://localhost:5173
# Postgres: localhost:5432
```

### Production (Neon + Render + Vercel)
See `SETUP.md` for environment variable configuration.

## Testing the System

### Test Queries

**Flow Tracing**:
- "Trace order #1 through the entire flow"
- "Show me the path from delivery #5 to payment"

**Aggregations**:
- "Total revenue by customer"
- "How many incomplete orders?"

**Lookups**:
- "List all products"
- "Show customers named 'ACME'"

**Edge Cases** (should be rejected):
- "What is 2+2?" (out of domain)
- "Delete all orders" (dangerous operation)
- "SELECT * FROM unknown_table" (schema violation)

## Architecture Deep Dive

### Backend Structure
```
backend/
├── main.py                    # FastAPI app
├── models.py                  # SQLAlchemy ORM
├── db.py                      # Database connection
├── query_engine/
│   ├── validator.py          # Domain filter + SQL validation
│   ├── intent.py             # Intent classification
│   ├── generator.py          # LLM-based SQL generation
│   ├── executor.py           # Query execution
│   └── pipeline.py           # Orchestrates all stages
└── graph/
    └── relations.py          # Graph relationships
```

### Frontend Structure
```
frontend/src/
├── App.jsx                     # Main component
├── components/
│   ├── GraphVisualization.jsx # React Flow with highlighting
│   ├── QueryInterface.jsx     # Query input with quick queries
│   ├── ResultsPanel.jsx       # Results + SQL display
│   └── FlowVisualization.jsx  # Flow-specific visualization
└── services/
    └── api.js                 # API client
```

## Why This Matters for FDE Role

This system demonstrates:

1. **Engineering Judgment** - Chose pragmatic solutions (PostgreSQL + logical graph) over complex architectures
2. **LLM Safety** - 5-stage validation pipeline with input/output guards (not just validators at end)
3. **Full-Stack Capability** - Backend, frontend, database, DevOps setup
4. **Production Thinking** - Error handling, timeouts, limits, parameterized queries
5. **Clear Communication** - System design easily explained and reasoned about

## Environment Variables

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

**"GEMINI_API_KEY not set"**
- Get key from https://makersuite.google.com/app/apikeys
- Add to backend/.env

**"Database connection failed"**
- Check DATABASE_URL is valid
- Run: `psql $DATABASE_URL -c "SELECT 1"` to test

**"Query timeout"**
- Queries limited to 5 seconds by design
- Complexity limit: max 1000 rows returned

## Future Enhancements

1. **Cached query results** - LRU cache for common queries
2. **Multi-step flows** - Chain multiple queries together
3. **Export results** - CSV/JSON download
4. **Query audit log** - Track all executed queries
5. **Custom schema** - Accept user-defined tables

---

Built for the Dodge AI Forward Deployed Engineer assessment.
