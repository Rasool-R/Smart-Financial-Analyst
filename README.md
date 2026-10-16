# Smart Financial Analyst

A small LLM-powered financial assistant focused on the Iranian market. It exposes live market data (Tehran stocks, global gold, USD/Toman) as **tools** through an [MCP](https://modelcontextprotocol.io) server, and lets an LLM call them to answer questions in Persian, including estimating the price of 18-karat gold per gram.

The repo also includes a notebook that shows the same idea using plain function calling with the OpenAI and Anthropic APIs, before moving to MCP.

## Features

- **Stock info**: last price, daily change %, and volume for any TSETMC ticker (e.g. `فولاد`, `خودرو`).
- **Global gold price**: XAU price per ounce in USD.
- **USD → Toman rate**: latest exchange rate from navasan.tech.
- **Built-in analyst prompt**: served by the MCP server itself. It forces the model to use tools instead of guessing, and defines the 18k gold formula:
  `(ounce price in USD / 31.1) × USD rate in Toman × 0.75`
- **Tool-calling client**: connects to the server, converts MCP tools to OpenAI function-calling format, and runs the tool loop (up to 8 rounds). Works with any OpenAI-compatible API.

## Project Structure

```
Smart-Financial-Analyst/
├── mcp_finance_server/
│   ├── server.py          # FastMCP server: tools + analyst prompt
│   ├── client.py          # CLI client that connects an LLM to the server
│   ├── requirements.txt
│   └── tools/
│       ├── stock_info.py  # TSETMC data via pytse-client
│       ├── gold_price.py  # gold-api.com
│       └── usd_rate.py    # navasan.tech
├── p1.ipynb               # Function-calling demo (OpenAI + Anthropic)
├── openai_schema.json     # Tool schema, OpenAI format
└── anthropic_schema.json  # Tool schema, Anthropic format
```

## Getting Started

**1. Install dependencies**

```bash
cd mcp_finance_server
pip install -r requirements.txt
```

**2. Create a `.env` file** in `mcp_finance_server/`

```env
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o              # any model that supports tool calling
OPENAI_BASE_URL=                 # optional, for OpenAI-compatible providers
NAVASAN_API_KEY=your_navasan_key # required for the USD rate tool
```

**3. Run the client**

```bash
python client.py
```

The client starts the MCP server automatically over stdio. Then ask something like:

```
Enter your financial question: قیمت تقریبی هر گرم طلای ۱۸ عیار چقدره؟
```

You can also run the server alone (`python server.py`) and plug it into any MCP-compatible client.

## Notes

- Stock data comes from TSETMC and the USD rate from navasan.tech, so both need access to those services from your network.
- The 18k gold price is a theoretical estimate from global gold and the exchange rate. The real Iranian market price can differ (market premium, spread, taxes, fees).
- The notebook `p1.ipynb` uses `OPENAI_API_URL` and `ANTHROPIC_API_KEY`, while the MCP client uses `OPENAI_BASE_URL`.

## Tech Stack

Python · MCP (FastMCP) · OpenAI API · Anthropic API · pytse-client · requests
