# MCP Servers Usage Guide for Happy Place Webstore

## Overview
This guide explains how to use the configured MCP (Model Context Protocol) servers to enhance development productivity for your e-commerce webstore.

## Configured MCP Servers

### Phase 1: Core Setup (Active)

#### 1. GitHub MCP Server
**Purpose**: Enhanced GitHub repository operations and automation

**Key Capabilities**:
- Create and manage pull requests
- Search repository code and files
- Manage issues and project boards
- Retrieve commit history and file contents
- Manage GitHub Actions workflows

**Example Use Cases**:
```
"Create a pull request for the new product catalog feature"
"Show me recent commits related to authentication"
"List all open issues tagged with 'bug'"
"Search the repository for 'inventory sync' code"
```

**Setup**:
1. Generate GitHub Personal Access Token at: https://github.com/settings/tokens
2. Grant scopes: `repo`, `read:org`, `read:user`
3. Add token to `.env` file: `GITHUB_TOKEN=ghp_your_token`
4. Restart Claude Code to load the configuration

---

#### 2. PostgreSQL MCP Server
**Purpose**: Direct database querying and management

**Key Capabilities**:
- Execute SQL queries against PostgreSQL database
- Inspect database schema and table structures
- View indexes, constraints, and relationships
- Debug data integrity issues
- Test queries before implementing in code

**Example Use Cases**:
```
"Show me all products in the maternity category"
"Query the inventory table for products with stock < 5"
"Display the schema for the User table"
"Find all users who registered this month"
"Check if there are duplicate product SKUs"
```

**Setup**:
1. Ensure PostgreSQL is running
2. Add connection string to `.env`: `DATABASE_URL=postgresql://user:password@localhost:5432/happy_place_db`
3. Test connection: `psql $DATABASE_URL -c "\dt"`

---

#### 3. SQLite MCP Server
**Purpose**: Local database development and testing

**Key Capabilities**:
- Query SQLite database files
- Inspect schema during development
- Export/import data for testing
- Rapid prototyping without PostgreSQL

**Example Use Cases**:
```
"Query the SQLite database for all categories"
"Show me the products table schema from the local database"
"Export all maternity products to JSON"
"Count total products in the development database"
```

**Setup**:
1. Ensure `backend/database.db` exists (created by seed.py)
2. Path is pre-configured in `.claude/mcp-servers.json`
3. No credentials needed for local SQLite files

---

#### 4. Web Fetch MCP Server
**Purpose**: Web content fetching and research

**Key Capabilities**:
- Fetch and parse web pages
- Extract product information from competitor sites
- Research fashion trends and pricing
- Access external APIs
- Download and analyze web content

**Example Use Cases**:
```
"Fetch product descriptions from [competitor URL]"
"Research current maternity fashion trends on major boutique sites"
"Get pricing data for women's clothing from [site]"
"Fetch new clothing images from Unsplash API"
"Analyze the homepage of purplessmaternity.com for design ideas"
```

**Setup**:
- No configuration needed
- Works out of the box
- Respects robots.txt and rate limiting

---

#### 5. File System MCP Server
**Purpose**: Advanced file and directory operations

**Key Capabilities**:
- Create, read, update, delete files
- Directory traversal and search
- File organization and management
- Batch file operations
- Asset management

**Example Use Cases**:
```
"Organize all product images into category folders"
"Find all CSV files in the project"
"Create a directory structure for product imports"
"List all image files larger than 1MB"
"Copy product images to the public directory"
```

**Setup**:
- Pre-configured with project path
- Limited to: `/Users/xreatives/Documents/Code/cli_projects/happy_place_webstore`
- Safe sandboxing prevents access outside allowed paths

---

## How to Use MCP Servers with Claude Code

### Method 1: Natural Language Requests
Simply ask Claude Code to perform tasks, and it will automatically use the appropriate MCP server:

```
"Use the database to show me all out-of-stock products"
"Create a GitHub issue for the payment integration bug"
"Fetch the latest product trends from [fashion site]"
```

### Method 2: Explicit MCP Commands (if available)
Some Claude Code versions support direct MCP commands:

```
/mcp list                    # List all configured servers
/mcp status github          # Check GitHub server status
/mcp enable postgresql      # Enable PostgreSQL server
/mcp disable web           # Disable web fetch server
```

### Method 3: Context-Aware Requests
Claude Code automatically selects the best MCP server based on context:

```
"Debug this SQL query" → Uses PostgreSQL/SQLite MCP
"Push this change to GitHub" → Uses GitHub MCP
"Research competitor pricing" → Uses Web Fetch MCP
"Optimize product images" → Uses File System MCP
```

---

## Common Workflows

### Product Management Workflow
```
1. "Query the database for products with low stock"
2. "Create a CSV file with these products"
3. "Create a GitHub issue to restock these items"
```

### Development Workflow
```
1. "Check the database schema for the Inventory table"
2. "Test this SQL query for inventory sync"
3. "Create a pull request with the inventory update code"
```

### Research & Design Workflow
```
1. "Fetch product descriptions from [competitor site]"
2. "Download clothing images from Unsplash for category [X]"
3. "Organize images into the appropriate directories"
```

### Deployment Workflow
```
1. "Query production database to verify migration"
2. "Create a GitHub release for version 1.0.0"
3. "Generate deployment checklist"
```

---

## Environment Setup

### Step 1: Copy Environment Template
```bash
cd /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore
cp .env.mcp.template .env
```

### Step 2: Fill in Credentials
Edit `.env` and replace placeholders:
- `GITHUB_TOKEN`: Your GitHub Personal Access Token
- `DATABASE_URL`: Your PostgreSQL connection string
- Other credentials as needed

### Step 3: Verify Configuration
```bash
# Check that MCP config exists
cat ~/.config/claude/mcp-servers.json

# Or check project-specific config
cat .claude/mcp-servers.json
```

### Step 4: Restart Claude Code
Close and reopen Claude Code to load the MCP servers

---

## Troubleshooting

### MCP Server Not Responding
```
1. Check that credentials are correct in .env
2. Verify the server is enabled: /mcp status [server-name]
3. Check logs: Look for MCP errors in Claude Code output
4. Restart Claude Code
```

### GitHub MCP Issues
```
- Verify token has correct scopes (repo, read:org, read:user)
- Check token hasn't expired
- Test token: curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

### Database MCP Issues
```
- Verify database is running: pg_isready (PostgreSQL)
- Test connection: psql $DATABASE_URL
- Check connection string format
- Verify database exists: psql -l
```

### Web Fetch MCP Issues
```
- Check internet connection
- Verify URL is accessible in browser
- Some sites may block automated access
- Respect rate limits and robots.txt
```

---

## Future Enhancements (Phase 2 & 3)

### Coming Soon
- **REST API Testing Server**: Test Flask endpoints
- **Image Processing Server**: Optimize product photos
- **Secrets Management Server**: Secure credential storage
- **Stripe MCP Server**: Payment integration testing

### Installation for Future Servers
These will be added to `mcp-servers.json` when needed:
```json
"stripe": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-stripe"],
  "env": {
    "STRIPE_API_KEY": "${STRIPE_API_KEY}"
  }
}
```

---

## Best Practices

### Security
- Never commit `.env` to git (it's in `.gitignore`)
- Use environment variables for all credentials
- Rotate API tokens regularly
- Use test/sandbox credentials for development

### Performance
- Disable unused MCP servers to reduce overhead
- Use SQLite for local development
- Cache frequently queried database results
- Batch file operations when possible

### Development
- Test database queries with MCP before implementing in code
- Use GitHub MCP for automated PR creation
- Research competitors regularly with Web Fetch MCP
- Organize files systematically with File System MCP

---

## Support & Documentation

- **MCP Official Docs**: https://modelcontextprotocol.io
- **GitHub API**: https://docs.github.com/en/rest
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **Claude Code Help**: Type `/help` in Claude Code

---

## Quick Reference

| Task | MCP Server | Example Command |
|------|-----------|-----------------|
| Query products | PostgreSQL/SQLite | "Show all maternity products" |
| Create PR | GitHub | "Create PR for inventory feature" |
| Research trends | Web Fetch | "Fetch trends from [site]" |
| Manage files | File System | "Organize product images" |
| Check schema | PostgreSQL/SQLite | "Show User table schema" |
| Search code | GitHub | "Find authentication code" |
| Download images | Web Fetch | "Get images from Unsplash" |

---

**Last Updated**: 2025-11-21
**Project**: Happy Place Webstore
**Repository**: https://github.com/devleks/happy-place-webstore
