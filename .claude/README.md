# Claude Code MCP Configuration

This directory contains configuration files for Model Context Protocol (MCP) servers that enhance Claude Code's capabilities for the Happy Place Webstore project.

## Quick Start

### 1. Set Up Environment Variables
```bash
# Copy the template
cp .env.mcp.template .env

# Edit .env and add your credentials
# Required for Phase 1:
# - GITHUB_TOKEN (from https://github.com/settings/tokens)
# - DATABASE_URL (your PostgreSQL connection string)
```

### 2. Verify MCP Configuration
The MCP servers are pre-configured in two locations:
- **Global**: `~/.config/claude/mcp-servers.json` (all projects)
- **Project**: `./.claude/mcp-servers.json` (this project only)

### 3. Restart Claude Code
Close and reopen Claude Code to load the MCP servers.

### 4. Test the Setup
Ask Claude Code to:
```
"Show me the configured MCP servers"
"Query the database for all products"
"List recent commits from GitHub"
```

## Configured MCP Servers (Phase 1)

| Server | Status | Purpose |
|--------|--------|---------|
| **GitHub** | ✅ Active | Repository operations, PR creation, issue management |
| **PostgreSQL** | ✅ Active | Database queries and schema inspection |
| **SQLite** | ✅ Active | Local database development |
| **Web Fetch** | ✅ Active | Web content fetching, product research |
| **File System** | ✅ Active | File and directory operations |

## Documentation

- **[MCP_USAGE_GUIDE.md](./MCP_USAGE_GUIDE.md)**: Comprehensive guide on using each MCP server
- **[mcp-servers.json](./mcp-servers.json)**: MCP server configuration for this project
- **[../.env.mcp.template](../.env.mcp.template)**: Environment variables template

## Project-Specific Configuration

The `.claude/mcp-servers.json` file is configured specifically for Happy Place Webstore:
- GitHub repository: `devleks/happy-place-webstore`
- SQLite database: `./backend/database.db`
- File system access: Project root only
- PostgreSQL: Connection via `DATABASE_URL` environment variable

## Common Tasks

### Database Queries
```
"Show me all products in the maternity category"
"Query inventory for low stock items"
"Display the User table schema"
```

### GitHub Operations
```
"Create a pull request for the new feature"
"Show recent commits"
"List all open issues"
```

### Product Research
```
"Fetch product trends from [competitor site]"
"Download clothing images from Unsplash"
```

### File Management
```
"Organize product images by category"
"List all CSV files in the project"
```

## Future Enhancements

### Phase 2 (Planned)
- REST API Testing Server
- Image Processing Server
- File System Extended Operations

### Phase 3 (Planned)
- Secrets Management Server
- Stripe Payment Server
- Analytics & Reporting Server

## Troubleshooting

### MCP Server Not Working
1. Check `.env` file has correct credentials
2. Verify MCP server configuration exists
3. Restart Claude Code
4. Check Claude Code logs for errors

### GitHub Authentication Issues
```bash
# Verify token
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user

# Regenerate token if needed
# https://github.com/settings/tokens
```

### Database Connection Issues
```bash
# Test PostgreSQL connection
psql $DATABASE_URL -c "\dt"

# Check if database exists
psql -l | grep happy_place
```

## Security Notes

- Never commit `.env` files to git (protected by `.gitignore`)
- Use environment variables for all credentials
- GitHub token requires: `repo`, `read:org`, `read:user` scopes
- File system access is sandboxed to project directory only

## Support

- **MCP Documentation**: https://modelcontextprotocol.io
- **Project Repository**: https://github.com/devleks/happy-place-webstore
- **Claude Code Help**: Type `/help` in Claude Code

---

**Last Updated**: 2025-11-21
**Configuration Version**: 1.0 (Phase 1)
