---
name: graphql-client
description: 'Best practices for consuming GraphQL APIs on the client using Apollo Client, including queries, mutations, subscriptions, fragments, caching, and error handling.'
---

# GraphQL Client Best Practices

Your goal is to help write clean, efficient GraphQL client code using Apollo Client and React hooks.

## Setup

Use **Apollo Client** with an in-memory cache and an HTTP link. Pass the client via `ApolloProvider` at the root of the component tree.

```tsx
import { ApolloClient, InMemoryCache, ApolloProvider, HttpLink } from '@apollo/client';

const client = new ApolloClient({
  link: new HttpLink({ uri: '/graphql' }),
  cache: new InMemoryCache(),
});

function App() {
  return (
    <ApolloProvider client={client}>
      <Router />
    </ApolloProvider>
  );
}
```

## Defining Operations

- Define queries, mutations, and subscriptions using the `gql` tagged template literal.
- Keep operation documents in **dedicated `.graphql` files** or in a `queries.ts` / `mutations.ts` file co-located with the feature.
- Give every operation an explicit, unique name in PascalCase — anonymous operations are harder to debug and cannot be tracked in monitoring tools.

```graphql
# operations/user.graphql
query GetUser($id: ID!) {
  user(id: $id) {
    id
    displayName
    email
  }
}

mutation UpdateUser($input: UpdateUserInput!) {
  updateUser(input: $input) {
    user {
      id
      displayName
    }
    errors {
      field
      message
    }
  }
}
```

## Queries with `useQuery`

```tsx
import { useQuery } from '@apollo/client';
import { GetUserDocument } from './__generated__/user.graphql';

function UserProfile({ userId }: { userId: string }) {
  const { data, loading, error } = useQuery(GetUserDocument, {
    variables: { id: userId },
  });

  if (loading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;

  return <div>{data.user.displayName}</div>;
}
```

- Use the `skip` option to conditionally skip a query: `skip: !userId`.
- Use `fetchPolicy` to control cache behaviour:
  - `cache-first` (default) — use cache if available, else network.
  - `network-only` — always fetch from network, write result to cache.
  - `cache-and-network` — show cached data immediately, then update with fresh data.
- Use `pollInterval` for lightweight polling; prefer subscriptions for real-time data.

## Mutations with `useMutation`

```tsx
import { useMutation } from '@apollo/client';
import { UpdateUserDocument } from './__generated__/user.graphql';

function EditUserForm({ userId }: { userId: string }) {
  const [updateUser, { loading, error }] = useMutation(UpdateUserDocument);

  async function handleSubmit(values: FormValues) {
    const { data } = await updateUser({
      variables: { input: { id: userId, ...values } },
    });

    if (data?.updateUser.errors.length) {
      // Handle user-level errors returned in the payload
    }
  }

  return <form onSubmit={...}> ... </form>;
}
```

- Handle both **application errors** (returned in the mutation payload) and **network/GraphQL errors** (thrown as an `ApolloError`).
- Use `onCompleted` and `onError` callbacks for side-effects like toasts or navigation.

## Fragment Colocation

- Define fragments alongside the component that uses the data, not at the query level.
- Compose queries from fragments at the route/page level.
- This ensures each component declares exactly what data it needs and avoids over-fetching.

```graphql
# UserCard.graphql
fragment UserCard_user on User {
  id
  displayName
  avatarUrl
}

# UserListPage.graphql
query GetUsers {
  users {
    edges {
      node {
        ...UserCard_user
      }
    }
  }
}
```

## Cache Management

- The `InMemoryCache` normalises objects by `__typename` + `id` by default. Ensure all queries include `id` (or the `keyFields` you configure) on every returned object type.
- Use `cache.modify()` to manually update the cache after a mutation when the mutation response alone is insufficient (e.g., removing an item from a list).
- Use `refetchQueries` for simple post-mutation refreshes:

```tsx
updateUser({
  variables: { input },
  refetchQueries: [{ query: GetUserDocument, variables: { id: userId } }],
});
```

- Avoid using `refetchQueries` excessively — prefer writing directly to the cache for performance-sensitive UIs.

## Optimistic Updates

Use `optimisticResponse` for mutations where the expected result is fully predictable, to make the UI feel instant:

```tsx
deletePost({
  variables: { id: postId },
  optimisticResponse: {
    deletePost: { __typename: 'DeletePostPayload', postId },
  },
  update(cache) {
    cache.evict({ id: cache.identify({ __typename: 'Post', id: postId }) });
    cache.gc();
  },
});
```

## Subscriptions

Use `useSubscription` for real-time data. Configure a `WebSocketLink` (or split link) in the client.

```tsx
import { useSubscription } from '@apollo/client';
import { MessageReceivedDocument } from './__generated__/messages.graphql';

function MessageFeed({ channelId }: { channelId: string }) {
  const { data } = useSubscription(MessageReceivedDocument, {
    variables: { channelId },
  });

  // data.messageReceived is the latest event
}
```

## Error Handling

- Wrap the Apollo link chain with an `onError` link to log unexpected errors globally.
- Distinguish between **network errors** (no response) and **GraphQL errors** (response with `errors` array).
- Do not surface raw error messages to end users — map to user-friendly messages at the UI layer.

```ts
import { onError } from '@apollo/client/link/error';

const errorLink = onError(({ graphQLErrors, networkError }) => {
  if (graphQLErrors) graphQLErrors.forEach(({ message }) => logger.error(message));
  if (networkError) logger.error('Network error', networkError);
});
```

## Code Generation

- Use **GraphQL Code Generator** (`@graphql-codegen/cli`) to generate fully-typed hooks and document nodes from `.graphql` files.
- Commit generated files or generate them as part of the build pipeline — never write typed query hooks by hand.
- Configure the `client` preset for Apollo Client v3+.
