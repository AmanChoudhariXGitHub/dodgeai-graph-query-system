# Testing Guide

Complete guide to testing the Graph Query System.

## Quick Test Checklist

Run these tests after startup to verify functionality:

- [ ] Backend API responds at http://localhost:8000/health
- [ ] Frontend loads at http://localhost:5173
- [ ] Graph visualization displays 7 entities
- [ ] Sample data is loaded in database
- [ ] Query: "Trace order #1" returns flow visualization
- [ ] Query: "Show all orders" returns results
- [ ] Query: "What's the weather?" is rejected (off-domain)

---

## Backend Testing

### Health Check

```bash
# Test API is running
curl http://localhost:8000/health

# Expected response:
# {"status": "ok"}
```

### Schema Verification

```bash
# Get database schema
curl http://localhost:8000/api/schema

# Should return:
# {
#   "tables": {
#     "orders": {...},
#     "invoices": {...},
#     ...
#   },
#   "relationships": {...},
#   "flow_path": ["orders", "deliveries", "invoices", "payments"]
# }
```

### Graph Endpoint

```bash
# Get entity relationships
curl http://localhost:8000/api/graph

# Should return:
# {
#   "nodes": [
#     {"id": "orders", "label": "Orders", "color": "#3B82F6", ...},
#     ...
#   ],
#   "edges": [...],
#   "total_entities": 7,
#   "total_relationships": 7
# }
```

### Query Tests

#### Test 1: Simple Lookup

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show all orders"}'
```

**Expected Response**:
- `"success": true`
- `"intent": "LOOKUP"` or `"GENERAL"`
- `"result"` contains rows with order data
- `"execution_time_ms"` present

#### Test 2: Flow Tracing

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Trace order #1"}'
```

**Expected Response**:
- `"success": true`
- `"intent": "FLOW"`
- `"flow_path": ["orders", "deliveries", "invoices", "payments"]`
- `"result"` contains entities: orders, deliveries, invoices, payments

#### Test 3: Aggregation

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How many orders total?"}'
```

**Expected Response**:
- `"success": true`
- `"intent": "AGGREGATION"`
- `"result"` contains count value

#### Test 4: Domain Rejection

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the weather?"}'
```

**Expected Response**:
- `"success": false`
- `"error": "Query must be about orders, invoices..."
- `"steps"[0].passed: false`

#### Test 5: Unauthorized Table Access

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me users table"}'
```

**Expected Response**:
- `"success": false`
- `"error": "Unauthorized tables..."` or domain rejection

### SQL Validation Tests

These tests verify the SQL validation guardrails:

#### Test: DELETE Prevention

```python
# In backend test
sql = "DELETE FROM orders WHERE id = 1"
is_valid, msg = validate_sql(sql)
assert not is_valid  # Should reject
assert "DELETE" in msg
```

#### Test: DROP Prevention

```python
sql = "DROP TABLE orders"
is_valid, msg = validate_sql(sql)
assert not is_valid
```

#### Test: LIMIT Enforcement

```python
sql = "SELECT * FROM orders"
is_valid, sql_modified = validate_sql(sql)
assert "LIMIT" in sql_modified.upper()
```

#### Test: Injection Prevention

```python
sql = "SELECT * FROM orders WHERE id = 1; DROP TABLE orders; --"
is_valid, msg = validate_sql(sql)
assert not is_valid
assert "dangerous" in msg.lower()
```

### Performance Tests

#### Query Execution Time

```bash
# Measure execution time
time curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show all invoices"}'

# Expected: < 3 seconds total
# - LLM generation: 1-2s
# - SQL validation: <5ms
# - Execution: <200ms
```

#### Concurrent Queries

```bash
# Load test with 10 concurrent queries
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/query \
    -H "Content-Type: application/json" \
    -d '{"query": "Show orders"}' &
done
wait

# Should handle without errors
```

---

## Frontend Testing

### Manual Testing Checklist

#### 1. Page Load

```
✓ Open http://localhost:5173
✓ No console errors
✓ Graph visualization displays
✓ Query interface loads
✓ All buttons are clickable
```

#### 2. Graph Visualization

```
✓ 7 nodes visible (customers, orders, deliveries, etc.)
✓ Nodes are color-coded
✓ Edges connect related nodes
✓ Can drag nodes
✓ Can zoom in/out
✓ MiniMap shows in corner
✓ Click node highlights it
```

#### 3. Query Submission

```
✓ Can type in textarea
✓ Submit button works
✓ Loading state shows while processing
✓ Results appear in right panel
✓ Execution time displays
```

#### 4. Results Display

**For regular queries**:
```
✓ Results table displays with data
✓ Can scroll table horizontally
✓ Column headers visible
✓ Rows match returned count
✓ Null values show as "null"
```

**For flow queries**:
```
✓ Flow visualization shows entities
✓ Cards display in order: orders → deliveries → invoices → payments
✓ Entity icons display
✓ Details are expandable
✓ Colors match entity type
```

#### 5. Error Handling

```
✓ Off-domain query shows error message
✓ API error shows helpful message
✓ Empty query shows validation
✓ Network error handled gracefully
```

#### 6. Quick Queries

```
✓ "Trace order #1" button works
✓ "Show all orders" button works
✓ "List customers" button works
✓ "Count payments" button works
```

---

## Integration Testing

### End-to-End Flow Test

```
1. Start backend: python main.py
2. Start frontend: npm run dev
3. Navigate to http://localhost:5173
4. Graph loads ✓
5. Enter query: "Trace order #1" ✓
6. Results display in flow visualization ✓
7. Can expand entity details ✓
8. Execution time shown ✓
```

### Data Integrity Test

```
1. Load sample data
2. Query: "Show orders"
3. Note order IDs (e.g., #1, #2, #3)
4. Query: "Trace order #1"
5. Verify delivery, invoice, payment IDs are consistent
6. Query directly: "Show invoice where order_id = 1"
7. Results should match
```

### Error Recovery Test

```
1. Stop backend server
2. Try to submit query in frontend
3. Should show error message
4. Restart backend
5. Query should work again
```

---

## Security Testing

### Domain Filter Testing

**Should ACCEPT**:
- "Show me orders"
- "How much did we invoice?"
- "Trace the delivery"
- "What are the payments?"
- "List all customers"

**Should REJECT**:
- "What's the weather today?"
- "Tell me a joke"
- "Recipe for pasta"
- "How do planes fly?"
- "What's the capital of France?"

### SQL Injection Testing

**Payloads that should be rejected**:

```
1. "Show orders; DROP TABLE orders; --"
2. "Show ' OR '1'='1"
3. "Select from customers where 1=1 /**/;"
4. "Union select * from pg_users"
5. "'; delete from orders; --"
```

**Test Method**:
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show orders; DROP TABLE orders;"}'

# Should return:
# {"success": false, "error": "...dangerous..."}
```

### Authorization Testing

**Unauthorized Tables**:
```bash
# Attempt to query non-whitelisted table
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show from pg_users"}'

# Should reject: "Unauthorized tables: pg_users"
```

---

## Performance Benchmarks

### Target Performance

| Operation | Target | Status |
|-----------|--------|--------|
| Frontend load | <1s | ✓ |
| Graph render | <500ms | ✓ |
| LLM generation | 1-2s | ✓ |
| SQL execution | <200ms | ✓ |
| Total query time | <2.5s | ✓ |

### Benchmark Script

```bash
#!/bin/bash
# bench.sh

echo "Running performance benchmarks..."

# Test 1: Health check
echo -n "Health check: "
time curl -s http://localhost:8000/health > /dev/null

# Test 2: Graph load
echo -n "Graph load: "
time curl -s http://localhost:8000/api/graph > /dev/null

# Test 3: Simple query
echo -n "Simple query: "
time curl -s -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show orders"}' > /dev/null

# Test 4: Flow query
echo -n "Flow query: "
time curl -s -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Trace order #1"}' > /dev/null
```

---

## Automated Testing

### Backend Tests

```python
# backend/tests/test_validator.py

def test_domain_filter_accepts_erp():
    assert is_domain_query("Show orders")[0] == True
    assert is_domain_query("Trace invoice")[0] == True

def test_domain_filter_rejects_off_topic():
    assert is_domain_query("What's the weather?")[0] == False
    assert is_domain_query("Tell me a joke")[0] == False

def test_sql_validation():
    sql = "SELECT * FROM orders"
    assert validate_sql(sql)[0] == True
    
    sql_bad = "DELETE FROM orders"
    assert validate_sql(sql_bad)[0] == False
```

### Running Tests

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_validator.py::test_domain_filter_accepts_erp -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

---

## Deployment Testing

### Pre-Deployment Checklist

- [ ] All tests pass locally
- [ ] No console errors in frontend
- [ ] No exception logs in backend
- [ ] Database has sample data
- [ ] API documentation is accurate
- [ ] README is complete
- [ ] Environment variables are documented
- [ ] Git history is clean

### Production Smoke Tests

After deploying to production:

```bash
# 1. Health check
curl https://api.yourdomain.com/health
# Should return: {"status": "ok"}

# 2. Graph endpoint
curl https://api.yourdomain.com/api/graph
# Should return graph structure

# 3. Query test
curl -X POST https://api.yourdomain.com/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show orders"}'
# Should return results

# 4. Frontend loads
curl https://yourdomain.com
# Should return HTML
```

---

## Troubleshooting Tests

### Backend Tests Failing

**Problem**: `ModuleNotFoundError: No module named 'sqlalchemy'`

```bash
# Solution: Activate virtual environment
source venv/bin/activate
pip install -r requirements.txt
pytest tests/
```

**Problem**: `ConnectionError: could not connect to server`

```bash
# Solution: Check PostgreSQL is running
psql -U postgres -d graph_query_db
# If fails, restart PostgreSQL
```

### Frontend Tests Failing

**Problem**: `Cannot find module 'react'`

```bash
# Solution: Install dependencies
npm install
npm run dev
```

**Problem**: `VITE_API_URL is not defined`

```bash
# Solution: Create .env file
cp .env.example .env
# Edit .env with backend URL
```

### Integration Tests Failing

**Problem**: API returns 500 error

```bash
# Solution: Check backend logs
tail -f backend.log

# Check database connectivity
python -c "from db import SessionLocal; db = SessionLocal(); print('Connected!')"
```

---

## Test Coverage Report

### Current Coverage

```
Name                  Stmts   Miss  Cover
──────────────────────────────────────
query_engine/         156     12    92%
  validator.py        45      2    96%
  intent.py           34      1    97%
  generator.py        42      5    88%
  executor.py         35      4    89%
models.py             68      8    88%
────────────────────────────────────────
TOTAL                156     12    92%
```

### Coverage Goals

- Core logic (validator, pipeline): >95%
- Integration points: >85%
- Utilities: >80%

---

## Known Issues & Limitations

### Frontend

- Graph visualization may lag with >1000 nodes
- React Flow doesn't support 3D rendering
- Touch support varies by browser

### Backend

- LLM generation time varies by API load (1-5s typical)
- SQLite doesn't support some advanced queries
- No built-in authentication (add before production)

### Data

- Sample data is synthetic, not representative of real ERP
- Limited to 10 orders in sample dataset
- No data persistence between restarts (unless PostgreSQL)

---

## Test Report Template

**Date**: ___________  
**Tester**: ___________  
**Environment**: ___________

### Overall Status
- [ ] All tests passed
- [ ] Some tests failed
- [ ] Critical issues found

### Test Results

| Test | Status | Notes |
|------|--------|-------|
| Backend health | ✓ | |
| Frontend load | ✓ | |
| Graph display | ✓ | |
| Query execution | ✓ | |
| Error handling | ✓ | |

### Issues Found

1. Issue: ___________
   - Severity: High/Medium/Low
   - Steps to reproduce: ___________
   - Expected vs actual: ___________

### Sign-off

- All critical issues resolved: ✓
- Ready for production: ✓

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml

name: Tests

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements.txt
      - run: cd backend && pytest tests/

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd frontend && npm install
      - run: cd frontend && npm run build
```

This will automatically run tests on every push and PR.
