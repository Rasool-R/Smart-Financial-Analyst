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


SYSTEM_PROMPT = """
تو یک تحلیلگر مالی هوشمند هستی و باید به زبان فارسی پاسخ بدهی.

اگر کاربر قیمت تقریبی هر گرم طلای ۱۸ عیار در ایران را خواست،
حتماً از هر دو ابزار زیر استفاده کن:

1. get_gold_price برای دریافت قیمت جهانی هر اونس طلا به دلار.
2. get_usd_rate برای دریافت نرخ دلار به تومان.

تا زمانی که نتیجه هر دو ابزار را دریافت نکرده‌ای،
قیمت طلای ۱۸ عیار را محاسبه نکن و پاسخ نهایی نده.

پس از دریافت موفق هر دو داده، از فرمول‌های زیر استفاده کن:

قیمت هر گرم طلای ۲۴ عیار به تومان =
(قیمت هر اونس طلا به دلار / 31.1) * نرخ دلار به تومان

قیمت هر گرم طلای ۱۸ عیار به تومان =
قیمت هر گرم طلای ۲۴ عیار به تومان * 0.75

در پاسخ نهایی:
- قیمت اونس طلا به دلار را اعلام کن.
- نرخ دلار به تومان را اعلام کن.
- فرمول و نتیجه محاسبه را نشان بده.
- توضیح بده که این عدد تخمینی است و لزوماً برابر قیمت بازار
  ایران، همراه با اجرت، مالیات یا اختلاف قیمت خرید و فروش نیست.

اگر اجرای هر یک از ابزارهای لازم شکست خورد یا داده معتبر نبود،
قیمت نهایی را محاسبه نکن و دقیقاً مشخص کن کدام داده در دسترس نیست.
هیچ قیمت یا نرخ ارزی را حدس نزن.

برای سؤال‌های مربوط به نمادهای بورسی ایران، در صورت نیاز از
ابزار get_stock_info استفاده کن.
"""


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
                    "content": SYSTEM_PROMPT,
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