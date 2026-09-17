"""MCP クライアント（mcp 1.30.0 の Streamable HTTP）。一つの関数の中で一つの接続を使う。"""

from __future__ import annotations

import json
from typing import Any, Callable

import anyio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


def session(url: str, body: Callable[[ClientSession], Any], timeout: float = 60.0) -> Any:
    """接続して初期化し、body(session) の戻り値を返す。"""

    async def main():
        with anyio.fail_after(timeout):
            async with streamablehttp_client(url) as (read, write, _):
                async with ClientSession(read, write) as client:
                    await client.initialize()
                    return await body(client)

    return anyio.run(main)


def payload(result) -> dict:
    """call_tool の結果から JSON（応答の外枠）を取り出す。"""
    assert result.content and result.content[0].type == "text"
    return json.loads(result.content[0].text)


def error_text(result) -> str:
    return "".join(c.text for c in result.content if getattr(c, "type", "") == "text")
