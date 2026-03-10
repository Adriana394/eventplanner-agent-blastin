import os 
from dotenv import load_dotenv
import httpx

from mcp.server.fastmcp import FastMCP


load_dotenv(override = True)

DZT_URL = os.getenv('DZT_URL')
DZT_API_KEY = os.getenv('DZT_API_KEY')



mcp = FastMCP('dzt')


async def _dzt_rpc_call(method: str, params: dict | None = None) -> dict:
    """
    Helper function for DZT requests
    """
    headers = {
        'x-api-key': DZT_API_KEY
        'Content-Type': 'application/json',
    }
    
    payload = {
        'jsonrpc': 2.0,
        'id': 'dzt-call',
        'method': method,
    }
    
    if params is not None:
        payload['params'] = params
        
    async with httpx.AsyncClient(timeout = 30.0) as client:
        response = await client.post(DZT_URL, headers = headers, json = payload)
        response.raise_for_status()
        return response.json()
    
    
    
@mcp.tool()
async def list_dzt_tools() -> dict:
    return await _dzt_rpc_call('tools/list')



        