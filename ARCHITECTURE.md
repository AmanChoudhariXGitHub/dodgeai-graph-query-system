# Architecture: Key Decisions

## System Design

```
React Frontend → FastAPI Backend → PostgreSQL Database
                (5-stage pipeline)
```

## The 5-Stage Query Pipeline

Every query goes through controlled validation before execution:

1. **Domain Filter** - Reject off-topic questions (keywords + semantic check)
2. **Intent Classification** - Route to FLOW | AGGREGATION | GENERAL handler
3. **LLM SQL Generation** - Schema-constrained prompting with Gemini
4. **SQL Validation** - Blocks dangerous operations, enforces limits
5. **Execution** - Parameterized queries, 5s timeout, 1000-row limit

## Why These Decisions?

### PostgreSQL vs Neo4j

| Factor | PostgreSQL | Neo4j |
|--------|-----------|-------|
| LLM SQL Gen | Excellent | Cypher weaker |
| Complexity | Simple | Higher |
| Single Source | Yes | Dual systems |
| Sufficient for 4-level flows | Yes | Yes |

**Decision**: PostgreSQL with logical graph abstraction

**Rationale**: For order→delivery→invoice→payment flows (max 4 levels), SQL JOINs are sufficient. Gemini generates more reliable SQL than Cypher. Single database = faster iteration and debugging.

**Tradeoff**: Would switch to Neo4j if flows exceed 8+ levels (deep recursion becomes painful in SQL).

### Schema-Constrained LLM Prompting

Most systems do: `LLM → SQL → THEN validate`

We do: `CONSTRAIN at generation → THEN validate as backup`

**System Prompt Includes**:
```
ALLOWED TABLES: orders, deliveries, invoices, payments, customers, products, order_items

RELATIONSHIPS:
- orders.customer_id → customers.id
- deliveries.order_id → orders.id
- invoices.delivery_id → deliveries.id
- payments.invoice_id → invoices.id

FORBIDDEN: DELETE, UPDATE, INSERT, DROP, CREATE, ALTER

RULES:
1. ONLY SELECT queries
2. ALWAYS LIMIT 50 unless aggregation
3. Use explicit JOINs (no implicit)
```

**Few-shot examples** for each intent type guide generation.

**Temperature**: 0.1 for deterministic output.

**Why**: LLM-constrained generation is more reliable than post-validation. This is the real differentiator for LLM safety.

### Gemini Over Other LLMs

| Provider | SQL Gen | Free Tier | Speed | Cost |
|----------|---------|-----------|-------|------|
| Gemini | ⭐⭐⭐⭐⭐ | 60 req/min | <1s | Free |
| Claude | ⭐⭐⭐⭐ | None | 1-2s | Paid |
| Groq | ⭐⭐⭐⭐ | Yes | <500ms | Free |

**Decision**: Gemini

**Rationale**: Best SQL generation quality, free tier sufficient for evaluation, fast enough for interactive use.

**Fallback**: If Gemini fails, use deterministic pre-written queries for common patterns.

## Multi-Layer Safety

```
Domain Filter (Block off-topic)
        ↓
Intent Classification (Route to handler)
        ↓
LLM Generation (Schema-constrained)
        ↓
SQL Validation (Forbidden keywords, table whitelist, injection patterns)
        ↓
Safe Execution (Parameterized queries, timeout, limits)
```

**Defense in Depth Principle**: Never rely on one layer. Each stage can catch different attack vectors.

## Flow Tracing Feature

When user asks "Trace order #1":

1. Query hits `/api/trace` endpoint
2. Backend executes flow query: `SELECT ... FROM orders LEFT JOIN deliveries LEFT JOIN invoices LEFT JOIN payments WHERE order_id = 1`
3. Returns: `{flow_path: ["orders", "deliveries", "invoices", "payments"], result: {...}}`
4. Frontend highlights these nodes RED with animated edges
5. Shows step-by-step progression with data at each level

**Why It Matters**: This is exactly what SAP/Oracle users need for ERP operations. Visualizing order-to-cash flows is a real business requirement.

## REST API Design

Simple endpoints, not GraphQL:

```
POST /api/query           → Execute natural language query
POST /api/trace/:id/:type → Trace entity through flow
GET  /api/graph           → Get entity relationship graph
GET  /api/schema          → Get allowed tables/columns
```

**Why**: Fewer abstractions = easier to debug LLM→API→Database flow. Clear error propagation.

## Production Readiness

**Implemented**:
- ✅ Error handling at each stage
- ✅ Input validation
- ✅ Parameterized queries (prevents injection at DB level)
- ✅ Timeout protection (5s max)
- ✅ Result limits (1000 rows, max)
- ✅ Environment variable management
- ✅ Docker deployment
- ✅ CORS configuration

**Not Implemented** (Out of scope):
- Authentication/Authorization
- Query audit logging
- Rate limiting beyond API key quota
- Query caching
- Metrics dashboard

## Why This Matters for FDE Role

**This architecture demonstrates**:

1. **Engineering Judgment** - Pragmatic decisions (PostgreSQL over Neo4j for this scope)
2. **LLM Safety** - Multi-stage validation pipeline, constraints at generation time
3. **Full-Stack** - Backend, frontend, database, DevOps (Docker + deploy setup)
4. **Production Thinking** - Timeouts, limits, parameterized queries, error paths
5. **Clear Communication** - Design is simple to reason about, tradeoffs explicitly documented

This mirrors **real ERP deployments** where order-to-cash flows drive business-critical operations. The ability to safely expose complex queries through natural language is a high-value feature in SAP/Oracle environments.

## Known Limitations

1. **No authentication** - Assumes trusted environment
2. **Single database user** - All queries run as same user
3. **No caching** - Every query hits database
4. **LLM latency** - 1-2s per query (acceptable for interactive use)
5. **Logical graphs only** - No recursive traversals beyond 4 levels

---

This is a pragmatic, defensible architecture that solves the core problem: **safely translate natural language to SQL for ERP queries with strict safety guardrails**.
