# Constitution

## Core Principles

### I. Code Quality

All public functions, methods, and classes MUST have a docstring or Javadoc comment
explaining intent, not implementation. No magic numbers or strings — use named constants
or enums. Functions MUST do one thing; if a block inside a function needs a comment to
explain what it does, that block MUST be extracted into a named function or method.

Cyclomatic complexity MUST NOT exceed 10 per function/method, enforced via static analysis
in CI. Commented-out code MUST NOT appear in any commit; use feature flags or delete it.

**Java / Spring Boot**

- Follow standard Spring layering: Controller → Service → Repository. Business logic in
  controllers or repositories is FORBIDDEN.
- Use `record` types for immutable DTOs. Use `sealed interface` for discriminated domain
  types.
- Prefer constructor injection. Field injection via `@Autowired` is FORBIDDEN in
  non-test production code.
- Define domain-specific checked exceptions for recoverable errors. Unchecked exceptions
  are reserved for programming errors only.
- `Optional<T>` MUST be returned for nullable values. Returning `null` from any public
  method is FORBIDDEN.
- Java compilation MUST pass before merge (for example, `mvn -q -DskipTests compile` or
  `./gradlew compileJava` in the affected repo).

**Python / FastAPI**

- Follow PEP 8. `ruff` MUST be used for linting and formatting (line length 100).
- Pydantic v2 models MUST be used for all request/response schemas and internal data
  contracts.
- All FastAPI route handlers MUST be `async`. `httpx` MUST be used for async HTTP calls;
  the `requests` library is FORBIDDEN in service code.
- Every function signature MUST be fully type-annotated including return types. Bare
  `except:` clauses are FORBIDDEN; catch specific exception types only.
- Shared resources (DB sessions, HTTP clients, configuration) MUST be injected via
  FastAPI `Depends`.
- Python compilation checks MUST pass before merge (for example,
  `python -m compileall -q .` in the affected repo).

**REST API Contracts (all services)**

- All REST API contracts MUST be resource-based. Endpoint paths MUST use plural
  resource nouns (for example, `/users`, `/orders/{orderId}/items`) and MUST NOT
  use verb-style action paths (for example, `/createUser`, `/getOrders`,
  `/calculateScore`).
- CRUD semantics MUST map to standard HTTP methods (`GET`, `POST`, `PUT`, `PATCH`,
  `DELETE`) on resources. RPC-style action tunneling over REST paths is FORBIDDEN
  unless explicitly approved in the feature specification with documented rationale.
- Resource identifiers MUST be path parameters and filtering/pagination inputs MUST
  be query parameters. Request bodies for `GET` endpoints are FORBIDDEN.
- REST contract artifacts (OpenAPI specs, endpoint docs, and tests) MUST reflect the
  same resource model and naming conventions as implemented routes.

**LangGraph / AI Agents (sapphire-wellness-agent, sapphire-wellness-coach)**

- Graph state MUST be defined as a `TypedDict` with fully `Annotated` fields specifying
  the appropriate reducer (e.g., `operator.add` for append-only lists). Raw `dict` state
  is FORBIDDEN.
- Each graph node MUST be a single-responsibility `async` function accepting and
  returning state. Node functions MUST NOT perform DB or HTTP I/O without injected async
  clients (passed via `RunnableConfig` extras or constructor-injected dependencies).
- Conditional routing MUST use named routing functions returning string literals that
  match registered edge targets. Anonymous `lambda` routing callables are FORBIDDEN.
- All production LangGraph agents MUST use a persistent checkpointer
  (`AsyncPostgresSaver` or equivalent). `MemorySaver` is permitted in unit tests and
  local development only.
- Tool definitions MUST use Pydantic v2 `BaseModel` subclasses for their input schema.
  Bare `dict` or untyped `args_schema` is FORBIDDEN.
- Graphs MUST be compiled once at application startup and reused across requests.
  Compiling a new `StateGraph` per request is FORBIDDEN.
- Human-in-the-loop pauses MUST be implemented using LangGraph's `interrupt_before` or
  `interrupt_after` mechanism. Polling loops or arbitrary `asyncio.sleep` for approval
  waiting are FORBIDDEN.
- Node failures MUST be caught and encoded into a typed `error` field in the state.
  Unhandled exceptions that propagate out of a node and crash the graph are FORBIDDEN.
- LangGraph agent execution MUST emit trace data via LangSmith or an OTEL-compatible
  callback. Silent graph execution without observable trace output is FORBIDDEN in
  non-local environments.
- Unit tests MUST test each node in isolation with minimal constructed state dicts.
  Integration tests MUST run the compiled graph end-to-end using `MemorySaver` with
  deterministic LLM stubs or recorded cassettes.

**TypeScript / React (Sapphire UI)**

- Strict TypeScript MUST be enabled project-wide. `any` is FORBIDDEN. `ts-ignore`
  requires an explanatory comment and a linked ticket reference.
- Class components are FORBIDDEN; use functional components only.
- Feature code MUST be co-located: one directory per feature containing the component,
  its hook, its types, and its tests.
- Apollo cache policies MUST be explicit on every query. Implicit `cache-first` for
  mutable health data is FORBIDDEN.
- Raw `fetch` calls inside components are FORBIDDEN. All API interaction MUST go through
  the Apollo client or a typed service module.
- TypeScript compilation MUST pass before merge (for example, `tsc --noEmit` or the repo's equivalent compile script).

**Node.js / BFF (sapphire-bff-api)**

- All GraphQL resolvers MUST validate JWT claims before delegating to backend REST calls.
- Inline SQL and raw REST URLs are FORBIDDEN. Use typed resolver helpers and
  environment-configured service clients.
- `DataLoader` MUST be used for any field resolver that could trigger N+1 calls.


**Version**: 2.2.0 | **Ratified**: 2026-03-21 | **Last Amended**: 2026-04-02
