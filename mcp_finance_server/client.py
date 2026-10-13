import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


load_dotenv()


def create_openai_client():
    """Building an OpenAI client or an API compatible with it."""
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")

    if not api_key:
        raise RuntimeError(
            "The OPENAI_API_KEY variable is not set in the .env file."
        )

    client_kwargs = {"api_key": api_key}

    if base_url:
        client_kwargs["base_url"] = base_url

    return OpenAI(**client_kwargs)


def convert_mcp_tools_to_openai(mcp_tools):
    """Converting MCP tools into the model's function-calling format."""
    openai_tools = []

    for tool in mcp_tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.inputSchema,
            },
        })

    return openai_tools


def extract_tool_result(result):
    """Converting the MCP tool output into text suitable for submission to the model."""
    content = []

    for item in result.content:
        if hasattr(item, "text"):
            content.append(item.text)
        else:
            content.append(str(item))

    output = "\n".join(content)

    if result.isError:
        return json.dumps(
            {
                "success": False,
                "error": output or "Tool execution failed.",
            },
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "success": True,
            "result": output,
        },
        ensure_ascii=False,
    )


async def main():
    model = os.getenv("OPENAI_MODEL")

    if not model:
        raise RuntimeError(
            "The OPENAI_MODEL variable is not set in the .env file."
        )

    client = create_openai_client()

    server_path = Path(__file__).with_name("server.py")

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
        cwd=str(server_path.parent),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            prompt_result = await session.get_prompt(
                "financial_analyst_prompt"
            )

            prompt_text = "\n".join(
                message.content.text
                for message in prompt_result.messages
                if hasattr(message.content, "text")
            )

            if not prompt_text.strip():
                raise RuntimeError(
                    "Financial analyst prompt not received from MCP Server.."
                )

            print("MCP prompt loaded successfully.")

            mcp_response = await session.list_tools()
            openai_tools = convert_mcp_tools_to_openai(
                mcp_response.tools
            )

            print("MCP tools:")
            for tool in mcp_response.tools:
                print(f"- {tool.name}")

            user_question = input(
                "\nEnter your financial question: "
            ).strip()

            if not user_question:
                print("The question cannot be left blank.")
                return

            messages = [
                {
                    "role": "system",
                    "content": prompt_text,
                },
                {
                    "role": "user",
                    "content": user_question,
                },
            ]

            max_rounds = 8

            for _ in range(max_rounds):
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=openai_tools,
                    tool_choice="auto",
                )

                assistant_message = response.choices[0].message

                messages.append(
                    assistant_message.model_dump(
                        exclude_none=True
                    )
                )

                if not assistant_message.tool_calls:
                    print("\nAnalyst's Response:")
                    print(assistant_message.content or "")
                    return

                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name

                    try:
                        arguments = json.loads(
                            tool_call.function.arguments
                        )

                        print(f"\nExecuting tool: {tool_name}")

                        result = await session.call_tool(
                            tool_name,
                            arguments=arguments,
                        )

                        tool_output = extract_tool_result(result)

                    except Exception as exc:
                        tool_output = json.dumps(
                            {
                                "success": False,
                                "error": str(exc),
                            },
                            ensure_ascii=False,
                        )

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_output,
                    })

            print(
                "The model did not provide a final answer even after several steps. "
                "Please try the question again."
            )


if __name__ == "__main__":
    asyncio.run(main())