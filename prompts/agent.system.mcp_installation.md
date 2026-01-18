
## MCP Server Installation Guide

When user asks to install or configure an MCP server, follow these instructions carefully.

### Configuration Format

MCP servers are configured in settings.json under `mcp_servers` field as JSON string:

```json
{
  "mcpServers": {
    "server_name": {
      "name": "server_name",
      "description": "Server description",
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "package-name", "--flag"],
      "disabled": false
    }
  }
}
```

### Common MCP Servers

#### Repomix (repository packaging)
```json
{
  "command": "npx",
  "args": ["-y", "repomix", "--mcp"]
}
```
IMPORTANT: Use `repomix --mcp` NOT `@repomix-mcp/mcp`

#### Filesystem
```json
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
}
```

#### Memory
```json
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-memory"]
}
```

#### GitHub
```json
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "token"
  }
}
```

### Installation Steps

1. Read current settings: `cat /a0/tmp/settings.json`
2. Parse existing mcp_servers JSON string
3. Add new server to mcpServers object
4. Write back as JSON string to mcp_servers field
5. Inform user to restart Agent Zero or reload settings

### Common Mistakes to Avoid

- DO NOT install CLI tools globally expecting them to work as MCP
- DO NOT use wrong package names (e.g. `@repomix-mcp/mcp` instead of `repomix --mcp`)
- DO NOT forget `-y` flag for npx (auto-confirm install)
- DO NOT forget `--mcp` flag for servers that require it
- ALWAYS verify the correct package name and args from official documentation

### Verification

After configuration, verify with:
```bash
cat /a0/tmp/settings.json | jq -r '.mcp_servers' | jq .
```
