# client_test.py
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio

server_params = StdioServerParameters(
    command="python",
    args=["math_mcp_server.py"],
    env=None,
)

async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            prompt = await session.get_prompt("example_prompt", arguments={"question": "how many times did I use 'Code.exe' last month?"})
            print(prompt.messages[0].content.text)

if __name__ == "__main__":
    asyncio.run(main())
