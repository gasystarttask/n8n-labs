

import asyncio
from typing import Any, Dict, Optional, cast

from rpds import List
from .server import EegDatasetServer

class _ServerHolder:
	instance: Optional[EegDatasetServer] = None

def _get_server() -> EegDatasetServer:
	if _ServerHolder.instance is None:
		_ServerHolder.instance = EegDatasetServer()
	return _ServerHolder.instance

# Tool registry for backwards compatibility
TOOLS = {}

def register_tool(name: str):
	def decorator(func):
		TOOLS[name] = func
		return func
	return decorator

@register_tool("getOne")
async def getOne(eeg_id: str) -> Optional[Dict[str, Any]]:
	server = _get_server()
	result = await server.getOne(eeg_id)
	return cast(Optional[Dict[str, Any]], result)

@register_tool("getMany")
async def getMany(skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
	server = _get_server()
	result = await server.getMany(skip=skip, limit=limit)
	return cast(List[Dict[str, Any]], result)

@register_tool("find")
async def find(keyword: str, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
	server = _get_server()
	result = await server.find(keyword=keyword, skip=skip, limit=limit)
	return cast(List[Dict[str, Any]], result)

def run_tool(name: str, **kwargs) -> Any:
	if name not in TOOLS:
		return {"success": False, "error": f"Unknown tool: {name}"}
	tool_func = TOOLS[name]
	return asyncio.run(tool_func(**kwargs))

