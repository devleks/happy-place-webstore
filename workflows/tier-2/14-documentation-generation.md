# 14 - Documentation Generation Workflow

Systematic approach to creating, maintaining, and automating project documentation across code, APIs, architecture, and user guides.

---

## Overview

This workflow establishes documentation standards, automates generation where possible, and ensures documentation stays synchronized with code changes.

## When to Use

- New project setup
- API documentation needs
- Architecture documentation
- Onboarding documentation
- README/contributing guides
- User/admin documentation
- Documentation debt cleanup

---

## Quick Start

```bash
./blackbox.sh start "docs-[type]-[scope]"
```

---

## Cascade Prompt

```
Execute Documentation Generation workflow for: [DESCRIPTION]

Documentation type: [api/architecture/user/developer/all]
Current state: [none/outdated/partial]
Output format: [markdown/html/pdf]

Steps:
1. Audit existing documentation
2. Identify gaps and priorities
3. Generate/update documentation
4. Set up automation
5. Review and publish
6. Configure maintenance

Reference: workflows/tier-2/14-documentation-generation.md
Session: [CURRENT-SESSION-ID]
```

---

## Documentation Types

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOCUMENTATION HIERARCHY                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PROJECT ROOT                                                   │
│  ├── README.md              ← Project overview                  │
│  ├── CONTRIBUTING.md        ← How to contribute                 │
│  ├── CHANGELOG.md           ← Version history                   │
│  ├── LICENSE                ← Legal                             │
│  └── CODE_OF_CONDUCT.md     ← Community guidelines              │
│                                                                 │
│  /docs                                                          │
│  ├── /architecture          ← System design                     │
│  │   ├── overview.md                                            │
│  │   ├── decisions/         ← ADRs                              │
│  │   └── diagrams/          ← Visual docs                       │
│  ├── /api                   ← API documentation                 │
│  │   ├── openapi.yaml                                           │
│  │   └── endpoints/                                             │
│  ├── /guides                ← How-to guides                     │
│  │   ├── getting-started.md                                     │
│  │   ├── deployment.md                                          │
│  │   └── troubleshooting.md                                     │
│  ├── /reference             ← Technical reference               │
│  │   ├── configuration.md                                       │
│  │   └── environment.md                                         │
│  └── /user                  ← End-user docs                     │
│      ├── quick-start.md                                         │
│      └── features/                                              │
│                                                                 │
│  CODE DOCUMENTATION                                             │
│  ├── JSDoc/TSDoc comments   ← Inline code docs                  │
│  ├── Type definitions       ← TypeScript interfaces             │
│  └── Generated docs         ← TypeDoc, Sphinx, etc.             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Documentation Audit

### Audit Checklist

```markdown
## Documentation Audit

### Project Root Files
- [ ] README.md exists and is current
- [ ] CONTRIBUTING.md exists
- [ ] CHANGELOG.md is maintained
- [ ] LICENSE file present
- [ ] .github templates (PR, issues)

### Code Documentation
- [ ] Functions have JSDoc/docstrings
- [ ] Complex logic is commented
- [ ] Types are documented
- [ ] Examples in comments where helpful

### API Documentation
- [ ] OpenAPI/Swagger spec exists
- [ ] All endpoints documented
- [ ] Request/response examples
- [ ] Error codes documented
- [ ] Authentication documented

### Architecture Documentation
- [ ] System overview exists
- [ ] Component diagrams current
- [ ] Data flow documented
- [ ] ADRs for major decisions
- [ ] Deployment architecture

### User Documentation
- [ ] Getting started guide
- [ ] Feature documentation
- [ ] FAQ/Troubleshooting
- [ ] Admin/config guides
```

### Audit Script

```bash
#!/bin/bash
# doc-audit.sh

echo "📚 Documentation Audit"
echo "======================"

# Check root files
echo ""
echo "📄 Root Files:"
for file in README.md CONTRIBUTING.md CHANGELOG.md LICENSE; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (missing)"
    fi
done

# Check docs directory
echo ""
echo "📁 Docs Directory:"
if [ -d "docs" ]; then
    find docs -name "*.md" | head -20 | while read f; do
        echo "   📄 $f"
    done
else
    echo "   ❌ /docs directory not found"
fi

# Check for OpenAPI
echo ""
echo "🔌 API Documentation:"
for file in openapi.yaml openapi.json swagger.yaml swagger.json; do
    if [ -f "$file" ] || [ -f "docs/api/$file" ]; then
        echo "   ✅ $file found"
    fi
done

# Check code comments
echo ""
echo "💻 Code Documentation Coverage:"
echo "   JSDoc comments: $(grep -r '@param\|@returns' src/ 2>/dev/null | wc -l)"
echo "   TODO comments: $(grep -r 'TODO\|FIXME' src/ 2>/dev/null | wc -l)"

# Check for generated docs
echo ""
echo "📖 Generated Docs:"
for dir in docs/api-reference docs/typedoc site _site; do
    if [ -d "$dir" ]; then
        echo "   ✅ $dir exists"
    fi
done
```

---

## Phase 2: README Template

### Comprehensive README

```markdown
# Project Name

[![Build Status](badge-url)](link)
[![Coverage](badge-url)](link)
[![License](badge-url)](link)

Brief description of what this project does and who it's for.

## Features

- ✅ Feature 1
- ✅ Feature 2
- ✅ Feature 3

## Quick Start

### Prerequisites

- Node.js >= 18
- PostgreSQL >= 14
- Redis >= 7

### Installation

\`\`\`bash
# Clone the repository
git clone https://github.com/org/project.git
cd project

# Install dependencies
npm install

# Set up environment
cp .env.example .env

# Run database migrations
npm run db:migrate

# Start development server
npm run dev
\`\`\`

### Running Tests

\`\`\`bash
npm test              # Run all tests
npm run test:unit     # Unit tests only
npm run test:e2e      # End-to-end tests
\`\`\`

## Documentation

- [Getting Started Guide](docs/guides/getting-started.md)
- [API Reference](docs/api/README.md)
- [Architecture](docs/architecture/overview.md)
- [Contributing](CONTRIBUTING.md)

## Project Structure

\`\`\`
├── src/
│   ├── api/          # API routes
│   ├── services/     # Business logic
│   ├── models/       # Data models
│   └── utils/        # Utilities
├── tests/
├── docs/
└── scripts/
\`\`\`

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `3000` |
| `DATABASE_URL` | Database connection | - |
| `REDIS_URL` | Redis connection | - |

See [Configuration Guide](docs/reference/configuration.md) for details.

## API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/users` | GET | List users |
| `/api/users/:id` | GET | Get user |
| `/api/users` | POST | Create user |

See [API Documentation](docs/api/README.md) for complete reference.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)

## Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](issues-url)
- 💬 [Discussions](discussions-url)
```

---

## Phase 3: API Documentation

### OpenAPI Specification Template

```yaml
# openapi.yaml
openapi: 3.1.0
info:
  title: Project API
  description: |
    API documentation for Project.
    
    ## Authentication
    All endpoints require Bearer token authentication.
    
    ## Rate Limiting
    - 100 requests per minute for authenticated users
    - 10 requests per minute for unauthenticated
  version: 1.0.0
  contact:
    email: api@example.com
  license:
    name: MIT

servers:
  - url: https://api.example.com/v1
    description: Production
  - url: https://staging-api.example.com/v1
    description: Staging
  - url: http://localhost:3000/v1
    description: Development

tags:
  - name: Users
    description: User management
  - name: Auth
    description: Authentication

paths:
  /users:
    get:
      tags: [Users]
      summary: List users
      description: Retrieve a paginated list of users
      operationId: listUsers
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
            maximum: 100
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserList'
              example:
                data:
                  - id: "123"
                    email: "user@example.com"
                    name: "John Doe"
                meta:
                  page: 1
                  total: 100
        '401':
          $ref: '#/components/responses/Unauthorized'
      security:
        - bearerAuth: []

    post:
      tags: [Users]
      summary: Create user
      operationId: createUser
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUser'
      responses:
        '201':
          description: User created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '400':
          $ref: '#/components/responses/BadRequest'
        '422':
          $ref: '#/components/responses/ValidationError'
      security:
        - bearerAuth: []

components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
          format: uuid
        email:
          type: string
          format: email
        name:
          type: string
        createdAt:
          type: string
          format: date-time
      required: [id, email, name]

    CreateUser:
      type: object
      properties:
        email:
          type: string
          format: email
        name:
          type: string
          minLength: 1
          maxLength: 100
        password:
          type: string
          minLength: 8
      required: [email, name, password]

    UserList:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/User'
        meta:
          $ref: '#/components/schemas/PaginationMeta'

    PaginationMeta:
      type: object
      properties:
        page:
          type: integer
        limit:
          type: integer
        total:
          type: integer

    Error:
      type: object
      properties:
        code:
          type: string
        message:
          type: string
        details:
          type: object

  responses:
    Unauthorized:
      description: Authentication required
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            code: UNAUTHORIZED
            message: Authentication required

    BadRequest:
      description: Invalid request
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    ValidationError:
      description: Validation failed
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

### Auto-Generate from Code

```typescript
// Using TSDoc for TypeScript
/**
 * Retrieves a user by their unique identifier.
 * 
 * @param id - The unique user identifier
 * @returns The user object if found
 * @throws {NotFoundError} When user doesn't exist
 * 
 * @example
 * ```typescript
 * const user = await getUser('123');
 * console.log(user.name);
 * ```
 */
export async function getUser(id: string): Promise<User> {
  // implementation
}

// Generate docs with TypeDoc
// npx typedoc --out docs/api-reference src/
```

```python
# Using docstrings for Python
def get_user(user_id: str) -> User:
    """
    Retrieve a user by their unique identifier.
    
    Args:
        user_id: The unique user identifier
        
    Returns:
        User: The user object if found
        
    Raises:
        NotFoundError: When user doesn't exist
        
    Example:
        >>> user = get_user('123')
        >>> print(user.name)
        'John Doe'
    """
    pass

# Generate docs with Sphinx
# sphinx-apidoc -o docs/api src/
```

---

## Phase 4: Architecture Documentation

### Architecture Decision Record (ADR)

```markdown
# ADR-001: Use PostgreSQL as Primary Database

## Status
Accepted

## Context
We need to choose a primary database for storing user data, transactions,
and application state. Key requirements:
- ACID compliance for financial transactions
- Strong consistency
- Rich querying capabilities
- Scalability to 10M+ records

## Decision
We will use PostgreSQL 15+ as our primary database.

## Alternatives Considered

### MySQL
- Pros: Familiar, good tooling
- Cons: Less feature-rich, weaker JSON support

### MongoDB
- Pros: Flexible schema, easy horizontal scaling
- Cons: No ACID transactions across documents, eventual consistency

### CockroachDB
- Pros: Distributed, PostgreSQL compatible
- Cons: Higher complexity, cost

## Consequences

### Positive
- Strong ACID guarantees
- Excellent JSON support for flexible data
- Rich ecosystem of tools
- Strong community support

### Negative
- Requires more planning for horizontal scaling
- Need to manage connection pooling carefully

### Neutral
- Team has existing PostgreSQL experience

## References
- [PostgreSQL Documentation](https://postgresql.org/docs/)
- [Architecture Meeting Notes](link)

---
*Recorded: 2024-12-17*
*Session: CONV-2024-12-17-001*
```

### System Diagram (Mermaid)

```markdown
# System Architecture

## High-Level Overview

\`\`\`mermaid
graph TB
    subgraph Client
        Web[Web App]
        Mobile[Mobile App]
    end
    
    subgraph Edge
        CDN[CloudFlare CDN]
        LB[Load Balancer]
    end
    
    subgraph Application
        API[API Servers]
        Worker[Background Workers]
    end
    
    subgraph Data
        PG[(PostgreSQL)]
        Redis[(Redis Cache)]
        S3[(S3 Storage)]
    end
    
    subgraph External
        Auth[Auth0]
        Email[SendGrid]
        Pay[Stripe]
    end
    
    Web --> CDN
    Mobile --> CDN
    CDN --> LB
    LB --> API
    API --> PG
    API --> Redis
    API --> S3
    API --> Auth
    API --> Email
    API --> Pay
    Worker --> PG
    Worker --> Redis
\`\`\`

## Data Flow

\`\`\`mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant D as Database
    participant Ca as Cache
    
    C->>A: GET /users/123
    A->>Ca: Check cache
    alt Cache hit
        Ca-->>A: Return cached user
    else Cache miss
        A->>D: Query user
        D-->>A: Return user
        A->>Ca: Store in cache
    end
    A-->>C: Return user JSON
\`\`\`
```

---

## Phase 5: Automation

### Documentation CI/CD

```yaml
# .github/workflows/docs.yml
name: Documentation

on:
  push:
    branches: [main]
    paths:
      - 'docs/**'
      - 'src/**'
      - 'openapi.yaml'
  pull_request:
    paths:
      - 'docs/**'

jobs:
  build-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          
      - name: Install dependencies
        run: npm ci
        
      - name: Generate API docs
        run: npm run docs:api
        
      - name: Generate TypeDoc
        run: npm run docs:typedoc
        
      - name: Validate OpenAPI
        run: npx @redocly/cli lint openapi.yaml
        
      - name: Build documentation site
        run: npm run docs:build
        
      - name: Deploy to GitHub Pages
        if: github.ref == 'refs/heads/main'
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs/_site

  check-links:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check links
        uses: lycheeverse/lychee-action@v1
        with:
          args: --verbose --no-progress './docs/**/*.md'
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: check-docs
        name: Check documentation
        entry: ./scripts/check-docs.sh
        language: script
        files: \.(ts|js|py)$
        
      - id: update-toc
        name: Update table of contents
        entry: npx doctoc docs/
        language: system
        files: docs/.*\.md$
```

---

## Phase 6: Maintenance

### Documentation Review Checklist

```markdown
## Quarterly Documentation Review

### Accuracy
- [ ] README reflects current setup
- [ ] API docs match implementation
- [ ] Environment variables are current
- [ ] Diagrams reflect current architecture

### Completeness
- [ ] All new features documented
- [ ] Breaking changes noted
- [ ] Migration guides exist
- [ ] Troubleshooting updated

### Quality
- [ ] No broken links
- [ ] Examples work
- [ ] Screenshots current
- [ ] Grammar/spelling checked

### Freshness
- [ ] Last update dates visible
- [ ] Deprecated docs marked
- [ ] Version numbers current
```

---

## Black Box Integration

```bash
# Start documentation session
./blackbox.sh start "docs-api-update"

# Log actions
./blackbox.sh action "Audited existing documentation" "Found 15 gaps"
./blackbox.sh decision "Use OpenAPI 3.1" "Better JSON Schema support"
./blackbox.sh action "Generated API reference" "45 endpoints documented"
./blackbox.sh milestone "API documentation complete"

# End session
./blackbox.sh end "Documentation coverage: 95%"
```

---

## Quick Reference

| Task | Command/Tool |
|------|--------------|
| Generate TypeDoc | `npx typedoc src/` |
| Generate Sphinx | `sphinx-build docs/ _build/` |
| Validate OpenAPI | `npx @redocly/cli lint openapi.yaml` |
| Check links | `npx lychee docs/**/*.md` |
| Preview docs | `npx serve docs/_site` |
| Update TOC | `npx doctoc README.md` |

---

*Documentation Generation Workflow v1.0*
*Integrates with Black Box for tracking*
