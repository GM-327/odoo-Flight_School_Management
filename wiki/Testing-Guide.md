# Testing Guide

Writing and running tests for the Flight School Management System.

---

## Running Tests

### Run All Module Tests

```bash
./odoo-bin -c odoo.conf -d test_db --test-enable -i fs_core --stop-after-init
```

### Run Specific Test Class

```bash
./odoo-bin -c odoo.conf -d test_db --test-enable \
    --test-tags /fs_core:TestAircraft --stop-after-init
```

### Run Tests with Output

```bash
./odoo-bin -c odoo.conf -d test_db --test-enable -i fs_core \
    --stop-after-init --log-level=test
```

---

## Writing Tests

### Test File Structure

```
fs_your_module/
└── tests/
    ├── __init__.py
    ├── test_your_model.py
    └── test_your_logic.py
```

### Basic Test Class

```python
# tests/test_aircraft.py
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestAircraft(TransactionCase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Aircraft = cls.env['fs.aircraft']
        cls.test_aircraft = cls.Aircraft.create({
            'registration': 'N12345',
            'make': 'Cessna',
            'model': '172S',
        })
    
    def test_aircraft_creation(self):
        """Test aircraft is created correctly."""
        self.assertEqual(self.test_aircraft.registration, 'N12345')
        self.assertEqual(self.test_aircraft.status, 'available')
    
    def test_registration_unique(self):
        """Test duplicate registration raises error."""
        with self.assertRaises(Exception):
            self.Aircraft.create({
                'registration': 'N12345',  # Duplicate
                'make': 'Piper',
                'model': 'Cherokee',
            })
    
    def test_status_change(self):
        """Test status can be changed."""
        self.test_aircraft.status = 'maintenance'
        self.assertEqual(self.test_aircraft.status, 'maintenance')
```

---

## Test Types

### TransactionCase

- Each test runs in its own transaction
- Rolled back after each test
- Fast, isolated

```python
from odoo.tests.common import TransactionCase

class TestMyModel(TransactionCase):
    def test_something(self):
        # Test code here
        pass
```

### SavepointCase

- Tests share setup
- Uses savepoints for rollback
- Faster for many tests with same data

```python
from odoo.tests.common import SavepointCase

class TestMyModel(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Shared setup
```

### HttpCase

- For testing web controllers
- Runs actual HTTP requests

```python
from odoo.tests.common import HttpCase

class TestController(HttpCase):
    def test_page_loads(self):
        response = self.url_open('/web/login')
        self.assertEqual(response.status_code, 200)
```

---

## Common Assertions

| Method | Description |
|--------|-------------|
| `assertEqual(a, b)` | Check a equals b |
| `assertNotEqual(a, b)` | Check a not equals b |
| `assertTrue(x)` | Check x is True |
| `assertFalse(x)` | Check x is False |
| `assertIn(a, b)` | Check a in b |
| `assertRaises(Error)` | Check error is raised |

---

## Test Tags

```python
from odoo.tests import tagged

@tagged('post_install', '-at_install', 'fs_core')
class TestAircraft(TransactionCase):
    pass
```

Common tags:
- `at_install` - Run during install
- `post_install` - Run after install
- `-at_install` - Don't run during install
- Custom tags for filtering

---

## Mocking

```python
from unittest.mock import patch

class TestWithMock(TransactionCase):
    
    def test_with_mock(self):
        with patch.object(self.Aircraft, '_send_notification') as mock:
            self.test_aircraft.action_ground()
            mock.assert_called_once()
```

---

## Best Practices

1. **One assertion per test** (when practical)
2. **Descriptive test names** - `test_aircraft_status_change_logs_message`
3. **Test edge cases** - Empty values, max values, invalid data
4. **Keep tests fast** - Avoid unnecessary setup
5. **Test business logic** - Focus on model methods, not ORM

---

**← Previous**: [Database Schema](Database-Schema) | **Next**: [Code Style Guide](Code-Style-Guide) →
