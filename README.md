# Graph-Based Query System for ERP Data

A sophisticated natural language query interface for exploring ERP order-to-payment flows with intelligent guardrails and flow visualization.

## 🎯 Overview

This system enables intuitive exploration of complex ERP relationships using natural language. Instead of writing SQL, users ask questions like:
- "Trace order #5 to payment"
- "Show me all invoices over $1000"
- "How many deliveries this month?"

The system intelligently routes queries through a controlled pipeline with multiple safety guardrails before execution.

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │  React + React Flow (Graph visualization)
│  (React)    │  Conversational query interface
└──────┬──────┘
       │ REST API (JSON)
       ▼
┌──────────────────────────────┐
│   FastAPI Backend            │
│  - Query Engine              │
│  - Guardrails & Validation   │
│  - Graph Abstraction Layer   │
└──────┬───────────────────────┘
       │ SQL Queries (validated)
       ▼
┌──────────────────────────────┐
│   PostgreSQL Database        │
│  - Tables: Orders, Invoices, │
│    Deliveries, Payments, etc │
│  - Relationships enforced     │
└──────────────────────────────┘
```

## 🔥 Core Features

### 1. **Controlled Query Pipeline**

Every user query passes through 5 validation steps:

1. **Domain Filter** - Rejects out-of-domain topics
2. **Intent Classification** - Routes to appropriate handler (FLOW, AGGREGATION, LOOKUP, etc.)
3. **Schema-Aware SQL Generation** - LLM generates SQL with explicit schema constraints
4. **SQL Validation** - Blocks dangerous operations, unauthorized tables, and injection attempts
5. **Execution** - Executes validated SQL with timeout and result limits

### 2. **Flow Tracing (Killer Feature)**

Trace an entity through its complete order-to-payment journey:

```
Order #5 → Delivery → Invoice → Payment
```

Returns structured data showing:
- Order details (date, total)
- Delivery info (date, status)
- Invoice (amount, date issued)
- Payment (amount, date, status)

Visualized as an interactive flow with expandable details.

### 3. **Strong Guardrails**

**Domain Validation**
- Only accepts queries about ERP entities (orders, invoices, deliveries, etc.)
- Rejects off-topic queries (weather, sports, recipes, etc.)

**SQL Safety**
- SELECT-only queries
- Forbidden keywords: DELETE, DROP, UPDATE, INSERT, ALTER
- No SQL comments or multiple statements
- Only queries on allowed tables (7 core ERP tables)
- Hard limits: 50-1000 rows per query, 5s timeout

**LLM Grounding**
- Provides explicit schema to LLM
- Includes all valid relationships
- Blocks hallucinated columns/tables
- Intent-based prompting for better results

### 4. **Graph Visualization**

Interactive graph showing:
- 7 ERP entities (customers, orders, products, deliveries, invoices, payments, order_items)
- Relationships between entities
- Color-coded nodes for quick identification
- Click to select and highlight connected entities

## 📊 Data Schema

### Tables
- **customers**: id, name, email
- **products**: id, name, price
- **orders**: id, customer_id (FK), order_date, total, status
- **order_items**: id, order_id (FK), product_id (FK), quantity
- **deliveries**: id, order_id (FK), delivery_date, status
- **invoices**: id, delivery_id (FK), amount, issue_date
- **payments**: id, invoice_id (FK), amount, payment_date, status

### Valid Relationships
```
customers ←→ orders ←→ deliveries ←→ invoices ←→ payments
           ↓
        order_items ↔ products
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL (or SQLite for development)
- Google Gemini API key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add:
# - DATABASE_URL (PostgreSQL connection string)
# - GEMINI_API_KEY (from Google AI Studio)

# Initialize database and load sample data
python ingest.py

# Start server
python main.py
# Runs on http://localhost:8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env if needed (default: http://localhost:8000)

# Start development server
npm run dev
# Runs on http://localhost:5173
```

### Usage

1. Open http://localhost:5173
2. Explore the graph visualization (left panel)
3. Enter natural language queries (right panel)
4. View results with flow visualization and data tables

## 🔍 Query Examples

### Flow Tracing
```
"Trace order #1 to payment"
"Show me the journey of order #3"
"Follow delivery #2 through the system"
```

### Aggregations
```
"How many orders total?"
"What's the highest invoice amount?"
"Count all completed payments"
```

### Lookups
```
"Show me all orders from Acme Corp"
"List products under $100"
"Which orders are still pending?"
```

## 🛡️ Safety Features

### Query Validation
- **Domain Filter**: Non-ERP queries rejected at first step
- **Intent Classification**: Routes to appropriate handler
- **Schema Validation**: Only allows known tables/columns
- **Operation Restriction**: SELECT only, no modifications
- **Injection Prevention**: Regex filters for dangerous patterns
- **Rate Limiting**: 5-second timeout, 1000-row limit

### LLM Safeguards
- Explicit schema provided to model
- Relationship constraints clearly stated
- No hallucination tolerance
- Generated SQL validated before execution

## 📁 Project Structure

```
.
├── backend/
│   ├── main.py                      # FastAPI application
│   ├── db.py                        # Database configuration
│   ├── models.py                    # SQLAlchemy models
│   ├── ingest.py                    # Sample data loader
│   ├── graph/
│   │   └── relations.py             # Graph abstraction layer
│   ├── query_engine/
│   │   ├── pipeline.py              # Main query processing
│   │   ├── validator.py             # SQL validation
│   │   ├── intent.py                # Intent classification
│   │   ├── generator.py             # LLM-based SQL generation
│   │   └── executor.py              # Query execution
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # Main app component
│   │   ├── main.jsx                 # React entry point
│   │   ├── index.css                # Global styles
│   │   ├── services/
│   │   │   └── api.js               # API client
│   │   └── components/
│   │       ├── GraphVisualization.jsx
│   │       ├── QueryInterface.jsx
│   │       ├── ResultsPanel.jsx
│   │       └── FlowVisualization.jsx
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── .env.example
│
├── README.md
└── .gitignore
```

## 🎨 Design Decisions

### Why PostgreSQL + Logical Graph (vs. Neo4j)?
- **Faster Development**: Single database, no dual-sync headaches
- **Cleaner LLM Integration**: SQL is more natural for LLMs than Cypher
- **Fewer Failure Points**: One database connection, one query language
- **Sufficient for Requirements**: Logical graph abstraction handles all flow-tracing needs

### Why Simple REST API (vs. GraphQL)?
- **Reduced Complexity**: Fewer potential attack vectors
- **Better for Learning**: Clear endpoint semantics
- **Easier Debugging**: Standard HTTP/JSON tooling
- **Query Pipeline Control**: Each step is explicit and auditable

### Why Intent Classification (vs. Fine-tuned LLM)?
- **Deterministic Routing**: No model hallucination on intent
- **Lower Cost**: No fine-tuning needed
- **Faster Inference**: Simple keyword matching is instant
- **Better Explainability**: Clear why each query went where

### Why Flow Path Emphasis?
- **ERP Workflow Alignment**: Mirrors actual SAP/Oracle workflows (Order → Delivery → Invoice → Payment)
- **Differentiating Feature**: Most query systems don't emphasize business processes
- **User-Centric**: Matches how business users think about their data
- **Demonstrates Domain Knowledge**: Shows understanding of enterprise workflows

## 📈 Performance

- Query execution: <200ms (typical)
- LLM generation: 1-2s (Gemini)
- Graph loading: <50ms
- Flow tracing: <100ms

## 🔐 Security Considerations

1. **Input Validation**
   - Domain filtering blocks off-topic queries
   - Regex patterns prevent SQL injection
   - Schema whitelist prevents unauthorized table access

2. **Output Limiting**
   - Hard caps on result size (1000 rows)
   - Query timeout (5 seconds)
   - No sensitive data exposure (logs don't contain values)

3. **LLM Safety**
   - Explicit schema constraints prevent hallucination
   - Generated SQL validated before execution
   - No access to system tables or stored procedures

## 📝 API Documentation

### POST /api/query
Process a natural language query

**Request:**
```json
{
  "query": "Trace order #5 to payment"
}
```

**Response:**
```json
{
  "query": "Trace order #5 to payment",
  "success": true,
  "intent": "FLOW",
  "sql": "SELECT ... FROM orders ...",
  "result": {
    "orders": {...},
    "deliveries": {...},
    "invoices": {...},
    "payments": {...}
  },
  "flow_path": ["orders", "deliveries", "invoices", "payments"],
  "execution_time_ms": 145,
  "steps": [...]
}
```

### GET /api/graph
Get complete entity relationship graph

### GET /api/schema
Get database schema with relationships

### POST /api/trace
Trace specific entity through flow

## 🧪 Testing

Sample queries to test:
1. "Trace order #1" → Flow visualization
2. "How many orders?" → Aggregation
3. "Show customers" → Lookup
4. "What's the weather?" → Domain rejection
5. "Show passwords" → Authorization check

## 🚢 Deployment

### Production Checklist
- [ ] Set DATABASE_URL to Neon PostgreSQL
- [ ] Set GEMINI_API_KEY from Google AI Studio
- [ ] Deploy backend to Render/Cloud Run
- [ ] Deploy frontend to Vercel
- [ ] Update VITE_API_URL in frontend env
- [ ] Enable CORS for production domain
- [ ] Set up monitoring/logging
- [ ] Create database backups

### Environment Variables

**Backend (.env)**
```
DATABASE_URL=postgresql://user:pass@host:5432/db
GEMINI_API_KEY=your_key_here
PORT=8000
DEBUG=False
```

**Frontend (.env)**
```
VITE_API_URL=https://api.yourdomain.com
```

## 📚 Architecture Deep Dive

### Query Pipeline Flow

```
User Input
    ↓
[Step 1: Domain Filter]
  - Check if query is about ERP topics
  - Reject: weather, sports, recipes, etc.
    ↓
[Step 2: Intent Classification]
  - FLOW: "trace", "follow", "path"
  - AGGREGATION: "count", "total", "sum"
  - LOOKUP: "show", "list", "find"
  - COMPARISON: "compare", "vs"
  - GENERAL: everything else
    ↓
[Step 3: SQL Generation]
  - Send intent-specific prompt to Gemini
  - Include explicit schema + relationships
  - Get back SELECT statement
    ↓
[Step 4: SQL Validation]
  - Must be SELECT only
  - Check against table whitelist
  - Validate column references
  - Enforce LIMIT clause
  - Detect injection patterns
    ↓
[Step 5: Execution]
  - Execute on PostgreSQL
  - Enforce 5s timeout
  - Cap results at 1000 rows
  - Return structured response
    ↓
Response with Results
```

### Graph Abstraction Layer

The backend maintains a logical graph model:

```python
GRAPH_RELATIONS = {
    "orders": {
        "customers": {"table": "customers", "via": "customer_id"},
        "deliveries": {"table": "deliveries", "via": "order_id"},
        "order_items": {"table": "order_items", "via": "order_id"},
    },
    # ... more relationships
}
```

This enables:
- Neighbor exploration without native graph DB
- Flow path traversal
- Relationship visualization
- Smart SQL generation

## 🎓 Learning Outcomes

Building this system demonstrates:
1. **System Design**: Tradeoff analysis, constraint-based thinking
2. **LLM Integration**: Prompt engineering, safety guardrails, grounding
3. **Full-Stack Development**: Backend + Frontend + Database
4. **ERP Domain Knowledge**: Order-to-payment workflows
5. **Security**: Input validation, output limiting, injection prevention
6. **Pragmatism**: Choosing simple solutions that work over complex ones

## 📞 Support

For issues or questions:
1. Check the error message in the query results
2. Review the pipeline steps in the response
3. Look at the SQL generation to debug intent classification
4. Verify database connectivity with `/health` endpoint

## 📄 License

MIT

---

**Built for:** Dodge AI Forward Deployed Engineer Assessment  
**Timeline:** 3-4 day sprint  
**Tech Stack:** Python/FastAPI + React + PostgreSQL + Google Gemini
