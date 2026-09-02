---
name: react-testing
description: 'Best practices for testing React components with React Testing Library, user-event, Jest, and MSW.'
---

# React Testing Best Practices

Your goal is to help write effective, maintainable React component tests that verify user-visible behaviour.

## Core Philosophy

- **Test behaviour, not implementation** — interact with the rendered output the way a real user would.
- Tests should not break when internal implementation details change (state variable names, internal component structure), only when observable behaviour changes.
- Avoid asserting on component internals: do not access instance state, call component methods, or spy on internal functions.

## Setup and Dependencies

- Use **React Testing Library** (`@testing-library/react`) as the rendering and query layer.
- Use **`@testing-library/user-event`** (v14+) for simulating user interactions — prefer it over `fireEvent` for all interactions a real user could perform.
- Use **Jest** as the test runner and assertion library.
- Optionally use `@testing-library/jest-dom` for expressive DOM matchers (`toBeVisible`, `toHaveTextContent`, etc.).

```shell
npm install --save-dev @testing-library/react @testing-library/user-event @testing-library/jest-dom jest jest-environment-jsdom
```

## Query Priority

Use queries in this order of preference (most to least semantic):

| Priority | Query | Use for |
|---|---|---|
| 1 | `getByRole` | Buttons, headings, inputs, links, checkboxes, comboboxes, etc. |
| 2 | `getByLabelText` | Form fields associated with a `<label>` |
| 3 | `getByPlaceholderText` | Inputs with a placeholder (only if no label exists) |
| 4 | `getByText` | Non-interactive text content |
| 5 | `getByDisplayValue` | Current value of form inputs |
| 6 | `getByAltText` | Images |
| 7 | `getByTitle` | Elements with a `title` attribute |
| 8 | `getByTestId` | **Last resort only** — adds coupling to implementation |

Always prefer queries that reflect what a screen-reader user would perceive.

## Basic Test Structure

```tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginForm } from './LoginForm';

describe('LoginForm', () => {
  it('calls onSubmit with email and password when form is submitted', async () => {
    const user = userEvent.setup();
    const handleSubmit = jest.fn();

    render(<LoginForm onSubmit={handleSubmit} />);

    await user.type(screen.getByLabelText(/email/i), 'user@example.com');
    await user.type(screen.getByLabelText(/password/i), 'secret');
    await user.click(screen.getByRole('button', { name: /log in/i }));

    expect(handleSubmit).toHaveBeenCalledWith({
      email: 'user@example.com',
      password: 'secret',
    });
  });
});
```

## User Interactions

- Always call `userEvent.setup()` at the top of each test for correct event sequencing.
- `await` every `userEvent` call — all methods are async.
- Use `userEvent.type()` to simulate real keystroke-by-keystroke input.
- Use `userEvent.click()`, `userEvent.selectOptions()`, `userEvent.upload()` for their respective interactions.
- Reserve `fireEvent` for cases where `userEvent` is insufficient (e.g., custom synthetic events, drag-and-drop).

## Async Rendering

- Use `findBy*` (returns a Promise) when querying for elements that appear after an async operation.
- Use `waitFor` when asserting on something that changes after an async side-effect.
- Always `await` async queries — omitting `await` creates false-positive tests.
- Wrap async state updates in `act()` only when React Testing Library does not do so automatically (rare).

```tsx
it('displays fetched users', async () => {
  render(<UserList />);

  // Wait for loading to finish
  const items = await screen.findAllByRole('listitem');
  expect(items).toHaveLength(3);
});

it('shows an error message on failure', async () => {
  render(<UserList />);

  await waitFor(() => {
    expect(screen.getByRole('alert')).toHaveTextContent(/failed to load/i);
  });
});
```

## Mocking

### Module mocking
```tsx
jest.mock('../api/users', () => ({
  fetchUsers: jest.fn().mockResolvedValue([{ id: '1', name: 'Alice' }]),
}));
```

### HTTP request mocking with MSW
Prefer **Mock Service Worker (MSW)** for integration-level tests that involve real `fetch`/`axios` calls.

```tsx
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  http.get('/api/users', () => HttpResponse.json([{ id: '1', name: 'Alice' }])),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### Mocking hooks
Mock the module that exports the hook, not the hook's internals:

```tsx
jest.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ user: { name: 'Alice' }, isAuthenticated: true }),
}));
```

## Wrapping with Context Providers

Create a shared `renderWithProviders` utility for components that depend on context:

```tsx
// test-utils.tsx
import { render, RenderOptions } from '@testing-library/react';

function AllProviders({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider theme={defaultTheme}>
      <QueryClientProvider client={new QueryClient()}>
        {children}
      </QueryClientProvider>
    </ThemeProvider>
  );
}

export function renderWithProviders(ui: React.ReactElement, options?: RenderOptions) {
  return render(ui, { wrapper: AllProviders, ...options });
}
```

Re-export from `@testing-library/react` so tests import from one place.

## Snapshot Testing

- Use snapshot tests only for stable, purely presentational components with no interactive behaviour.
- Prefer `toMatchInlineSnapshot()` over `toMatchSnapshot()` — inline snapshots are visible in the test file and easier to review.
- Regenerate snapshots deliberately (`--updateSnapshot`) — never auto-update them without reviewing the diff.
- Do **not** snapshot large component trees; they become brittle and hide meaningful regressions.

## Test Organisation

- Place test files adjacent to the component: `UserCard.test.tsx` alongside `UserCard.tsx`.
- Alternatively, use a `__tests__/` folder within the feature directory.
- Group related tests inside a `describe` block named after the component.
- One assertion focus per `it` block; avoid testing multiple unrelated behaviours in one test.
- Keep setup (`beforeEach`) minimal — favour explicit, readable setup within each test.
