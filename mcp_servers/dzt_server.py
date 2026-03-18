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
        'x-api-key': DZT_API_KEY,
        'Content-Type': 'application/json',
    }
    
    payload = {
        'jsonrpc': '2.0',
        'id': 'dzt-call',
        'method': method,
    }
    
    if params is not None:
        payload['params'] = params
        
    async with httpx.AsyncClient(timeout = 30.0) as client:
        response = await client.post(DZT_URL, headers = headers, json = payload)
        response.raise_for_status()
        return response.json()
    

async def _dzt_tool_call(tool_name: str, arguments: dict) -> dict:
    """ Helpfer function that calls one remote DZT tool and only the useful payload
    """
    raw_response = await _dzt_rpc_call(
        method = 'tools/call',
        params = {
            'name': tool_name,
            'arguments': arguments
        }
    )
    result = raw_response.get('result', {})
    
    if result.get('isError'):
        raise ValueError(f'DZT tool call failed for {tool_name}: {result}')
    
    return {
        'tool_name': tool_name,
        'arguments': arguments,
        'structuredContent': result.get('structuredContent'),
        'content': result.get('content')
    }
    
    

@mcp.tool()
async def get_pois_by_criteria(
    name: str | None = None,
    keywords: str | None = None,
    type: str | None = None,
    locality: str | None = None,
    region: str | None = None,
    postal_code: str | None = None,
    near_point: str | None = None,
) -> dict:
    """
    Search DZT points of interest such as museums, landmarks, restaurants etc.
    Input notes:
    - keywords should be comma seperated, e.g. 'art, history, viewpoint'
    - near_point format: <distance>km,<lat>,<lon>
    """
    arguments = {}
    
    if name:
        arguments['name'] = name
    if keywords:
        arguments['keywords'] = keywords
    if type:
        arguments['type'] = type
    if locality:
        arguments['locality'] = locality
    if region:
        arguments['region'] = region
    if postal_code:
        arguments['postal_code'] = postal_code
    if near_point:
        arguments['near_point'] = near_point
        
    return await _dzt_tool_call('get_pois_by_criteria', arguments)


@mcp.tool()
async def get_trails_by_criteria(
    name: str | None = None,
    keywords: str | None = None,
    difficulty: str | None = None,
    max_length_km: float | None = None,
    region: str | None = None,
    is_circular: bool | None = None,
    near_point: str | None = None,
) -> dict:
    """ 
    Search DZT hiking and biking trails.
    
    Input notes:
    - difficulty values are typically: 'easy', 'medizm', 'heavy'
    - near_point format: '<distance>km,<lat>,<lon>'
    """
    arguments = {}
    
    if name:
        arguments['name'] = name
    if keywords:
        arguments['keywords'] = keywords
    if difficulty:
        arguments['difficulty'] = difficulty
    if max_length_km is not None:
        arguments['max_length_km'] = max_length_km
    if region:
        arguments['region'] = region
    if is_circular is not None:
        arguments['is_circular'] = is_circular
    if near_point:
        arguments['near_point'] = near_point
    
    return await _dzt_tool_call('get_trails_by_criteria', arguments)


@mcp.tool()
async df get_entity_details(
    uri: str, 
    language: str = 'de',
) -> dict:
    """ 
    Fetch full DZT entity details.
    """
    
    arguments = {
        'uri': uri,
        'language': language,
    }
    
    return await _dzt_tool_call('get_entity_details', arguments)

   
    
if __name__ == 'main':
    mcp.run(transport = 'stdio')



        