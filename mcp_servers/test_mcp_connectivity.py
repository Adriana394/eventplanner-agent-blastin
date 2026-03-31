import argparse
import asyncio
import os
import sys
from pathlib import Path

from agents.mcp import MCPServerStdio
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mcp_servers.mcp_servers import get_server_config

load_dotenv(override = True)


def _parse_csv(raw_value: str | None) -> set[str]:
    if not raw_value:
        return set()
    return {part.strip() for part in raw_value.split(",") if part.strip()}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke-test MCP server startup and basic tool access."
    )
    parser.add_argument(
        "--include",
        default=os.getenv("MCP_SMOKE_INCLUDE", ""),
        help="Comma-separated server aliases to include, e.g. filesystem,eventim",
    )
    parser.add_argument(
        "--skip",
        default=os.getenv("MCP_SMOKE_SKIP", ""),
        help="Comma-separated server aliases to skip, e.g. playwright",
    )
    parser.add_argument(
        "--startup-timeout",
        type=float,
        default=float(os.getenv("MCP_SMOKE_STARTUP_TIMEOUT", "60")),
        help="Per-server startup timeout in seconds.",
    )
    parser.add_argument(
        "--tool-timeout",
        type=float,
        default=float(os.getenv("MCP_SMOKE_TOOL_TIMEOUT", "30")),
        help="Per-tool-call timeout in seconds.",
    )
    return parser


def _select_configs(configs, include_aliases: set[str], skip_aliases: set[str]):
    selected = []
    for cfg in configs:
        if include_aliases and cfg.alias not in include_aliases:
            continue
        if cfg.alias in skip_aliases:
            continue
        selected.append(cfg)
    return selected


async def _list_tool_names(server: MCPServerStdio, tool_timeout: float) -> list[str]:
    tools = await asyncio.wait_for(server.list_tools(), timeout=tool_timeout)
    tool_list = tools.tools if hasattr(tools, "tools") else tools
    return [tool.name for tool in tool_list]


async def _run_filesystem_checks(
    server: MCPServerStdio,
    reports_dir: str,
    tool_timeout: float,
) -> None:
    allowed = await asyncio.wait_for(
        server.call_tool(
            tool_name="list_allowed_directories",
            arguments={},
        ),
        timeout=tool_timeout,
    )
    print("allowed:", allowed, flush=True)

    result = await asyncio.wait_for(
        server.call_tool(
            tool_name="list_directory",
            arguments={"path": reports_dir},
        ),
        timeout=tool_timeout,
    )
    print("list_directory:", result, flush=True)


async def _smoke_test_server(
    cfg,
    reports_dir: str,
    startup_timeout: float,
    tool_timeout: float,
) -> tuple[str, bool, str | None]:
    command_str = f"{cfg.command} {' '.join(cfg.args)}"
    print(f"\n=== {cfg.alias} ===", flush=True)
    print(f"command: {command_str}", flush=True)
    print(f"startup_timeout={startup_timeout}s tool_timeout={tool_timeout}s", flush=True)

    server = MCPServerStdio(
        params={
            "command": cfg.command,
            "args": cfg.args,
            **({"env": cfg.env} if getattr(cfg, "env", None) else {}),
        },
        client_session_timeout_seconds=max(
            cfg.timeout_seconds,
            int(startup_timeout + tool_timeout),
        ),
    )

    try:
        print(f"[{cfg.alias}] starting...", flush=True)
        await asyncio.wait_for(server.__aenter__(), timeout=startup_timeout)
        print(f"[{cfg.alias}] started", flush=True)

        tool_names = await _list_tool_names(server, tool_timeout)
        print("tools:", tool_names, flush=True)

        if cfg.alias == "filesystem":
            await _run_filesystem_checks(server, reports_dir, tool_timeout)

        print(f"[{cfg.alias}] smoke test passed", flush=True)
        return cfg.alias, True, None
    except TimeoutError:
        message = (
            f"Timed out while testing server '{cfg.alias}' after "
            f"{startup_timeout:.1f}s startup / {tool_timeout:.1f}s tool timeout. "
            f"Command: {command_str}. "
            "This usually means the MCP server process did not become ready in time. "
            "If this is an npx-based server, check package resolution, network access, "
            "and whether the command runs manually."
        )
        print(f"[{cfg.alias}] ERROR: {message}", flush=True)
        return cfg.alias, False, message
    except Exception as exc:
        message = (
            f"{type(exc).__name__}: {exc}. "
            f"Command: {command_str}"
        )
        print(f"[{cfg.alias}] ERROR: {message}", flush=True)
        return cfg.alias, False, message
    finally:
        try:
            await server.__aexit__(None, None, None)
            print(f"[{cfg.alias}] closed", flush=True)
        except Exception as exc:
            print(f"[{cfg.alias}] close warning: {type(exc).__name__}: {exc}", flush=True)


async def main() -> int:
    args = _build_parser().parse_args()

    reports_dir = os.getenv("REPORTS_DIR", os.path.join(os.getcwd(), "reports"))
    os.makedirs(reports_dir, exist_ok=True)

    include_aliases = _parse_csv(args.include)
    skip_aliases = _parse_csv(args.skip)

    configs = get_server_config(reports_dir)
    selected_configs = _select_configs(configs, include_aliases, skip_aliases)

    if not selected_configs:
        print("No servers selected. Adjust --include/--skip.", flush=True)
        return 1

    print("Selected servers:", ", ".join(cfg.alias for cfg in selected_configs), flush=True)

    results = []
    for cfg in selected_configs:
        result = await _smoke_test_server(
            cfg=cfg,
            reports_dir=reports_dir,
            startup_timeout=args.startup_timeout,
            tool_timeout=args.tool_timeout,
        )
        results.append(result)

    failures = [result for result in results if not result[1]]

    print("\n=== Summary ===", flush=True)
    for alias, ok, message in results:
        status = "PASS" if ok else "FAIL"
        suffix = "" if not message else f" - {message}"
        print(f"{status}: {alias}{suffix}", flush=True)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
