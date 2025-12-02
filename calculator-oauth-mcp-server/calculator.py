from fastmcp import FastMCP, Context
import os
from fastmcp.server.auth.providers.jwt import JWTVerifier
from dotenv import load_dotenv
from starlette.responses import RedirectResponse
from starlette.requests import Request
from datetime import datetime

load_dotenv()

print(os.getenv("OAUTH_JWKS_URI"))
print(os.getenv("OAUTH_ISSUER"))
print(os.getenv("OAUTH_AUDIENCE"))
# Configure JWT verification using JWKS
token_verifier = JWTVerifier(
    jwks_uri=os.getenv("OAUTH_JWKS_URI"),
    issuer=os.getenv("OAUTH_ISSUER"),
    audience=os.getenv("OAUTH_AUDIENCE"),
)

# Bearer token authentication
mcp = FastMCP("Demo 🚀", auth=token_verifier)

# Forward .well-known/oauth-authorization-server to the actual OAuth server
@mcp.custom_route("/.well-known/oauth-authorization-server", methods=["GET", "HEAD", "OPTIONS"], include_in_schema=False)
async def oauth_well_known(request: Request):
    """Redirect to the upstream OAuth server's well-known endpoint."""
    return RedirectResponse(os.environ.get(f"OAUTH_ISSUER") + "/.well-known/oauth-authorization-server", status_code=307)

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    return a - b

@mcp.tool()
def get_me(ctx: Context) -> dict:
    """
    Get authenticated user information from the verified JWT token.
    """    
    claims = get_access_token().claims
    
    return {
        "user_id": claims.get('sub', 'N/A'),
        "uid": claims.get('uid'),
        "issuer": claims.get('iss'),
        "audience": claims.get('aud'),
        "client_id": claims.get('cid'),
        "scopes": claims.get('scp', claims.get('scope', [])),
        "issued_at": datetime.fromtimestamp(claims['iat']).isoformat() if claims.get('iat') else None,
        "expires_at": datetime.fromtimestamp(claims['exp']).isoformat() if claims.get('exp') else None,
        "token_id": claims.get('jti'),
    }

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000, stateless_http=True)
