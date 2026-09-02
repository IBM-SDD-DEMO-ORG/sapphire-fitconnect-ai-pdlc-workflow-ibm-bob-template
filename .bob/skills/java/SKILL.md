---
name: java
description: 'Entry point for Java skills. Routes to the appropriate subskill based on the task.'
---

# Java Skills — Router

This is the parent skill for Java development. It does **not** contain guidance directly. Instead, identify which subskill applies to the task and load that file with `read_file` before proceeding.

## Subskills

| Subskill | File | When to load |
|---|---|---|
| **java-junit** | `java/java-junit/SKILL.md` | Writing, reviewing, or debugging JUnit 5 unit tests; parameterized/data-driven tests; test structure, assertions, mocking with Mockito |
| **java-springboot** | `java/java-springboot/SKILL.md` | Building or reviewing Spring Boot applications; REST controllers, services, repositories, configuration, security, logging, testing slices |

## Progressive Disclosure Instructions

1. **Read the user's request** and determine which subskill(s) apply from the table above.
2. **Load only the relevant subskill(s)** using `read_file` on the corresponding `SKILL.md` path before generating any response or code.
3. If a task spans multiple subskills (e.g., writing a Spring Boot service *and* its JUnit tests), load **all** applicable subskill files before proceeding.
4. Do **not** guess or generate Java guidance from this file alone — always load the subskill first.

## Using Context7 for Up-to-Date Library Documentation

Context7 resolves library documentation from the web at query time. Use it to avoid generating stale or hallucinated API details.

### When to use Context7

| Situation | Action |
|---|---|
| User specifies a **library version** (e.g., Spring Boot 3.4, JUnit 5.11) | Fetch docs for that exact version |
| User asks about a **specific API, annotation, or configuration property** whose signature may have changed across versions | Fetch the current reference |
| Generated code uses an API you are **not fully confident** is accurate for the stated version | Verify before returning |
| User asks "what's new" or "how do I migrate" for a Java library | Fetch the release notes / migration guide |

### When NOT to use Context7

- Stable, widely known Java SE core APIs (e.g., `java.util.List`, `java.io.File`) — these rarely change.
- Tasks that are purely structural (project layout, naming conventions) with no specific library API surface.

### How to use Context7

1. **Load the tool** — call `tool_search_tool_regex` with pattern `context7` to discover the available Context7 tools before using them.
2. **Resolve the library ID** — use `resolve-library-id` with the library name (e.g., `"spring-boot"`, `"junit5"`, `"mockito"`).
3. **Fetch the docs** — use `get-library-docs` with the resolved ID and a focused `topic` (e.g., `"@MockBean"`, `"@ParameterizedTest"`, `"spring.datasource configuration"`).
4. **Apply the result** — use the returned documentation to ground generated code and examples. Prefer it over training-time knowledge when there is any conflict.
