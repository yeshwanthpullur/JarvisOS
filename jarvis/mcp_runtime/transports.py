"""MCP transport boundaries. No installation or arbitrary shell evaluation."""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import os
from pathlib import Path
import shutil
from threading import Event, Thread
from typing import Any, Protocol
from urllib.parse import urlsplit


class MCPTransportError(RuntimeError):
    """Normalized transport failure safe for bounded diagnostics."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class MCPTransport(Protocol):
    def connect(self): ...
    def initialize(self): ...
    def list_tools(self): ...
    def list_resources(self): ...
    def read_resource(self, uri): ...
    def list_prompts(self): ...
    def call_tool(self, name, arguments): ...
    def close(self): ...
    def health(self): ...


def _model_data(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, (tuple, list)):
        return [_model_data(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _model_data(item) for key, item in value.items()}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


class LocalStdioTransport:
    """Synchronous boundary over the official MCP SDK stdio client."""

    _SAFE_ENV_KEYS = (
        "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP",
        "APPDATA", "LOCALAPPDATA", "HOME", "USERPROFILE",
    )

    def __init__(
        self,
        executable: str,
        args: tuple[str, ...] = (),
        *,
        allowed_executables: tuple[str, ...] = (),
        timeout: int = 10,
        call_timeout: int = 30,
        credential_env: dict[str, str] | None = None,
        installation_allowed: bool = False,
    ) -> None:
        self.executable = executable
        self.args = tuple(args)
        self.allowed = tuple(allowed_executables)
        self.timeout = max(1, int(timeout))
        self.call_timeout = max(1, int(call_timeout))
        self.credential_env = dict(credential_env or {})
        self.installation_allowed = installation_allowed
        self.process = None
        self._thread: Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._session: Any = None
        self._shutdown: asyncio.Event | None = None
        self._startup = Event()
        self._initialize_result: Any = None
        self._capabilities: dict[str, Any] = {}
        self._error_code = ""
        self._effective_executable = self.executable
        self._effective_args = self.args

    @staticmethod
    def sdk_available() -> bool:
        try:
            import mcp  # noqa: F401
            from mcp.client.stdio import stdio_client  # noqa: F401
        except ImportError:
            return False
        return True

    def _validate_executable(self) -> None:
        has_path = any(sep in self.executable for sep in ("/", "\\"))
        if has_path:
            requested_path = os.path.normcase(os.path.abspath(self.executable))
            allowed_paths = {
                os.path.normcase(os.path.abspath(item))
                for item in self.allowed
                if any(sep in item for sep in ("/", "\\"))
            }
            if requested_path not in allowed_paths or not Path(self.executable).is_file():
                raise PermissionError("mcp_executable_path_not_allowed")
            return
        requested = Path(self.executable).name.lower()
        allowed = {Path(item).name.lower() for item in self.allowed if not any(sep in item for sep in ("/", "\\"))}
        if requested not in allowed:
            raise PermissionError("mcp_executable_not_allowed")

    def _environment(self) -> dict[str, str]:
        env = {key: os.environ[key] for key in self._SAFE_ENV_KEYS if os.environ.get(key)}
        env.update(self.credential_env)
        if Path(self.executable).name.lower() in {"npx", "npx.cmd", "npm", "npm.cmd"} and not self.installation_allowed:
            env.update({"NPM_CONFIG_OFFLINE": "true", "NPM_CONFIG_UPDATE_NOTIFIER": "false", "NO_UPDATE_NOTIFIER": "1"})
        return env

    def _resolve_effective_command(self) -> None:
        """Resolve one approved cached npx package without invoking npm installation."""
        executable_name = Path(self.executable).name.lower()
        if executable_name not in {"npx", "npx.cmd"} or self.installation_allowed:
            return
        if len(self.args) < 2 or self.args[:2] != ("-y", "@playwright/mcp@latest"):
            raise MCPTransportError("mcp_npx_package_not_allowed")
        cache_value = os.environ.get("NPM_CONFIG_CACHE", "")
        cache_root = Path(cache_value).expanduser() if cache_value else Path(os.environ.get("LOCALAPPDATA", "")) / "npm-cache"
        node = shutil.which("node.exe") or shutil.which("node")
        candidates: list[tuple[float, Path]] = []
        try:
            for package_json in (cache_root / "_npx").glob("*/node_modules/@playwright/mcp/package.json"):
                data = json.loads(package_json.read_text(encoding="utf-8"))
                cli = package_json.parent / str(data.get("bin", {}).get("playwright-mcp", ""))
                if data.get("name") == "@playwright/mcp" and cli.is_file():
                    candidates.append((package_json.stat().st_mtime, cli))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            candidates = []
        if not node or not candidates:
            raise MCPTransportError("mcp_package_not_cached")
        cli = max(candidates, key=lambda item: item[0])[1]
        self._effective_executable = node
        self._effective_args = (str(cli),) + self.args[2:]

    def connect(self) -> bool:
        self._validate_executable()
        self._resolve_effective_command()
        if self.health():
            return True
        if not self.sdk_available():
            raise MCPTransportError("mcp_sdk_unavailable")
        self._startup.clear()
        self._error_code = ""
        self._thread = Thread(target=self._thread_main, name="jarvis-mcp-stdio", daemon=True)
        self._thread.start()
        if not self._startup.wait(self.timeout):
            self.close()
            raise MCPTransportError("mcp_startup_timeout")
        if self._error_code:
            self.close()
            raise MCPTransportError(self._error_code)
        return self.health()

    def _thread_main(self) -> None:
        try:
            asyncio.run(self._session_main())
        except MCPTransportError as exc:
            self._error_code = exc.code
            self._startup.set()
        except BaseException as exc:
            name = type(exc).__name__.lower()
            self._error_code = "mcp_startup_timeout" if "timeout" in name else "mcp_server_start_failed"
            self._startup.set()
        finally:
            self._session = None
            self._loop = None

    async def _session_main(self) -> None:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        self._loop = asyncio.get_running_loop()
        self._shutdown = asyncio.Event()
        parameters = StdioServerParameters(command=self._effective_executable, args=list(self._effective_args), env=self._environment())
        try:
            async with stdio_client(parameters) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    self._session = session
                    self._initialize_result = await asyncio.wait_for(session.initialize(), timeout=self.timeout)
                    initialized = _model_data(self._initialize_result)
                    self._capabilities = initialized.get("capabilities", {}) if isinstance(initialized, dict) else {}
                    self._startup.set()
                    await self._shutdown.wait()
        except asyncio.TimeoutError as exc:
            self._error_code = "mcp_startup_timeout"
            self._startup.set()
            raise MCPTransportError("mcp_startup_timeout") from exc
        except BaseException:
            self._startup.set()
            raise

    def initialize(self) -> Any:
        self.connect()
        return _model_data(self._initialize_result)

    def _invoke(self, method: str, *args: Any, **kwargs: Any) -> Any:
        self.connect()
        if self._loop is None or self._session is None:
            raise MCPTransportError("mcp_session_unavailable")
        operation = getattr(self._session, method)(*args, **kwargs)
        future = asyncio.run_coroutine_threadsafe(operation, self._loop)
        try:
            return future.result(timeout=self.call_timeout)
        except concurrent.futures.TimeoutError as exc:
            future.cancel()
            self.close()
            raise MCPTransportError("mcp_call_timeout") from exc
        except Exception as exc:
            raise MCPTransportError("mcp_protocol_error") from exc

    def list_tools(self) -> tuple[dict[str, Any], ...]:
        if "tools" not in self._capabilities:
            return ()
        result = self._invoke("list_tools")
        return tuple(_model_data(item) for item in getattr(result, "tools", ()))

    def list_resources(self) -> tuple[dict[str, Any], ...]:
        if "resources" not in self._capabilities:
            return ()
        result = self._invoke("list_resources")
        return tuple(_model_data(item) for item in getattr(result, "resources", ()))

    def read_resource(self, uri: str) -> Any:
        if "resources" not in self._capabilities:
            raise MCPTransportError("mcp_resources_unsupported")
        result = self._invoke("read_resource", uri)
        return _model_data(getattr(result, "contents", result))

    def list_prompts(self) -> tuple[dict[str, Any], ...]:
        if "prompts" not in self._capabilities:
            return ()
        result = self._invoke("list_prompts")
        return tuple(_model_data(item) for item in getattr(result, "prompts", ()))

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        result = self._invoke("call_tool", name, arguments=arguments)
        return _model_data(getattr(result, "content", result))

    def health(self) -> bool:
        return bool(self._thread and self._thread.is_alive() and self._session is not None and not self._error_code)

    def close(self) -> None:
        loop, shutdown, thread = self._loop, self._shutdown, self._thread
        if loop is not None and shutdown is not None and loop.is_running():
            loop.call_soon_threadsafe(shutdown.set)
        if thread is not None and thread.is_alive():
            thread.join(timeout=3)
        self._thread = None
        self._session = None


class HTTPMCPTransport:
    """Validated HTTP endpoint placeholder; remote HTTP remains disabled by policy."""

    def __init__(self, endpoint: str, *, remote: bool = False, allowed_hosts: tuple[str, ...] = ()):
        parsed = urlsplit(endpoint)
        host = (parsed.hostname or "").lower()
        if parsed.username or parsed.password:
            raise ValueError("credentials_in_url")
        if remote and (parsed.scheme != "https" or host not in allowed_hosts):
            raise ValueError("remote_mcp_endpoint_blocked")
        if not remote and (parsed.scheme not in {"http", "https"} or host not in {"localhost", "127.0.0.1", "::1"}):
            raise ValueError("local_mcp_endpoint_invalid")
        self.endpoint = endpoint
        self.remote = remote

    def connect(self): return True
    def initialize(self): raise MCPTransportError("mcp_http_protocol_adapter_required")
    def list_tools(self): return ()
    def list_resources(self): return ()
    def read_resource(self, uri): raise MCPTransportError("mcp_http_protocol_adapter_required")
    def list_prompts(self): return ()
    def call_tool(self, name, arguments): raise MCPTransportError("mcp_http_protocol_adapter_required")
    def close(self): return None
    def health(self): return False
