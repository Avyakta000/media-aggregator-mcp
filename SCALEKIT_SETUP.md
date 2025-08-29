# ScaleKit Authentication Setup for Media Aggregator MCP Server

This guide explains how to set up ScaleKit authentication for your Media Aggregator MCP server.

## Overview

The server now uses ScaleKit for OAuth 2.0 authentication, providing secure access to the MCP tools without requiring scopes (as requested). The authentication middleware validates Bearer tokens for all requests except the well-known endpoints.

## Prerequisites

1. A ScaleKit account and environment
2. Python 3.8+ with the required dependencies
3. Environment variables configured

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Copy the environment template:
```bash
cp env.example .env
```

3. Configure your ScaleKit settings in the `.env` file (see Configuration section below)

## Configuration

### ScaleKit Environment Variables

Update your `.env` file with the following ScaleKit configuration:

```env
# ScaleKit Environment URL
SCALEKIT_ENVIRONMENT_URL=https://your-environment.scalekit.com

# ScaleKit Client ID
SCALEKIT_CLIENT_ID=your_client_id_here

# ScaleKit Client Secret
SCALEKIT_CLIENT_SECRET=your_client_secret_here

# ScaleKit Resource Identifier
SCALEKIT_RESOURCE_IDENTIFIER=your_resource_identifier

# ScaleKit Resource Metadata URL
SCALEKIT_RESOURCE_METADATA_URL=https://your-server.com/.well-known/oauth-protected-resource/mcp

# ScaleKit Authorization Servers
SCALEKIT_AUTHORIZATION_SERVERS=https://your-environment.scalekit.com

# ScaleKit Audience Name
SCALEKIT_AUDIENCE_NAME=your_audience_name

# ScaleKit Resource Name
SCALEKIT_RESOURCE_NAME=FinanceMCP

# ScaleKit Resource Documentation URL
SCALEKIT_RESOURCE_DOCS_URL=https://your-docs-url.com

# Server Port
PORT=3000
```

### Getting ScaleKit Credentials

1. Log into your ScaleKit dashboard
2. Navigate to your environment
3. Create a new application or use an existing one
4. Note down the Client ID and Client Secret
5. Configure the resource settings in your ScaleKit environment

## Running the Server

### Development Mode
```bash
python server.py
```

### Production Mode
```bash
uvicorn server:app --host 0.0.0.0 --port 3000
```

## Authentication Flow

1. **Well-known Endpoint**: The server exposes `/.well-known/oauth-protected-resource/mcp` for OAuth 2.0 discovery
2. **Token Validation**: All requests (except well-known endpoints) require a valid Bearer token
3. **No Scopes**: As requested, the authentication does not enforce specific scopes
4. **Error Handling**: Invalid or missing tokens return 401 Unauthorized responses

## API Endpoints

### Public Endpoints (No Authentication Required)
- `GET /.well-known/oauth-protected-resource/mcp` - OAuth 2.0 discovery endpoint

### Protected Endpoints (Authentication Required)
- All MCP endpoints (tools, resources, prompts)
- All requests must include `Authorization: Bearer <token>` header

## Testing Authentication

### 1. Test Well-known Endpoint
```bash
curl http://localhost:3000/.well-known/oauth-protected-resource/mcp
```

### 2. Test Protected Endpoint (without token)
```bash
curl http://localhost:3000/mcp
# Should return 401 Unauthorized
```

### 3. Test Protected Endpoint (with valid token)
```bash
curl -H "Authorization: Bearer YOUR_VALID_TOKEN" http://localhost:3000/mcp
# Should return MCP server response
```

## Troubleshooting

### Common Issues

1. **Token Validation Failed**
   - Verify your ScaleKit environment URL, client ID, and client secret
   - Ensure the token is valid and not expired
   - Check that the audience matches your configuration

2. **Missing Environment Variables**
   - Ensure all required ScaleKit variables are set in your `.env` file
   - Restart the server after updating environment variables

3. **CORS Issues**
   - The server includes CORS middleware allowing all origins in development
   - For production, update the `allow_origins` list in `main.py`

### Logs

The server provides detailed logging for authentication:
- Authentication middleware logs
- Token validation logs
- Error details for debugging

## Security Considerations

1. **Environment Variables**: Never commit your `.env` file to version control
2. **Client Secrets**: Keep your ScaleKit client secret secure
3. **Production**: Update CORS settings and use HTTPS in production
4. **Token Storage**: Clients should securely store and manage their access tokens

## Integration with MCP Clients

MCP clients should:
1. Discover the OAuth 2.0 configuration via the well-known endpoint
2. Obtain access tokens from ScaleKit
3. Include tokens in the `Authorization` header for all requests
4. Handle 401 responses by refreshing tokens or re-authenticating

## Example MCP Client Configuration

```json
{
  "mcpServers": {
    "finance": {
      "command": "python",
      "args": ["server.py"],
      "env": {
        "SCALEKIT_ENVIRONMENT_URL": "https://your-environment.scalekit.com",
        "SCALEKIT_CLIENT_ID": "your_client_id",
        "SCALEKIT_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```
