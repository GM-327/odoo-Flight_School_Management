# API Reference

REST API documentation for the Flight School Management System.

---

## Authentication

### XML-RPC Authentication

```python
import xmlrpc.client

url = 'http://localhost:8069'
db = 'flight_school'
username = 'admin'
password = 'admin'

# Authenticate
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
```

### JSON-RPC Authentication

```python
import requests
import json

url = 'http://localhost:8069/jsonrpc'
payload = {
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "service": "common",
        "method": "authenticate",
        "args": [db, username, password, {}]
    },
    "id": 1
}
response = requests.post(url, json=payload)
uid = response.json()['result']
```

---

## Aircraft API

### List Aircraft

```python
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

aircraft = models.execute_kw(
    db, uid, password,
    'fs.aircraft', 'search_read',
    [[]],
    {'fields': ['registration', 'make', 'model', 'status']}
)
```

### Get Single Aircraft

```python
aircraft = models.execute_kw(
    db, uid, password,
    'fs.aircraft', 'read',
    [[aircraft_id]],
    {'fields': ['registration', 'make', 'model', 'total_flight_hours']}
)
```

### Create Aircraft

```python
aircraft_id = models.execute_kw(
    db, uid, password,
    'fs.aircraft', 'create',
    [{'registration': 'N12345', 'make': 'Cessna', 'model': '172S'}]
)
```

### Update Aircraft

```python
models.execute_kw(
    db, uid, password,
    'fs.aircraft', 'write',
    [[aircraft_id], {'status': 'maintenance'}]
)
```

### Delete Aircraft

```python
models.execute_kw(
    db, uid, password,
    'fs.aircraft', 'unlink',
    [[aircraft_id]]
)
```

---

## Student API

### List Students

```python
students = models.execute_kw(
    db, uid, password,
    'fs.student', 'search_read',
    [[['state', '=', 'active']]],
    {'fields': ['name', 'training_program', 'instructor_id']}
)
```

### Search with Domain

```python
# Find students with specific instructor
domain = [
    ('instructor_id', '=', instructor_id),
    ('state', '=', 'active')
]
students = models.execute_kw(
    db, uid, password,
    'fs.student', 'search_read',
    [domain],
    {'fields': ['name', 'training_program']}
)
```

---

## Common Operations

### Search (IDs only)

```python
ids = models.execute_kw(
    db, uid, password,
    'fs.aircraft', 'search',
    [[['status', '=', 'available']]]
)
```

### Count Records

```python
count = models.execute_kw(
    db, uid, password,
    'fs.aircraft', 'search_count',
    [[['status', '=', 'available']]]
)
```

### Pagination

```python
records = models.execute_kw(
    db, uid, password,
    'fs.aircraft', 'search_read',
    [[]],
    {
        'fields': ['registration', 'make'],
        'offset': 0,
        'limit': 10,
        'order': 'registration asc'
    }
)
```

---

## Domain Operators

| Operator | Example |
|----------|---------|
| `=` | `[('status', '=', 'active')]` |
| `!=` | `[('status', '!=', 'retired')]` |
| `>`, `<`, `>=`, `<=` | `[('hours', '>', 100)]` |
| `like` | `[('name', 'like', 'Cessna')]` |
| `ilike` | `[('name', 'ilike', 'cessna')]` |
| `in` | `[('id', 'in', [1, 2, 3])]` |
| `not in` | `[('id', 'not in', [1, 2])]` |
| `child_of` | `[('category_id', 'child_of', 1)]` |

### Combining Domains

```python
# AND (default)
domain = [('status', '=', 'active'), ('hours', '>', 100)]

# OR
domain = ['|', ('status', '=', 'active'), ('status', '=', 'maintenance')]

# NOT
domain = ['!', ('status', '=', 'retired')]
```

---

## Error Handling

```python
try:
    result = models.execute_kw(...)
except xmlrpc.client.Fault as e:
    print(f"Error: {e.faultString}")
```

---

**← Previous**: [Module Development](Module-Development) | **Next**: [Database Schema](Database-Schema) →
