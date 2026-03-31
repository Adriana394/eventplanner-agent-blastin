# MCP Runtime and Integration Plan

## Scope

This document defines the recommended technical approach for operating MCP servers in this project across three stages:

- local development
- agent integration
- later multi-user or production-oriented deployment

The document focuses on runtime behavior, transport choices, validation strategy, and migration constraints.

## System Context

The current architecture includes:

- Python-based MCP servers for domain-specific tooling
- external MCP dependencies started through command-based runtimes
- agent flows that depend on MCP server startup and tool availability
- a UI layer that ultimately depends on successful MCP-backed planner execution

The immediate requirement is to make local testing deterministic enough for engineering validation. The later requirement is to support a runtime model that remains operable under broader usage conditions.

## Current Technical Position

### Runtime Model

Python-based MCP servers should be started from the project runtime rather than from the system interpreter.

Current target pattern:

```bash
uv run python -m mcp_servers.event_server
uv run python -m mcp_servers.dzt_server
```

Technical reasons:

- dependency resolution is aligned with the project environment
- local execution does not depend on manual virtual environment activation
- child processes started by the application can use the same dependency graph as the main process

### Configuration Boundary

MCP startup configuration should remain centralized.

The server configuration layer should define:

- command
- arguments
- environment variables
- working directory
- timeout policy

In this codebase, that responsibility belongs in:

- `mcp_servers/mcp_servers.py`

This allows transport and runtime behavior to be changed without refactoring agent logic.

### Environment Propagation

Child processes must not depend on implicit shell state.

Environment variables should be passed explicitly per server where needed. Relevant examples include:

- `UV_CACHE_DIR`
- `EVENT_URL`
- `CITY_URL`
- `DZT_URL`
- `DZT_API_KEY`

This is required for reproducibility, especially when startup is initiated indirectly by agents or test tooling.

## Development Transport Strategy

### Development Mode

`stdio` remains acceptable as a development-only transport if it is sufficient to validate:

- tool registration
- agent tool usage
- planner flow wiring
- UI integration paths

At this stage, `stdio` should be treated as a local engineering mode, not as the final runtime architecture.

### Constraints of `stdio`

`stdio` is sensitive to:

- child process startup behavior
- interpreter selection
- working directory mismatches
- environment propagation
- handshake timing
- unintended stdout output

In practice, it is usually easiest to operate in:

- local single-user development
- isolated smoke tests
- tightly coupled tooling experiments

It is generally weaker for:

- shared environments
- long-running processes
- process supervision
- multi-user access patterns
- production-style observability

### Engineering Decision

The recommended short-term position is:

- keep `stdio` available for local development and early validation
- do not treat `stdio` as the final transport assumption
- preserve a clean path to a network transport later

## Validation Strategy

### Smoke Test Objectives

The smoke test should answer the following questions:

- can the server process be started
- does MCP initialization succeed
- does `list_tools()` succeed
- do minimal baseline calls succeed where applicable

The smoke test is not intended to validate business correctness. Its purpose is runtime and reachability validation.

Recommended execution patterns:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run -m mcp_servers.test_mcp_connectivity
UV_CACHE_DIR=/tmp/uv-cache uv run -m mcp_servers.test_mcp_connectivity --include eventim,dzt
UV_CACHE_DIR=/tmp/uv-cache uv run -m mcp_servers.test_mcp_connectivity --skip playwright
```

### Required Failure Visibility

Smoke-test output should make the following visible:

- which server is being started
- the exact startup command
- timeout boundaries
- whether failure occurred during process startup, MCP initialization, or tool invocation

This is necessary because agent failures frequently mask underlying infrastructure issues.

## Agent Integration Requirements

### Integration Boundary

Agent code should not own MCP startup semantics directly.

Agent logic should consume MCP servers through a stable configuration abstraction. That abstraction should be the only place where the following decisions are made:

- `stdio` versus network transport
- local runtime versus external service
- timeout policy
- environment injection

This keeps agent orchestration decoupled from runtime-specific process details.

### Health Preconditions

Before using MCP-backed flows in meaningful agent paths, the following preconditions should be verified:

- process startup completes
- MCP initialization completes
- tool enumeration succeeds
- critical tool calls succeed at least once in a controlled test path

Without these checks, agent output failures are difficult to classify accurately.

### Error Model

Errors should be categorized at least into the following classes:

- startup failure
- dependency or interpreter failure
- MCP initialization failure
- tool execution failure
- network failure
- credential or configuration failure

This classification should be preserved in logs and in developer-facing diagnostics.

## Runtime Evolution Path

### Stage 1: Local Engineering Mode

Target characteristics:

- child-process startup
- project-managed Python runtime
- `stdio` allowed
- explicit env propagation
- smoke-test driven validation

This stage is intended to support engineering productivity and rapid iteration.

### Stage 2: Integration-Ready Runtime

Target characteristics:

- stable startup contracts
- clearer health checks
- explicit runtime configuration
- reduced dependence on transient tooling such as `npx @latest`
- transport kept configurable

At this stage, the system should be reliable enough for repeated team validation and agent behavior testing.

### Stage 3: Multi-User or Production-Oriented Runtime

For broader usage scenarios, a network-based transport should be evaluated explicitly.

Candidate directions:

- SSE
- `streamable-http`
- separately deployed MCP services

Reasons:

- better lifecycle separation
- better monitoring
- improved restart behavior
- more natural fit for shared or concurrent usage

## Deployment Model Options

### Embedded Child Processes

Advantages:

- minimal infrastructure
- low friction for local development
- straightforward coupling during early prototyping

Limitations:

- weaker process supervision
- tighter coupling between application and server lifecycle
- poorer fit for concurrent or shared usage

### Separate Service Runtime

Advantages:

- clearer operational boundaries
- stronger observability
- better restart and supervision characteristics
- better fit for network-based MCP transports

Limitations:

- increased deployment complexity
- additional infrastructure requirements

### Recommended Direction

A hybrid model is the most practical technical path:

- local development continues to use embedded startup where useful
- later shared environments move toward separately running services or a network transport

This preserves development speed without locking the system into an unsuitable long-term runtime.

## Dependency and Version Policy

Commands that depend on floating external versions should not be treated as stable runtime dependencies.

Example:

```bash
npx @playwright/mcp@latest
```

Recommended progression:

- pin versions where possible
- prefer predictable runtime paths over on-demand resolution
- move critical services away from `@latest`-style startup patterns

## Operational Recommendations

The following practices should be adopted before broader rollout:

- explicit server-specific environment validation at startup
- centralized timeout policy
- logging of runtime command, transport, and initialization outcome
- stable smoke-test coverage for critical servers
- transport kept configurable rather than embedded into business logic

## Implementation Sequence

1. stabilize Python MCP startup through the project runtime
2. preserve `stdio` only as a local engineering transport
3. pass environment variables explicitly per server
4. use smoke tests as the baseline runtime validation mechanism
5. validate agent flows only after MCP startup behavior is stable
6. reassess the transport model before multi-user or inference-oriented usage
7. introduce a network-capable or separately deployed runtime model where needed

## Summary

The immediate technical objective is not final deployment architecture. The immediate objective is to make MCP-backed development and testing reliable enough for engineering work.

The longer-term objective is to evolve toward a runtime model with:

- explicit startup behavior
- stable tool contracts
- clear separation of configuration and orchestration
- a transport suitable for broader operational use
