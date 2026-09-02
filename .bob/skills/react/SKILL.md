---
name: react
description: 'Entry point for React skills. Routes to the appropriate subskill based on the task.'
---

# React Skills — Router

This is the parent skill for React development. It does **not** contain guidance directly. Instead, identify which subskill applies to the task and load that file with `read_file` before proceeding.

## Subskills

| Subskill | File | When to load |
|---|---|---|
| **react-components** | `react/react-components/SKILL.md` | Building, reviewing, or refactoring React functional components; JSX, props, state, context, custom hooks, composition patterns, performance optimisation (memo, useMemo, useCallback) |
| **react-testing** | `react/react-testing/SKILL.md` | Writing, reviewing, or debugging React component tests; React Testing Library, user-event, snapshot tests, mocking hooks or modules, async rendering |

## Progressive Disclosure Instructions

1. **Read the user's request** and determine which subskill(s) apply from the table above.
2. **Load only the relevant subskill(s)** using `read_file` on the corresponding `SKILL.md` path before generating any response or code.
3. If a task spans multiple subskills (e.g., building a component *and* writing its tests), load **all** applicable subskill files before proceeding.
4. Do **not** guess or generate React guidance from this file alone — always load the subskill first.

## Using Context7 for Up-to-Date Library Documentation

Context7 resolves library documentation from the web at query time. Use it to avoid generating stale or hallucinated API details.

### When to use Context7

| Situation | Action |
|---|---|
| User specifies a **React or ecosystem library version** (e.g., React 19, React Router v7, Next.js 15) | Fetch docs for that exact version |
| User asks about a **specific hook, API, or component** whose signature may have changed across versions | Fetch the current reference |
| Generated code uses an API you are **not fully confident** is accurate for the stated version | Verify before returning |
| User asks "what's new" or "how do I migrate" for React or a React ecosystem library | Fetch the release notes / migration guide |

### When NOT to use Context7

- Stable, well-known React APIs that have not changed across recent major versions (e.g., basic `useState`, `useEffect` usage).
- Tasks that are purely structural (component folder layout, naming conventions) with no specific library API surface.

### How to use Context7

1. **Load the tool** — call `tool_search_tool_regex` with pattern `context7` to discover the available Context7 tools before using them.
2. **Resolve the library ID** — use `resolve-library-id` with the library name (e.g., `"react"`, `"react-router"`, `"testing-library"`).
3. **Fetch the docs** — use `get-library-docs` with the resolved ID and a focused `topic` (e.g., `"useTransition"`, `"Suspense"`, `"screen queries"`, `"Server Components"`).
4. **Apply the result** — use the returned documentation to ground generated code and examples. Prefer it over training-time knowledge when there is any conflict.
