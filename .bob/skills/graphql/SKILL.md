---
name: graphql
description: 'Entry point for GraphQL skills. Routes to the appropriate subskill based on the task.'
---

# GraphQL Skills — Router

This is the parent skill for GraphQL development. It does **not** contain guidance directly. Instead, identify which subskill applies to the task and load that file with `read_file` before proceeding.

## Subskills

| Subskill | File | When to load |
|---|---|---|
| **graphql-schema** | `graphql/graphql-schema/SKILL.md` | Designing or reviewing a GraphQL schema; SDL type definitions, queries, mutations, subscriptions, interfaces, unions, custom scalars, directives, resolver structure, pagination, error handling patterns |
| **graphql-client** | `graphql/graphql-client/SKILL.md` | Consuming a GraphQL API on the client; Apollo Client, urql, writing queries/mutations/subscriptions, fragment colocation, cache management, `useQuery`/`useMutation` hooks, optimistic updates, error handling |

## Progressive Disclosure Instructions

1. **Read the user's request** and determine which subskill(s) apply from the table above.
2. **Load only the relevant subskill(s)** using `read_file` on the corresponding `SKILL.md` path before generating any response or code.
3. If a task spans multiple subskills (e.g., designing a schema *and* writing client queries for it), load **all** applicable subskill files before proceeding.
4. Do **not** guess or generate GraphQL guidance from this file alone — always load the subskill first.

## Using Context7 for Up-to-Date Library Documentation

Context7 resolves library documentation from the web at query time. Use it to avoid generating stale or hallucinated API details.

### When to use Context7

| Situation | Action |
|---|---|
| User specifies a **library version** (e.g., Apollo Client 3.11, Apollo Server 4, GraphQL.js 16) | Fetch docs for that exact version |
| User asks about a **specific directive, cache policy, or client API** whose behaviour may have changed across versions | Fetch the current reference |
| Generated code uses an API you are **not fully confident** is accurate for the stated version | Verify before returning |
| User asks "what's new" or "how do I migrate" for a GraphQL library | Fetch the release notes / migration guide |

### When NOT to use Context7

- Core GraphQL specification concepts (type system, fields, resolvers, introspection, execution model) — these are stable and version-independent.
- Tasks that are purely structural (schema file organisation, naming conventions) with no specific library API surface.

### How to use Context7

1. **Load the tool** — call `tool_search_tool_regex` with pattern `context7` to discover the available Context7 tools before using them.
2. **Resolve the library ID** — use `resolve-library-id` with the library name (e.g., `"apollo-client"`, `"apollo-server"`, `"graphql-js"`, `"urql"`).
3. **Fetch the docs** — use `get-library-docs` with the resolved ID and a focused `topic` (e.g., `"InMemoryCache"`, `"@deprecated"`, `"subscription resolvers"`, `"dataSources"`).
4. **Apply the result** — use the returned documentation to ground generated code and examples. Prefer it over training-time knowledge when there is any conflict.
