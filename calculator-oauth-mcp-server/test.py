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

# access_token = ""
print(f"Access Token: {access_token}")
print(f"Expires in: {token_data['expires_in']} seconds")

# token = "eyJraWQiOiJSVUVWLTl1VG9jbUdEZjZhaW5XSUlDNUVxN0dyNUktN2E0X2dtRS0wMEQ4IiwiYWxnIjoiUlMyNTYifQ.eyJ2ZXIiOjEsImp0aSI6IkFULkxvdTBoZjZCZnl0V1FneENrU1BUVTExT2hxN1IzdmlYdWNjMEFITDZUWGsiLCJpc3MiOiJodHRwczovL3RydWVmb3VuZHJ5Lm9rdGEuY29tL29hdXRoMi9hdXN4eGdwanZoS1pSdVpmeTY5NyIsImF1ZCI6Imh0dHBzOi8vY2FsY3VsYXRvci1tY3Atc2VydmVyLmV4YW1wbGUuY29tIiwiaWF0IjoxNzY0NTgxNzA4LCJleHAiOjE3NjQ1ODUzMDgsImNpZCI6IjBvYXh0bTlmaXJ1Y1FHQkU1Njk3Iiwic2NwIjpbImNhbGN1bGF0b3IuYWRkIl0sInN1YiI6IjBvYXh0bTlmaXJ1Y1FHQkU1Njk3In0.QuU5PSZmMYNiqEcdw0FaXNEg92PEdOHdi6YzafY3qeb0rAL7BS5LS6ya3_yjvIAzegYzi53jjv3jNWGfJjPJU-VfzIlwWwB5vD4qtKlSUeDLUPx3qMFkjxTojjm7q_NcEnITNqsWo3lUPHtPKmRxX2X9o9SuKYzmabeYgRakdlie-VVLFiHr3T6Utx3ZQ89bmI54_iZxOBHZXDXrpsyuMniXoi1AX4pMCfKuKDyHSEpxeEjeZ3Nv__b4ZPSCp3UkNj0LlXDzkHxOY1jh3rrlkEpTsHGWBaq6qANk26SghWgQ2-G1QvIHOv4snTb75NZ43Rsb99MjQBwG5sVkgE8TYw"
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
