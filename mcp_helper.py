import asyncio
import os
import sys
from contextlib import AsyncExitStack
from typing import List, Any, Dict

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_core.tools import StructuredTool
from pydantic import create_model

class MCPClient:
    def __init__(self, server_script_path: str):
        self.server_script_path = server_script_path
        self.session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()
        self._tools_cache = []

    async def connect(self):
        # Use the current python interpreter
        python_exe = sys.executable
        
        server_params = StdioServerParameters(
            command=python_exe,
            args=[self.server_script_path],
            env=os.environ.copy()
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        read, write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(read, write))
        await self.session.initialize()
        
    async def get_tools(self) -> List[StructuredTool]:
        if not self.session:
            raise RuntimeError("Client not connected")
            
        result = await self.session.list_tools()
        tools = []
        
        for tool_info in result.tools:
            # Create a dynamic Pydantic model for the arguments
            input_schema = tool_info.inputSchema
            properties = input_schema.get("properties", {})
            required = input_schema.get("required", [])
            
            fields = {}
            for field_name, field_def in properties.items():
                field_type = field_def.get("type", "string")
                python_type = str
                if field_type == "integer":
                    python_type = int
                elif field_type == "number":
                    python_type = float
                elif field_type == "boolean":
                    python_type = bool
                elif field_type == "array":
                    python_type = list
                elif field_type == "object":
                    python_type = dict
                
                # Handle default values if present in schema, though MCP schema might not always have them
                # For now, we assume optional if not in required
                if field_name in required:
                    fields[field_name] = (python_type, ...)
                else:
                    fields[field_name] = (python_type, None)
            
            # Create the Pydantic model
            if fields:
                ArgsModel = create_model(f"{tool_info.name}Args", **fields)
            else:
                ArgsModel = None

            def make_tool_wrapper(tool_name):
                async def _tool_wrapper(**kwargs):
                    return await self.session.call_tool(tool_name, arguments=kwargs)
                return _tool_wrapper

            lc_tool = StructuredTool.from_function(
                func=None,
                coroutine=make_tool_wrapper(tool_info.name),
                name=tool_info.name,
                description=tool_info.description,
                args_schema=ArgsModel
            )
            tools.append(lc_tool)
            
        self._tools_cache = tools
        return tools

    async def cleanup(self):
        await self.exit_stack.aclose()

async def test_connection():
    # Test connecting to computer_info_server.py
    server_path = os.path.join(os.getcwd(), "computer_info_server.py")
    client = MCPClient(server_path)
    try:
        print(f"Connecting to {server_path}...")
        await client.connect()
        print("Connected!")
        tools = await client.get_tools()
        print(f"Found {len(tools)} tools:")
        for t in tools:
            print(f"- {t.name}: {t.description}")
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(test_connection())
