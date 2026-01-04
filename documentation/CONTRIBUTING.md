# Contributing to Happy Place Boutique

Thank you for your interest in contributing to Happy Place Boutique! This guide will help you get started.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Testing Guidelines](#testing-guidelines)
6. [Commit Guidelines](#commit-guidelines)
7. [Pull Request Process](#pull-request-process)
8. [Documentation](#documentation)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors.

### Expected Behavior

- Be respectful and considerate
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Accept responsibility for mistakes

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Publishing private information
- Unprofessional conduct

---

## Getting Started

### Prerequisites

- **Python:** 3.11+
- **Node.js:** 16+
- **PostgreSQL:** 14+
- **Git:** Latest version

### Fork and Clone

1. **Fork the repository** on GitHub

2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/happy-place-webstore.git
   cd happy-place-webstore
   ```

3. **Add upstream remote:**
   ```bash
   git remote add upstream https://github.com/devleks/happy-place-webstore.git
   ```

### Setup Development Environment

1. **Backend setup:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your database credentials
   python seed.py
   ```

2. **Frontend setup:**
   ```bash
   cd frontend
   npm install
   ```

3. **Run development servers:**
   ```bash
   # Terminal 1 - Backend
   cd backend
   source venv/bin/activate
   python app.py
   
   # Terminal 2 - Frontend
   cd frontend
   npm start
   ```

---

## Development Workflow

### Branch Strategy

We use **Git Flow** branching model:

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

### Creating a Feature Branch

```bash
# Update develop branch
git checkout develop
git pull upstream develop

# Create feature branch
git checkout -b feature/your-feature-name

# Work on your feature
# ... make changes ...

# Push to your fork
git push origin feature/your-feature-name
```

### Keeping Your Branch Updated

```bash
# Fetch latest changes
git fetch upstream

# Rebase on develop
git rebase upstream/develop

# Force push (if already pushed)
git push origin feature/your-feature-name --force-with-lease
```

---

## Coding Standards

### Python (Backend)

**Style Guide:** PEP 8

**Formatting:**
```bash
# Use Black for formatting
pip install black
black backend/

# Use isort for imports
pip install isort
isort backend/
```

**Linting:**
```bash
# Use flake8
pip install flake8
flake8 backend/ --max-line-length=100
```

**Example:**
```python
"""
Module docstring explaining purpose.
"""

from typing import List, Optional
from flask import Blueprint, request, jsonify
from models import Customer


def get_customer_by_id(customer_id: int) -> Optional[Customer]:
    """
    Retrieve customer by ID.
    
    Args:
        customer_id: The customer's unique identifier
        
    Returns:
        Customer object if found, None otherwise
    """
    return Customer.query.get(customer_id)


@app.route('/api/customers/<int:customer_id>', methods=['GET'])
def customer_detail(customer_id: int):
    """Get customer details endpoint."""
    customer = get_customer_by_id(customer_id)
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    return jsonify(customer.to_dict()), 200
```

### JavaScript/React (Frontend)

**Style Guide:** Airbnb JavaScript Style Guide

**Formatting:**
```bash
# Use Prettier
npm install --save-dev prettier
npm run format
```

**Linting:**
```bash
# Use ESLint
npm run lint
```

**Example:**
```javascript
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

/**
 * Customer profile component
 */
const CustomerProfile = () => {
  const [customer, setCustomer] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchCustomer();
  }, []);

  const fetchCustomer = async () => {
    try {
      const response = await api.get('/customers/me');
      setCustomer(response.data);
    } catch (error) {
      console.error('Failed to fetch customer:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="customer-profile">
      <h1>{customer.first_name} {customer.last_name}</h1>
      <p>{customer.email}</p>
    </div>
  );
};

export default CustomerProfile;
```

### SQL

**Guidelines:**
- Use uppercase for SQL keywords
- Use snake_case for table and column names
- Always use parameterized queries (via SQLAlchemy)
- Add indexes for frequently queried columns

**Example:**
```sql
-- Good
SELECT 
    c.id,
    c.email_encrypted,
    COUNT(o.id) AS order_count
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
WHERE c.is_active = TRUE
GROUP BY c.id
ORDER BY order_count DESC
LIMIT 10;

-- Bad
select * from customers where email='test@example.com'
```

---

## Testing Guidelines

### Backend Tests

**Framework:** pytest

**Location:** `backend/tests/`

**Running Tests:**
```bash
cd backend
source venv/bin/activate
pytest

# With coverage
pytest --cov=. --cov-report=html
```

**Example Test:**
```python
import pytest
from app import app, db
from models import Customer


@pytest.fixture
def client():
    """Test client fixture."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://test_db'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


def test_customer_registration(client):
    """Test customer registration endpoint."""
    response = client.post('/api/auth/customer/register', json={
        'email': 'test@example.com',
        'password': 'SecurePass123',
        'first_name': 'Test',
        'last_name': 'User',
        'gdpr_consent': True
    })
    
    assert response.status_code == 201
    assert 'customer_id' in response.json


def test_customer_login(client):
    """Test customer login endpoint."""
    # Create customer first
    client.post('/api/auth/customer/register', json={
        'email': 'test@example.com',
        'password': 'SecurePass123',
        'first_name': 'Test',
        'last_name': 'User',
        'gdpr_consent': True
    })
    
    # Test login
    response = client.post('/api/auth/customer/login', json={
        'email': 'test@example.com',
        'password': 'SecurePass123'
    })
    
    assert response.status_code == 200
    assert 'access_token' in response.json
```

### Frontend Tests

**Framework:** Jest + React Testing Library

**Location:** `frontend/src/__tests__/`

**Running Tests:**
```bash
cd frontend
npm test

# With coverage
npm test -- --coverage
```

**Example Test:**
```javascript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import CustomerProfile from '../pages/CustomerProfile';
import api from '../services/api';

jest.mock('../services/api');

describe('CustomerProfile', () => {
  test('renders customer information', async () => {
    api.get.mockResolvedValue({
      data: {
        first_name: 'John',
        last_name: 'Doe',
        email: 'john@example.com'
      }
    });

    render(
      <BrowserRouter>
        <CustomerProfile />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('john@example.com')).toBeInTheDocument();
    });
  });
});
```

### Test Coverage Requirements

- **Minimum coverage:** 80%
- **Critical paths:** 100% (authentication, payments, orders)
- **New features:** Must include tests

---

## Commit Guidelines

### Commit Message Format

We follow **Conventional Commits** specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```bash
feat(auth): add Google OAuth login

Implement Google OAuth 2.0 authentication for customers.
Includes backend endpoint and frontend integration.

Closes #123

---

fix(cart): prevent negative quantities

Add validation to ensure cart item quantities cannot be negative.

Fixes #456

---

docs(api): update endpoint documentation

Add missing parameters and response examples for order endpoints.
```

### Commit Best Practices

1. **Atomic commits:** One logical change per commit
2. **Clear messages:** Explain what and why, not how
3. **Reference issues:** Include issue numbers
4. **Sign commits:** Use GPG signing (optional but recommended)

---

## Pull Request Process

### Before Submitting

1. **Update from develop:**
   ```bash
   git fetch upstream
   git rebase upstream/develop
   ```

2. **Run tests:**
   ```bash
   # Backend
   cd backend && pytest
   
   # Frontend
   cd frontend && npm test
   ```

3. **Check code style:**
   ```bash
   # Backend
   black backend/ && flake8 backend/
   
   # Frontend
   npm run lint
   ```

4. **Update documentation** if needed

### Creating Pull Request

1. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Open PR on GitHub** from your fork to `upstream/develop`

3. **Fill out PR template:**
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## Testing
   - [ ] Unit tests pass
   - [ ] Integration tests pass
   - [ ] Manual testing completed
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Comments added for complex code
   - [ ] Documentation updated
   - [ ] No new warnings generated
   
   ## Related Issues
   Closes #123
   ```

### Review Process

1. **Automated checks** must pass (CI/CD)
2. **Code review** by at least one maintainer
3. **Address feedback** and push updates
4. **Approval** from maintainer
5. **Merge** by maintainer (squash and merge)

### After Merge

1. **Delete feature branch:**
   ```bash
   git branch -d feature/your-feature-name
   git push origin --delete feature/your-feature-name
   ```

2. **Update local develop:**
   ```bash
   git checkout develop
   git pull upstream develop
   ```

---

## Documentation

### Code Documentation

**Python:**
```python
def calculate_order_total(order_id: int) -> float:
    """
    Calculate total amount for an order including tax and shipping.
    
    Args:
        order_id: The order's unique identifier
        
    Returns:
        Total amount in KES
        
    Raises:
        ValueError: If order not found
        
    Example:
        >>> calculate_order_total(123)
        5499.00
    """
    pass
```

**JavaScript:**
```javascript
/**
 * Fetch customer orders from API
 * @param {number} customerId - Customer ID
 * @param {Object} filters - Optional filters
 * @param {string} filters.status - Order status filter
 * @returns {Promise<Array>} Array of orders
 * @throws {Error} If API request fails
 */
async function fetchOrders(customerId, filters = {}) {
  // Implementation
}
```

### API Documentation

Update `API_REFERENCE.md` when adding/modifying endpoints.

### Database Changes

Document schema changes in `DATABASE_SCHEMA.md` and create migration files.

---

## Project Structure

```
happy_place_webstore/
├── backend/
│   ├── app.py                 # Flask application
│   ├── models/                # Database models
│   ├── routes/                # API endpoints
│   ├── services/              # Business logic
│   ├── middleware/            # Auth, rate limiting
│   ├── migrations/            # Database migrations
│   ├── tests/                 # Backend tests
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/        # Reusable components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API services
│   │   ├── context/           # React context
│   │   └── __tests__/         # Frontend tests
│   └── package.json           # Node dependencies
├── docs/                      # Documentation
├── .github/                   # GitHub workflows
└── README.md                  # Project overview
```

---

## Getting Help

### Resources

- **Documentation:** See `/docs` folder
- **API Reference:** `API_REFERENCE.md`
- **Troubleshooting:** `TROUBLESHOOTING.md`
- **Security:** `SECURITY_GUIDE.md`

### Communication

- **GitHub Issues:** Bug reports and feature requests
- **GitHub Discussions:** Questions and ideas
- **Email:** dev@happyplace.com

### Mentorship

New contributors are welcome! Reach out if you need help getting started.

---

## Recognition

Contributors are recognized in:
- `CONTRIBUTORS.md` file
- GitHub contributors page
- Release notes

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to Happy Place Boutique! 🎉
