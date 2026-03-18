import os

from dataclasses import dataclass
from typing import Dict, List
from agents.mcp import MCPServerStdio


@dataclass(frozen = True) # dataclass is immutable
class ServerConfig:
    """
    Config container for MCP Server.
    
    Place to define which severs to use.
    Add more servers by appending another ServerConfig.
    
    Fields:
    alias: name 
    command/args: how to start the MCP server as subprocess over stdio
    timeout_seconds: how long client waits before timing out
    """
    alias: str
    command: str
    args: List[str]
    timeout_seconds: int = 120
    
    
def get_server_config(reports_dir: str) -> List[ServerConfig]:
    """
    Centrak place to define all MCP servers used in project.
    
    - Filesystem requires an 'allowed_directory' argument
    - security feature: it can only read and write inside that directory
    """
    reports_dir_path = os.path.abspath(reports_dir)
    
    return [
        ServerConfig(
            alias = 'playwright',
            command = 'npx',
            args = ['-y', '@playwright/mcp@latest'],
            timeout_seconds = 120,
        ),
        
        ServerConfig(
            alias = 'filesystem',
            command = 'npx',
            args = ['-y', '@modelcontextprotocol/server-filesystem', reports_dir_path],
            timeout_seconds = 120,
        ),
        
        ServerConfig(
            alias = 'eventim',
            command = 'python3',
            args = ['-m', 'mcp_servers.event_server'],
            timeout_seconds = 120,
        )
        
        ServerConfig(
            alias = 'dzt',
            command = 'python3',
            args = ['-m', 'mcp_servers.dzt_server'],
            timeout_seconds = 120,
        )
    ]
        
        # Add another Sever
        # ServerConfig(....)
    
    
class MCPServerBundle:
    """
    An async context manager that starts multiple MCP servers and cloeses them cleanly.
    
    Normally, with one server, you write:
        async with MCPServerStdio(...) as server:
            ...

    When you have 2-6 servers, the 'async with ... as a, ... as b' line can get messy.
    This bundle lets you:
    - define servers in a list (configs)
    - start them in a loop
    - access them by alias (servers["playwright"], servers["filesystem"])
    - reliably close them on exit

    Important:
    You see __aenter__ / __aexit__ here because:
    - 'async with X:' internally calls X.__aenter__() and X.__aexit__()
    - We call them manually so we can do it inside a loop.
    """
    
    def __init__(self, configs: List[ServerConfig]):
        self.configs = configs
        self.servers: Dict[str, MCPServerStdio] = {}
        
    async def __aenter__(self) -> Dict[str, MCPServerStdio]:
        """
        Called automatically when write:
        
        async with MCPServerBundle(configs) as server:
        ....
        
        """
        for cfg in self.configs:
            # create client wrapper that start MCP server (stdio)
            
            server = MCPServerStdio(
                params = {'command': cfg.command, 'args': cfg.args},
                client_session_timeout_seconds = cfg.timeout_seconds,
            )
            
            # async with server
            # manually because we are in a loop
            await server.__aenter__()
            
            self.servers[cfg.alias] = server
            
         # return Dict   
        return self.servers
            
            
    async def __aexit__(self, exc_type, exc, tb) -> None:
        """ 
        Called automatically when leaving 'async with' block-
        
        Close all servers.
        """
        for alias, server in reversed(list(self.servers.items())):
            try:
                await server.__aexit__(exc_type, exc, tb)
            except Exception:
                pass
        
        self.servers.clear()
        
        
def bundle_servers(configs: List[ServerConfig]) -> MCPServerBundle:
    """ 
    Looks nicer. 
    """
    return MCPServerBundle(configs)
        