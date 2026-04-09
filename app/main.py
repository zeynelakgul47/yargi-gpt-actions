from __future__ import annotations

import inspect
from typing import Any, Awaitable, Callable

from fastapi import Body, FastAPI, HTTPException
from pydantic import BaseModel, Field

try:
    import mcp_server_main as yargi_mcp
except Exception as exc:  # pragma: no cover - import error is exposed via API
    yargi_mcp = None
    IMPORT_ERROR = str(exc)
else:
    IMPORT_ERROR = None


ToolFn = Callable[..., Awaitable[Any]]


class ExecuteRequest(BaseModel):
    tool_name: str = Field(..., description="Name of the yargi-mcp tool to execute.")
    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="JSON object containing the arguments expected by the selected tool.",
    )


class ToolResult(BaseModel):
    tool_name: str
    result: Any


def _serialize(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, tuple):
        return [_serialize(item) for item in value]
    return value


def _signature_payload(func: ToolFn) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for name, parameter in inspect.signature(func).parameters.items():
        if name == "ctx":
            continue
        entry: dict[str, Any] = {"kind": str(parameter.kind)}
        if parameter.annotation is not inspect._empty:
            entry["annotation"] = str(parameter.annotation)
        if parameter.default is not inspect._empty:
            entry["default"] = parameter.default
            entry["required"] = False
        else:
            entry["required"] = True
        payload[name] = entry
    return payload


def _tool_registry() -> dict[str, dict[str, Any]]:
    if yargi_mcp is None:
        return {}

    return {
        "search_bedesten_unified": {
            "fn": yargi_mcp.search_bedesten_unified,
            "summary": "Search Yargitay, Danistay, local courts, appeal courts, and KYB decisions.",
        },
        "get_bedesten_document_markdown": {
            "fn": yargi_mcp.get_bedesten_document_markdown,
            "summary": "Fetch a Bedesten decision and convert it to Markdown.",
        },
        "search_anayasa_unified": {
            "fn": yargi_mcp.search_anayasa_unified,
            "summary": "Search Constitutional Court decisions for norm review or individual applications.",
        },
        "get_anayasa_document_unified": {
            "fn": yargi_mcp.get_anayasa_document_unified,
            "summary": "Fetch a Constitutional Court decision as paginated Markdown.",
        },
        "search_emsal_detailed_decisions": {
            "fn": yargi_mcp.search_emsal_detailed_decisions,
            "summary": "Search UYAP precedent decisions with detailed filters.",
        },
        "get_emsal_document_markdown": {
            "fn": yargi_mcp.get_emsal_document_markdown,
            "summary": "Fetch a UYAP precedent decision as Markdown.",
        },
        "search_uyusmazlik_decisions": {
            "fn": yargi_mcp.search_uyusmazlik_decisions,
            "summary": "Search Uyusmazlik Mahkemesi decisions.",
        },
        "get_uyusmazlik_document_markdown_from_url": {
            "fn": yargi_mcp.get_uyusmazlik_document_markdown_from_url,
            "summary": "Fetch a Uyusmazlik Mahkemesi decision from its URL.",
        },
        "search_kik_v2_decisions": {
            "fn": yargi_mcp.search_kik_v2_decisions,
            "summary": "Search Kamu Ihale Kurulu decisions.",
        },
        "get_kik_v2_document_markdown": {
            "fn": yargi_mcp.get_kik_v2_document_markdown,
            "summary": "Fetch a Kamu Ihale Kurulu decision as paginated Markdown.",
        },
        "search_rekabet_kurumu_decisions": {
            "fn": yargi_mcp.search_rekabet_kurumu_decisions,
            "summary": "Search Competition Authority decisions.",
        },
        "get_rekabet_kurumu_document": {
            "fn": yargi_mcp.get_rekabet_kurumu_document,
            "summary": "Fetch a Competition Authority decision as Markdown.",
        },
        "search_sayistay_unified": {
            "fn": yargi_mcp.search_sayistay_unified,
            "summary": "Search Court of Accounts decisions across chamber types.",
        },
        "get_sayistay_document_unified": {
            "fn": yargi_mcp.get_sayistay_document_unified,
            "summary": "Fetch a Court of Accounts decision as Markdown.",
        },
        "search_kvkk_decisions": {
            "fn": yargi_mcp.search_kvkk_decisions,
            "summary": "Search KVKK decisions.",
        },
        "get_kvkk_document_markdown": {
            "fn": yargi_mcp.get_kvkk_document_markdown,
            "summary": "Fetch a KVKK decision as paginated Markdown.",
        },
        "search_bddk_decisions": {
            "fn": yargi_mcp.search_bddk_decisions,
            "summary": "Search BDDK decisions.",
        },
        "get_bddk_document_markdown": {
            "fn": yargi_mcp.get_bddk_document_markdown,
            "summary": "Fetch a BDDK decision as paginated Markdown.",
        },
        "search_sigorta_tahkim_decisions": {
            "fn": yargi_mcp.search_sigorta_tahkim_decisions,
            "summary": "Search Sigorta Tahkim Commission decisions.",
        },
        "get_sigorta_tahkim_document_markdown": {
            "fn": yargi_mcp.get_sigorta_tahkim_document_markdown,
            "summary": "Fetch a Sigorta Tahkim journal issue as paginated Markdown.",
        },
        "search_within_sigorta_tahkim_issue": {
            "fn": yargi_mcp.search_within_sigorta_tahkim_issue,
            "summary": "Search within a Sigorta Tahkim issue for matching decisions.",
        },
    }


TOOL_REGISTRY = _tool_registry()

app = FastAPI(
    title="Yargi GPT Actions Adapter",
    version="0.1.0",
    description=(
        "OpenAPI adapter that exposes yargi-mcp legal search tools in a format "
        "ChatGPT Custom GPT Actions can call."
    ),
)


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "service": "yargi-gpt-actions-adapter",
        "status": "ok" if IMPORT_ERROR is None else "degraded",
        "openapi_url": "/openapi.json",
        "docs_url": "/docs",
        "tools_url": "/tools",
        "tool_count": len(TOOL_REGISTRY),
        "import_error": IMPORT_ERROR,
    }


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "healthy" if IMPORT_ERROR is None else "unhealthy",
        "import_error": IMPORT_ERROR,
        "tool_count": len(TOOL_REGISTRY),
    }


@app.get("/tools")
async def list_tools() -> dict[str, Any]:
    return {
        "tools": [
            {
                "name": name,
                "summary": meta["summary"],
                "signature": _signature_payload(meta["fn"]),
            }
            for name, meta in TOOL_REGISTRY.items()
        ]
    }


async def _run_tool(tool_name: str, arguments: dict[str, Any]) -> ToolResult:
    if IMPORT_ERROR is not None:
        raise HTTPException(status_code=500, detail=f"yargi-mcp import failed: {IMPORT_ERROR}")

    tool = TOOL_REGISTRY.get(tool_name)
    if tool is None:
        raise HTTPException(status_code=404, detail=f"Unsupported tool: {tool_name}")

    try:
        result = await tool["fn"](**arguments)
    except TypeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid arguments for {tool_name}: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"{tool_name} failed: {exc}") from exc

    return ToolResult(tool_name=tool_name, result=_serialize(result))


@app.post("/execute", response_model=ToolResult)
async def execute_tool(payload: ExecuteRequest) -> ToolResult:
    return await _run_tool(payload.tool_name, payload.arguments)


def _register_action_endpoint(tool_name: str, summary: str) -> None:
    async def endpoint(arguments: dict[str, Any] = Body(default_factory=dict)) -> ToolResult:
        return await _run_tool(tool_name, arguments)

    endpoint.__name__ = f"action_{tool_name}"
    app.post(
        f"/actions/{tool_name}",
        response_model=ToolResult,
        summary=summary,
        description=(
            f"Executes `{tool_name}` from yargi-mcp. "
            "Send a JSON object containing the tool arguments."
        ),
    )(endpoint)


for name, meta in TOOL_REGISTRY.items():
    _register_action_endpoint(name, meta["summary"])
