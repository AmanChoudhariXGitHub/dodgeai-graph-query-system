# Architecture Documentation

Deep dive into the system design and key decisions.

## System Overview

```
┌──────────────────────────────────────────────────────────────┐
│                         Frontend (React)                     │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Query Interface    Graph Visualization    Results Panel  │  │
│  └────────────────────────────────────────────────────────┘  │
│                           ▼                                    │
│                  REST API (JSON)                              │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                          │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Query Pipeline                                        │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │ 1. Domain Filter                                 │  │  │
│  │  │ 2. Intent Classification                         │  │  │
│  │  │ 3. SQL Generation (Gemini LLM)                   │  │  │
│  │  │ 4. SQL Validation & Guardrails                   │  │  │
│  │  │ 5. Query Execution                               │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  │                                                         │  │
│  │  Graph Abstraction Layer                              │  │
│  │  - Relationships mapping                              │  │
│  │  - Flow tracing logic                                 │  │
│  │  - Entity colors & icons                              │  │
│  └────────────────────────────────────────────────────────┘  │
│                           ▼                                    │
│                    Validated SQL                              │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│               PostgreSQL Database                            │
│  - customers       - order_items                             │
│  - orders          - products                                │
│  - deliveries      - invoices                                │
│  - payments                                                  │
└──────────────────────────────────────────────────────────────┘
```

---

## Query Pipeline Architecture

### Pipeline Stages

Each query passes through 5 stages with validation at each step:

```
┌─────────────┐
│ User Query  │
└──────┬──────┘
       │
       ▼
┌──────────────────────┐
│  1. Domain Filter    │
├──────────────────────┤
│ Is query about ERP?  │
│ ✓ orders             │
│ ✓ invoices           │
│ ✗ weather            │
│ ✗ sports             │
└──────┬───────────────┘
       │ (blocked queries rejected)
       ▼
┌──────────────────────┐
│ 2. Intent Classify   │
├──────────────────────┤
│ FLOW: trace, path    │
│ AGGREGATION: count   │
│ LOOKUP: show, find   │
│ COMPARISON: vs       │
│ GENERAL: other       │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ 3. SQL Generation    │
├──────────────────────┤
│ LLM + Intent-based   │
│ schema prompt        │
│ → Gemini             │
│ ← SELECT statement   │
└──────┬───────────────┘
       │ (invalid SQL rejected)
       ▼
┌──────────────────────┐
│ 4. SQL Validation    │
├──────────────────────┤
│ ✓ SELECT only        │
│ ✗ DELETE/UPDATE      │
│ ✓ Allowed tables     │
│ ✗ Injection patterns │
│ ✓ LIMIT enforced     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ 5. Execution         │
├──────────────────────┤
│ Execute on DB        │
│ Timeout: 5s          │
│ Limit: 1000 rows     │
│ Format results       │
└──────┬───────────────┘
       │
       ▼
┌──────────────────┐
│ Structured Result│
└──────────────────┘
```

### Domain Filter (validator.py)

**Purpose**: Block off-topic queries early to prevent wasting LLM tokens

**Logic**:
```python
def is_domain_query(query):
    # ALLOW if query contains ERP keywords
    keywords = ["order", "invoice", "delivery", "payment", ...]
    has_keyword = any(kw in query.lower() for kw in keywords)
    
    # REJECT if query is about non-ERP topics
    rejected = ["weather", "sports", "recipe", ...]
    is_off_topic = any(t in query.lower() for t in rejected)
    
    return has_keyword and not is_off_topic
```

**Examples**:
- ✓ "Trace order #1" → Domain keyword "order"
- ✓ "How much did we invoice?" → Domain keywords "invoice"
- ✗ "What's the weather?" → Rejected topic
- ✗ "Recipe for pasta" → Rejected topic

### Intent Classification (intent.py)

**Purpose**: Route queries to appropriate handler based on semantic intent

**Classification Strategy**: Keyword-based (deterministic, no ML)

```python
FLOW_KEYWORDS = ["trace", "flow", "path", "journey", "follow"]
AGGREGATION_KEYWORDS = ["count", "total", "sum", "average"]
LOOKUP_KEYWORDS = ["show", "find", "list", "what", "which"]
COMPARISON_KEYWORDS = ["compare", "vs", "difference"]
```

**Why Keyword-Based?**
- No hallucination risk
- Instant processing
- Explainable routing
- Easy to debug

**Intent-Specific SQL Prompts**: Each intent gets customized LLM prompt

```python
if intent == FLOW:
    # Prompt emphasizes: return connected tables through flow
    prompt += "Focus on: Return entities linked through order→delivery→invoice→payment"
    
elif intent == AGGREGATION:
    # Prompt emphasizes: use GROUP BY and aggregate functions
    prompt += "Focus on: Use GROUP BY and aggregate functions appropriately"
```

### SQL Generation (generator.py)

**Purpose**: Convert natural language to SQL using LLM

**Process**:
1. Select intent-specific prompt template
2. Include explicit schema definition
3. Add relationship constraints
4. Add execution rules
5. Send to Gemini API
6. Extract SQL from response
7. Clean markdown formatting

**Example Prompt** (simplified):
```
You are a SQL expert for ERP data.

RULES:
- Only SELECT queries
- Use only provided schema
- No hallucinated columns
- Keep queries efficient (LIMIT 50)

SCHEMA:
- orders: id, customer_id, order_date, total
- customers: id, name, email
- ... [7 tables total]

RELATIONSHIPS:
- orders.customer_id → customers.id
- orders.id → deliveries.order_id
- ... [all relationships]

User question: "Show me all orders from Acme Corp"

Generate ONLY the SQL query, no explanation.
```

**Gemini Response**:
```sql
SELECT o.* FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE c.name = 'Acme Corp'
LIMIT 50
```

### SQL Validation (validator.py)

**Purpose**: Ensure SQL is safe before execution

**Checks** (in order):

1. **Must be SELECT**
   ```python
   if not sql.upper().startswith("SELECT"):
       return False, "Only SELECT queries allowed"
   ```

2. **Forbidden operations**
   ```python
   forbidden = ["DELETE", "DROP", "UPDATE", "INSERT", "ALTER"]
   if any(f in sql.upper() for f in forbidden):
       return False, "Operation not allowed"
   ```

3. **SQL injection patterns**
   ```python
   # Block comments
   if re.search(r"--|/\*|\*/", sql):
       return False, "Query contains dangerous patterns"
   
   # Block multiple statements
   if re.search(r";\s*\w+", sql):
       return False, "Multiple statements not allowed"
   ```

4. **Table whitelist**
   ```python
   allowed = {"orders", "deliveries", "invoices", "payments", 
              "customers", "products", "order_items"}
   for table in extracted_tables:
       if table not in allowed:
           return False, f"Unauthorized table: {table}"
   ```

5. **Result limiting**
   ```python
   if "LIMIT" not in sql.upper():
       sql += " LIMIT 50"
   if limit > 1000:
       sql = sql.replace(f"LIMIT {limit}", "LIMIT 1000")
   ```

### Query Execution (executor.py)

**Purpose**: Execute validated SQL and format results

**Safety Features**:
- 5-second timeout
- 1000-row hard limit
- Transaction isolation
- Error handling

**Execution Flow**:
```python
def execute_query(db, sql):
    try:
        # Execute with timeout
        result = db.execute(text(sql))
        
        # Fetch and convert to list of dicts
        rows = result.fetchall()
        results = [dict(zip(columns, row)) for row in rows]
        
        # Hard limit
        results = results[:1000]
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        return True, {
            "rows": results,
            "count": len(results),
            "execution_time_ms": int(execution_time * 1000)
        }
    except DatabaseError as e:
        return False, f"Database error: {str(e)}"
```

---

## Graph Abstraction Layer

### Logical Graph Model

The system doesn't use a separate graph database. Instead, it maintains a logical graph model in Python:

```python
GRAPH_RELATIONS = {
    "orders": {
        "customers": {"table": "customers", "via": "customer_id"},
        "deliveries": {"table": "deliveries", "via": "order_id"},
        "order_items": {"table": "order_items", "via": "order_id"},
    },
    "deliveries": {
        "orders": {"table": "orders", "via": "order_id"},
        "invoices": {"table": "invoices", "via": "delivery_id"},
    },
    "invoices": {
        "deliveries": {"table": "deliveries", "via": "delivery_id"},
        "payments": {"table": "payments", "via": "invoice_id"},
    },
    # ... more relationships
}
```

### Why Logical Graph (Not Neo4j)?

| Aspect | Logical Graph | Neo4j |
|--------|---|---|
| **Complexity** | Simple, maintained in code | Separate DB, sync issues |
| **LLM Integration** | SQL is natural for LLMs | Cypher is less natural |
| **Failure Points** | One DB connection | Two DBs to coordinate |
| **Development Speed** | Fast, iterate quickly | Slower setup, more setup |
| **Query Language** | SQL (LLMs know it well) | Cypher (less common) |
| **For This Use Case** | Sufficient | Overkill |

### Benefits

1. **Single Source of Truth**: All relationships defined in one place
2. **Type-Safe**: Defined in Python, IDEs can validate
3. **Flexible**: Can be updated without schema migration
4. **Queryable**: Python code can traverse relationships
5. **Visual**: Used to generate graph visualizations

### Flow Path Tracing

```python
FLOW_PATH = ["orders", "deliveries", "invoices", "payments"]

def get_flow_sequence(start_table, end_table):
    """Get path between two tables"""
    start_idx = FLOW_PATH.index(start_table)
    end_idx = FLOW_PATH.index(end_table)
    return FLOW_PATH[start_idx:end_idx+1]
```

**Example**:
- `get_flow_sequence("orders", "payments")` → `["orders", "deliveries", "invoices", "payments"]`
- `get_flow_sequence("deliveries", "invoices")` → `["deliveries", "invoices"]`

---

## Frontend Architecture

### Component Hierarchy

```
App
├── Header
├── Main Content
│   ├── Left: GraphVisualization
│   │   ├── ReactFlow
│   │   │   ├── Nodes (7 entities)
│   │   │   ├── Edges (relationships)
│   │   │   ├── Controls
│   │   │   └── MiniMap
│   │   └── Styling (colors, animations)
│   │
│   └── Right: Sidebar
│       ├── QueryInterface
│       │   ├── Input textarea
│       │   ├── Submit button
│       │   └── Quick query buttons
│       │
│       └── ResultsPanel
│           ├── Success/Error indicator
│           ├── FlowVisualization (if applicable)
│           │   └── Entity flow cards
│           │   └── Detailed views
│           │
│           └── Results table
│               └── Expandable rows
```

### Data Flow

```
User Input
    ↓
QueryInterface
    ↓
onQuery() callback
    ↓
API call (queryAPI.query)
    ↓
Backend processing
    ↓
Response
    ↓
setQueryResult(response)
    ↓
ResultsPanel renders
    ↓
Display results
```

### React Flow Integration

**Why React Flow?**
- Purpose-built for graph visualization
- Handles layout automatically
- Touch-friendly controls
- Performant (uses canvas)
- Customizable styling

**Usage**:
```jsx
<ReactFlow
  nodes={nodes}           // [{ id, data, position, style }]
  edges={edges}           // [{ id, source, target, animated }]
  onNodesChange={handler} // Updates position
  onEdgesChange={handler} // Edge updates
  onNodeClick={handler}   // Selection
>
  <Background />
  <Controls />
  <MiniMap />
</ReactFlow>
```

### API Integration (services/api.js)

**Centralized API Client** using Axios:

```javascript
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
})

export const queryAPI = {
  query(query) {...},          // POST /api/query
  trace(id, type) {...},        // POST /api/trace
  getGraph() {...},             // GET /api/graph
  getNeighbors(type) {...},     // GET /api/graph/neighbors/:type
  getSchema() {...},            // GET /api/schema
  initData() {...},             // POST /api/init-data
  health() {...},               // GET /health
}
```

---

## Database Schema

### Entity-Relationship Diagram

```
┌─────────────┐        ┌──────────────┐
│ CUSTOMERS   │        │ PRODUCTS     │
├─────────────┤        ├──────────────┤
│ id (PK)     │        │ id (PK)      │
│ name        │        │ name         │
│ email       │        │ price        │
└─────────────┘        └──────────────┘
      ▲                       ▲
      │                       │
      │ FK                    │ FK
      │ customer_id           │ product_id
      │                       │
┌─────────────┐        ┌──────────────┐
│ ORDERS      │        │ ORDER_ITEMS  │
├─────────────┤        ├──────────────┤
│ id (PK)     │◄───────│ order_id (FK)│
│ customer_id │        │ product_id (F│
│ order_date  │        │ quantity     │
│ total       │        └──────────────┘
│ status      │
└─────────────┘
      │
      │ FK order_id
      │
┌─────────────────┐
│ DELIVERIES      │
├─────────────────┤
│ id (PK)         │
│ order_id (FK)   │
│ delivery_date   │
│ status          │
└─────────────────┘
      │
      │ FK delivery_id
      │
┌─────────────────┐
│ INVOICES        │
├─────────────────┤
│ id (PK)         │
│ delivery_id (FK)│
│ amount          │
│ issue_date      │
└─────────────────┘
      │
      │ FK invoice_id
      │
┌─────────────────┐
│ PAYMENTS        │
├─────────────────┤
│ id (PK)         │
│ invoice_id (FK) │
│ amount          │
│ payment_date    │
│ status          │
└─────────────────┘
```

### Indexes

All foreign keys and commonly filtered fields have indexes:

```python
# In models.py
orders.id = Column(Integer, primary_key=True, index=True)
orders.customer_id = Column(Integer, ForeignKey(...), index=True)
orders.order_date = Column(DateTime, index=True)
invoices.amount = Column(Float, index=True)
# ... etc
```

---

## API Design

### RESTful Principles

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/query` | POST | Execute natural language query |
| `/api/trace` | POST | Trace entity through flow |
| `/api/graph` | GET | Get entity relationship graph |
| `/api/graph/neighbors/{type}` | GET | Get connected entities |
| `/api/schema` | GET | Get database schema |
| `/health` | GET | Health check |

### Request/Response Examples

**Query Request**:
```json
{
  "query": "Trace order #1"
}
```

**Query Response**:
```json
{
  "success": true,
  "query": "Trace order #1",
  "intent": "FLOW",
  "sql": "SELECT ... FROM orders ...",
  "result": {
    "rows": [{...}],
    "count": 1,
    "execution_time_ms": 145
  },
  "flow_path": ["orders", "deliveries", "invoices", "payments"],
  "steps": [
    {"step": "domain_filter", "passed": true},
    {"step": "intent_classification", "intent": "FLOW"},
    ...
  ]
}
```

---

## Security Model

### Threat Model

| Threat | Mitigation |
|--------|-----------|
| Off-topic queries | Domain filter rejects early |
| SQL injection | Regex validation + parameterized queries |
| Resource exhaustion | Result limits + timeout |
| Unauthorized table access | Table whitelist |
| Malicious SQL operations | Operation whitelist (SELECT only) |
| LLM token abuse | Limited API key quota |
| Data exfiltration | No PII in sample data |

### Defense in Depth

```
┌─────────────────────────────────────────┐
│ Attack Vector → Defense Layer           │
├─────────────────────────────────────────┤
│ Off-domain question → Domain Filter     │
│ Bad SQL syntax → Intent classifier      │
│ Dangerous SQL → SQL Validator           │
│ Resource attack → Execution timeout     │
│ Data theft → Result limits (1000 rows)  │
└─────────────────────────────────────────┘
```

---

## Performance Characteristics

### Query Performance

| Operation | Typical Time | Notes |
|-----------|------|-------|
| Domain filter | <1ms | Regex match |
| Intent classification | <1ms | Keyword lookup |
| LLM generation | 1-2s | Gemini API call |
| SQL validation | <5ms | Regex + parsing |
| Query execution | 50-200ms | Database dependent |
| Result formatting | <10ms | List comprehension |
| **Total** | **1.1-2.2s** | Gemini dominates |

### Scalability

| Metric | Limit | Notes |
|--------|-------|-------|
| Concurrent users | ~100 | Per backend instance |
| Concurrent queries | Limited by DB | Pool size: 5-20 |
| Result size | 1000 rows | Hard limit |
| Query timeout | 5 seconds | Hard limit |
| Rows per table | 1M+ | With proper indexes |

### Optimization Opportunities

1. **LLM Caching**: Cache generated SQL for identical queries
2. **Connection Pooling**: Already configured in SQLAlchemy
3. **Query Result Caching**: Use Redis for frequent queries
4. **Batch Processing**: Process multiple queries in parallel
5. **Index Optimization**: Already applied to all FK/frequent filters

---

## Deployment Architecture

### Local Development

```
Dev Machine
├── Backend (Python 3.11)
│   ├── FastAPI server (port 8000)
│   └── SQLite or local PostgreSQL
├── Frontend (Node.js)
│   ├── Vite dev server (port 5173)
│   └── Hot module reloading
└── Browser
    └── http://localhost:5173
```

### Production (Render + Vercel)

```
Internet
    │
    ├─→ Vercel Edge Network
    │   └─→ Frontend (static + React)
    │
    └─→ Render
        ├─→ Backend (FastAPI)
        │   └─→ Connection pool
        │
        └─→ Neon (PostgreSQL)
            └─→ Data storage
```

### Docker Deployment

```
Docker Host
├── postgres (PostgreSQL 15)
├── backend (Python 3.11)
│   └── FastAPI via Uvicorn
└── frontend (Node.js)
    └── Vite dev server
```

---

## Error Handling

### Backend Error Types

| Error | Status | Response |
|-------|--------|----------|
| Query missing | 400 | `{"detail": "Query cannot be empty"}` |
| Domain rejected | 200 | `{"success": false, "error": "..."}` |
| SQL generation failed | 200 | `{"success": false, "error": "..."}` |
| SQL invalid | 200 | `{"success": false, "error": "..."}` |
| Execution error | 200 | `{"success": false, "error": "..."}` |
| Server error | 500 | `{"detail": "..."}` |

### Frontend Error Handling

```jsx
try {
  const result = await queryAPI.query(query);
  setQueryResult(result);
} catch (err) {
  setError(`Query failed: ${err.message}`);
}
```

---

## Configuration Management

### Environment Variables

```
Backend:
  DATABASE_URL      → PostgreSQL connection
  GEMINI_API_KEY    → LLM access
  PORT              → Server port
  DEBUG             → Debug logging

Frontend:
  VITE_API_URL      → Backend URL
```

### Configuration Patterns

**Feature Flags**:
```python
ENABLE_FLOW_TRACING = True
ENABLE_AGGREGATIONS = True
DEBUG_SQL = False
```

**Rate Limits**:
```python
QUERY_TIMEOUT = 5  # seconds
MAX_RESULT_ROWS = 1000
MAX_RESULT_SIZE = 10_000_000  # bytes
```

---

## Testing Strategy

### Backend Tests

```python
# test_validator.py
def test_domain_filter_accepts_erp_queries()
def test_domain_filter_rejects_off_topic()
def test_sql_validation_blocks_delete()

# test_pipeline.py
def test_full_query_pipeline()
def test_flow_tracing()

# test_executor.py
def test_query_timeout()
def test_result_limiting()
```

### Frontend Tests

```javascript
// __tests__/QueryInterface.test.jsx
test('submits query on button click')
test('shows loading state during request')

// __tests__/ResultsPanel.test.jsx
test('displays results in table')
test('shows flow visualization for flow queries')
```

### Integration Tests

```python
# test_e2e.py
def test_full_user_flow():
    # Query → Backend → Database → Frontend display
```

---

## Future Improvements

1. **Caching Layer**: Redis for frequent queries
2. **Monitoring**: Datadog/New Relic for production
3. **Analytics**: Track query patterns, popular questions
4. **Multi-language**: Support queries in multiple languages
5. **Advanced Visualization**: 3D graph or timeline views
6. **Query Explanation**: Explain WHY results were returned
7. **Feedback Loop**: User feedback to improve LLM prompts
8. **Custom Models**: Fine-tune Gemini on company-specific data

---

This architecture balances simplicity, safety, and functionality for the assessment criteria while demonstrating solid engineering judgment.
