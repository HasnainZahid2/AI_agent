

# langgraph_mcp_client.py
from typing import List
from typing_extensions import TypedDict
from typing import Annotated

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import AnyMessage, add_messages

from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_mcp_adapters.resources import load_mcp_resources
from langchain_mcp_adapters.prompts import load_mcp_prompt
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_core.messages import HumanMessage, AIMessage
import asyncio

server_params = StdioServerParameters(
    command="python",
    args=["math_mcp_server.py"],
    env=None,
)


async def create_graph(session):
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        api_key=""
    )

    tools = await load_mcp_tools(session)
    llm_with_tool = llm.bind_tools(tools)

    system_prompt = await load_mcp_prompt(session, "system_prompt")
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt[0].content),
        MessagesPlaceholder("messages")
    ])
    chat_llm = prompt_template | llm_with_tool

    class State(TypedDict):
        messages: Annotated[List[AnyMessage], add_messages]

    def chat_node(state: State) -> State:
        state["messages"] = chat_llm.invoke({"messages": state["messages"]})
        return state

    graph_builder = StateGraph(State)
    graph_builder.add_node("chat_node", chat_node)
    graph_builder.add_node("tool_node", ToolNode(tools=tools))
    graph_builder.add_edge(START, "chat_node")
    graph_builder.add_conditional_edges("chat_node", tools_condition, {"tools": "tool_node", "__end__": END})
    graph_builder.add_edge("tool_node", "chat_node")
    graph = graph_builder.compile()  
    return graph


async def main():
    config = {"configurable": {"thread_id": 1234}}
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await load_mcp_tools(session)
            print("Available tools:", [tool.name for tool in tools])

            example_prompt = await load_mcp_prompt(session, "example_prompt", arguments={"question": "what is 2+2"})
            print("example_prompt:", example_prompt[0].content)

            system_prompt = await load_mcp_prompt(session, "system_prompt")
            print("system_prompt:", system_prompt[0].content)

            resources = await load_mcp_resources(session, uris=["greeting://Alice", "config://app"])
            print("Available resources:", [res.data for res in resources])

            agent = await create_graph(session)

            
            messages = []

            while True:
                user_input = input("User: ")
                messages.append(HumanMessage(content=user_input))
                response = await agent.ainvoke({"messages": messages}, config=config)
                reply = response["messages"][-1]
                print("AI:", reply.content)
                messages.append(reply)

if __name__ == "__main__":
    asyncio.run(main())




# from typing import TypedDict, Annotated
# from langgraph.graph import StateGraph, START, END
# from math_mcp_server import query_sql  

# # Define input/output schema
# class GraphState(TypedDict):
#     input: Annotated[str, "SQL Query"]
#     output: Annotated[list, "Query result"]  

# # Wrapper function for the tool
# def run_query_sql(state: GraphState) -> GraphState:
#     query = state["input"]
#     result = query_sql(query)  
#     return {"input": query, "output": result}

# graph = StateGraph(GraphState)

# graph.add_node("query_sql_node", run_query_sql)
# graph.add_edge(START, "query_sql_node")
# graph.add_edge("query_sql_node", END)

# graph_executor = graph.compile()

# # Test
# if __name__ == "__main__":
#     result = graph_executor.invoke({
#         "input": "SELECT * FROM usage_logs LIMIT 3;"
#     })
#     print(result["output"])  
