import asyncio
import os

from dotenv import load_dotenv

from mcp_servers.mcp_servers import bundle_servers, get_server_config,ServerConfig

load_dotenv(override = True)


async def main():
    reports_dir = os.getenv('REPORTS_DIR', os.path.join(os.getcwd(), 'reports'))
    os.makedirs(reports_dir, exist_ok = True)

    configs = get_server_config(reports_dir)


    async with bundle_servers(configs) as servers:
        for alias, server in servers.items():
            print(f'\n=== {alias} ===')

            tools = await server.list_tools()

            # Agents SDK kann je nach Version entweder direkt eine Liste liefern
            # oder ein Objekt mit .tools – wir fangen beides ab:
            tool_list = tools.tools if hasattr(tools, 'tools') else tools

            tool_names = [t.name for t in tool_list]
            print('tools:', tool_names)

        fs = servers['filesystem']

        # Erst tool names anschauen. Falls list_directory nicht existiert,
        # nimm den exakten Namen aus der Ausgabe.
        allowed = await fs.call_tool(
            tool_name = 'list_allowed_directories',
            arguments = {}
        )
        print('allowed:', allowed)

        root_dir = reports_dir

        result = await fs.call_tool(
            tool_name = 'list_directory',
            arguments = {'path': root_dir}
        )
        print(result)



if __name__ == '__main__':
    asyncio.run(main())

