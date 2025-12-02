# Sample OAuth MCP Server

A sample MCP (Model Context Protocol) server with OAuth2 authentication that works with any OAuth 2.0/OIDC-compliant identity provider. This server demonstrates how to build a production-ready MCP server that validates OAuth tokens before processing requests.

> **Note**: This server is provider-agnostic and works with any OAuth 2.0 provider (Okta, Auth0, Google, Azure AD, AWS Cognito, etc.). The examples in this README use Okta for demonstration purposes, but you can configure it to work with any compatible OAuth provider.

## Features

- OAuth2 token validation using JWT verification
- JWKS (JSON Web Key Set) support for token verification
- OAuth well-known endpoint forwarding for auto-discovery
- Example tool that extracts user information from JWT claims
- Support for both user authentication and machine-to-machine authentication

## Prerequisites

- Python 3.13+
- An OAuth 2.0/OIDC-compliant identity provider with:
  - An OAuth application/client configured
  - Client Credentials grant type enabled (for machine-to-machine authentication)
  - An Authorization Server (if applicable)
  - Access policies configured (if applicable)

## Installation

```bash
# Clone the repository
git clone https://github.com/truefoundry/mcp-servers.git
cd mcp-servers/sample-oauth-mcp

# Install dependencies
pip install -r requirements.txt
```

## Configuration

The server requires the following environment variables:

| Variable | Description | Example (Okta) |
|----------|-------------|----------------|
| `OAUTH_JWKS_URI` | JSON Web Key Set URI for token verification | `https://dev-12345678.okta.com/oauth2/aus123abc/v1/keys` |
| `OAUTH_ISSUER` | Authorization server issuer URI | `https://dev-12345678.okta.com/oauth2/aus123abc` |
| `OAUTH_AUDIENCE` | Audience identifier for your API | `https://your-mcp-server.example.com` |
| `HOST` | Server host (optional, defaults to `0.0.0.0`) | `0.0.0.0` |
| `PORT` | Server port (optional, defaults to `8000`) | `8000` |

### Setting Environment Variables

You can set these in your shell (using Okta as an example):

```bash
export OAUTH_JWKS_URI="https://dev-12345678.okta.com/oauth2/aus123abc/v1/keys"
export OAUTH_ISSUER="https://dev-12345678.okta.com/oauth2/aus123abc"
export OAUTH_AUDIENCE="https://your-mcp-server.example.com"
```

Or create a `.env` file:

```bash
OAUTH_JWKS_URI=https://dev-12345678.okta.com/oauth2/aus123abc/v1/keys
OAUTH_ISSUER=https://dev-12345678.okta.com/oauth2/aus123abc
OAUTH_AUDIENCE=https://your-mcp-server.example.com
```

> **Note**: Replace the Okta URLs with your OAuth provider's endpoints. Most OAuth providers expose these endpoints in their documentation or via their `.well-known/openid-configuration` endpoint.

## Running the Server

```bash
python calculator.py
```

The server will start on `http://localhost:8000/mcp` (or the port you specified).

## Getting an Access Token

To connect to the MCP server, you need a valid OAuth access token. The method for obtaining a token depends on your OAuth provider. Most providers support the Client Credentials grant type for machine-to-machine authentication.

> **Example (Okta)**: Check the test.py script to get the token

Consult your OAuth provider's documentation for the specific steps to obtain access tokens.


## Using the MCP Server

### Using MCP Inspector

MCP Inspector provides a visual interface to explore your MCP server's capabilities:

1. **Install MCP Inspector**:

```bash
npm install -g @modelcontextprotocol/inspector
```

2. **Start the Inspector**:

```bash
mcp-inspector http://localhost:8000/mcp
```

3. **Configure Authentication**:
   - When prompted, select HTTP transport
   - Enter the server URL: `http://localhost:8000/mcp`
   - In the headers section, add:
     - **Header Name**: `Authorization`
     - **Header Value**: `Bearer your-access-token-here`

4. **Test the Connection**:
   - The inspector will attempt to connect to your MCP server
   - If authentication succeeds, you'll see the available tools (e.g., `get_me`)
   - You can test tool calls directly from the inspector UI

## How It Works

The server implements OAuth token validation to secure MCP endpoints:

1. **Extract Bearer Token**: The server extracts the Bearer token from the `Authorization` header of incoming requests
2. **Fetch JWKS**: It fetches the JSON Web Key Set (JWKS) from your OAuth provider's JWKS endpoint to get the public keys needed for verification
3. **Decode and Verify**: The server decodes the JWT token and verifies its signature using the public keys from your OAuth provider
4. **Validate Claims**: It validates critical claims:
   - **Issuer**: Confirms the token was issued by your trusted OAuth authorization server (matches `OAUTH_ISSUER`)
   - **Audience**: Ensures the token was issued specifically for this MCP server (matches `OAUTH_AUDIENCE`)
   - **Expiration**: Checks that the token hasn't expired
5. **Allow/Deny**: Based on validation results, the request is either allowed to proceed or rejected with an authentication error

The server also exposes a `/.well-known/oauth-authorization-server` endpoint that automatically redirects to your OAuth provider's well-known endpoint (constructed from the `OAUTH_ISSUER`). This enables OAuth clients to auto-discover OAuth configuration details.

> **Note**: This server works with any OAuth 2.0/OIDC-compliant provider. The examples use Okta, but you can configure it to work with Google, Azure AD, AWS Cognito, or any other compatible provider.

## Troubleshooting

If you encounter authentication errors, verify that:

- Your access token hasn't expired
- The `OAUTH_AUDIENCE` environment variable matches the audience claim in your token
- The `OAUTH_ISSUER` matches the issuer claim in your token
- Your token includes the required scopes
- The `OAUTH_JWKS_URI` is correct and accessible
