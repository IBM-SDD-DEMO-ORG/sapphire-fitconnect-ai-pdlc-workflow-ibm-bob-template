---
name: graphql-schema
description: 'Best practices for designing GraphQL schemas using SDL, including types, queries, mutations, subscriptions, resolvers, and pagination.'
---

# GraphQL Schema Best Practices

Your goal is to help design clear, maintainable, and evolvable GraphQL schemas following established conventions.

## Core Design Principles

- Design the schema around the **client's data needs**, not the shape of the underlying data sources.
- Prefer **nullable fields by default**; mark a field non-null (`!`) only when the server guarantees a value will always be present.
- Design for **evolvability**: avoid breaking changes. Add fields rather than removing or renaming them; use `@deprecated` to phase out old fields.
- Expose domain concepts, not database rows — the schema is a product interface.

## Type System

### Scalars
Use the built-in scalars (`String`, `Int`, `Float`, `Boolean`, `ID`) and define custom scalars for types with special validation or serialisation needs (e.g., `DateTime`, `URL`, `EmailAddress`).

```graphql
scalar DateTime
scalar EmailAddress
```

### Object Types
```graphql
type User {
  id: ID!
  email: EmailAddress!
  displayName: String!
  createdAt: DateTime!
  posts: [Post!]!
}
```

### Interfaces and Unions
- Use **interfaces** when multiple types share a common set of fields and consumers always need those fields.
- Use **unions** when multiple types can appear in a position but share no common fields.

```graphql
interface Node {
  id: ID!
}

union SearchResult = User | Post | Comment
```

### Enums
Use enums for fields with a fixed, known set of values:

```graphql
enum UserRole {
  ADMIN
  EDITOR
  VIEWER
}
```

## Queries, Mutations, and Subscriptions

### Queries
- Name queries after what they return, using camelCase: `user`, `usersByRole`, `post`.
- Accept ID arguments as `ID!` for single-resource lookups.
- Return `null` for a not-found single resource rather than throwing an error.

```graphql
type Query {
  user(id: ID!): User
  users(role: UserRole, first: Int, after: String): UserConnection!
}
```

### Mutations
- Use the **input object pattern** — wrap all mutation arguments in a single `input` type.
- Return a **payload object** (not just the mutated entity) so errors and metadata can be added later without breaking changes.

```graphql
type Mutation {
  createUser(input: CreateUserInput!): CreateUserPayload!
  deleteUser(input: DeleteUserInput!): DeleteUserPayload!
}

input CreateUserInput {
  email: String!
  displayName: String!
  role: UserRole!
}

type CreateUserPayload {
  user: User
  errors: [UserError!]!
}
```

### Subscriptions
- Use subscriptions only for data that clients genuinely need in real time.
- Name subscriptions with a past-tense verb to indicate an event: `userCreated`, `messageReceived`.

```graphql
type Subscription {
  messageReceived(channelId: ID!): Message!
}
```

## Naming Conventions

| Concept | Convention | Example |
|---|---|---|
| Types | PascalCase | `UserProfile` |
| Fields | camelCase | `displayName` |
| Enum values | SCREAMING_SNAKE_CASE | `PENDING_REVIEW` |
| Mutations | verb + noun | `createUser`, `updatePost` |
| Input types | Operation + `Input` suffix | `CreateUserInput` |
| Payload types | Operation + `Payload` suffix | `CreateUserPayload` |

## Pagination

Use **cursor-based (Relay-style) connections** for any list that could grow large. Avoid offset pagination for production APIs.

```graphql
type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
}

type UserEdge {
  node: User!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}
```

## Error Handling

- Distinguish between **user errors** (invalid input, business rule violations) and **unexpected errors** (system failures).
- Return user errors as data in the mutation payload — do **not** throw GraphQL errors for expected validation failures.
- Use GraphQL errors (`errors` array in the response) only for unexpected, system-level failures.

```graphql
type UserError {
  field: String        # Which field caused the error, if applicable
  message: String!
}
```

## Resolvers

- Keep resolvers **thin**: delegate business logic to a service layer; resolvers should only transform and forward.
- Use **DataLoaders** to batch and deduplicate database lookups within a single request, preventing the N+1 query problem.
- Never access the database directly in a resolver — go through a repository or data-source layer.
- Type the `context` argument — never use `any`.

```ts
// Example resolver (TypeScript, Apollo Server)
const resolvers = {
  Query: {
    user: (_parent, { id }, context: AppContext) =>
      context.dataSources.userService.findById(id),
  },
  User: {
    posts: (parent: User, _args, context: AppContext) =>
      context.loaders.postsByUserId.load(parent.id),
  },
};
```

## Schema Organisation

- Split large schemas across multiple `.graphql` files by domain and merge them at startup.
- Keep input types, payload types, and enum definitions in the same file as the operation they support.
- Co-locate resolver implementations with their type definitions in the same feature module.
