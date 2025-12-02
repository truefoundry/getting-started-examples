import asyncio
from fastmcp import Client
import requests
import base64


# Configuration
TOKEN_ENDPOINT = "https://example.okta.com/oauth2/sdfdsfsdfsd/v1/token"
CLIENT_ID = "sdfsdfdsfsdfs"
CLIENT_SECRET = "sdfsdfsdfasdfsdaf"
AUDIENCE = "https://calculator-mcp-server.example.com"

# Encode credentials
credentials = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()

# Request token
response = requests.post(
    TOKEN_ENDPOINT,
    headers={
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    },
    data={
        "grant_type": "client_credentials",
        "audience": AUDIENCE,
        "scope": "calculator.add"
    }
)

print(response.json())
response.raise_for_status()
token_data = response.json()
access_token = token_data["access_token"]

print(f"Access Token: {access_token}")
print(f"Expires in: {token_data['expires_in']} seconds")

async def main():
    async with Client("http://localhost:8000/mcp", auth=access_token) as client:
        tools = await client.list_tools()
        print(tools)
        result = await client.call_tool(
            name="add", 
            arguments={"a": 1, "b": 2}
        )
        print(result)

asyncio.run(main())
