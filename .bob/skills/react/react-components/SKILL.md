---
name: react-components
description: 'Best practices for building React functional components, hooks, JSX, state, context, and performance patterns.'
---

# React Components Best Practices

Your goal is to help write high-quality, idiomatic React functional components following modern React conventions.

## Core Principles

- Prefer **functional components** with hooks — avoid class components in new code.
- Keep components **small and focused**: one responsibility per component.
- Co-locate state as close to where it is used as possible; lift state only when two or more siblings need it.
- Derive values from existing state/props rather than storing redundant copies in state.
- Components should be pure with respect to their inputs.

## Component Structure

- One component per file. Name the file to match the exported component (`UserCard.tsx`).
- Export components as **named exports**, not default exports, to improve refactoring and IDE support.
- Declare props with a TypeScript `interface` directly above the component.

```tsx
interface UserCardProps {
  name: string;
  avatarUrl: string;
  onSelect: (id: string) => void;
}

export function UserCard({ name, avatarUrl, onSelect }: UserCardProps) {
  return (
    <div onClick={() => onSelect(name)}>
      <img src={avatarUrl} alt={name} />
      <span>{name}</span>
    </div>
  );
}
```

## TypeScript Conventions

- Always type component props explicitly with an `interface` or `type`.
- Avoid `React.FC` — prefer plain function declarations with typed props; `React.FC` disallows returning `undefined` and adds an implicit `children` prop.
- Use `React.ReactNode` for `children` props.
- Use `React.ComponentProps<'button'>` to extend native element props cleanly.

## State Management

- Use `useState` for simple, independent pieces of local state.
- Use `useReducer` when state has multiple sub-values or when the next state depends on complex logic involving the previous state.
- Never mutate state directly — always return new objects/arrays.

```tsx
// Correct — return new array
setItems(prev => [...prev, newItem]);

// Incorrect — mutates state
items.push(newItem);
setState(items);
```

## Side Effects

- Use `useEffect` for side effects: data fetching setup, subscriptions, manual DOM mutations.
- **Always specify a dependency array.** An empty array (`[]`) means run once on mount; omitting the array means run after every render.
- Clean up subscriptions and timers by returning a cleanup function from `useEffect`.
- Prefer abstracting data fetching into a custom hook or a data-fetching library (React Query, SWR) over raw `useEffect` fetch calls.

```tsx
useEffect(() => {
  const controller = new AbortController();
  fetchData(controller.signal).then(setData);
  return () => controller.abort();
}, [id]);
```

## Common Hooks Reference

| Hook | Use for |
|---|---|
| `useState` | Local UI state |
| `useEffect` | Side effects, subscriptions, data fetching |
| `useRef` | DOM access or storing a mutable value without triggering a re-render |
| `useMemo` | Expensive derived computations — memoises the result |
| `useCallback` | Stable function references to pass to memoised child components |
| `useContext` | Consuming a React context value |
| `useReducer` | Complex state with multiple transitions |
| `useId` | Generating stable unique IDs for accessibility attributes |

## Custom Hooks

- Extract repeated stateful or side-effect logic into `useSomething()` hooks.
- A custom hook must call at least one built-in hook.
- Custom hooks can return any shape: a value, a tuple, or an object.

```tsx
function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}
```

## Performance

- Do **not** optimise prematurely — profile first with React DevTools Profiler.
- Wrap with `React.memo()` only when a component demonstrably re-renders unnecessarily due to stable-but-equal props.
- Use `useMemo` for expensive computations (e.g., filtering/sorting large lists).
- Use `useCallback` when passing a callback as a prop to a `React.memo`-wrapped child.
- Avoid creating object or array literals inline in JSX — they produce new references on every render.

```tsx
// Avoid
<Chart config={{ color: 'red' }} />

// Prefer — stable reference
const chartConfig = useMemo(() => ({ color: 'red' }), []);
<Chart config={chartConfig} />
```

## Context

- Use React Context for genuinely global or cross-cutting state: theme, authenticated user, locale.
- Do **not** use Context as a general-purpose state manager; prefer component props for local concerns.
- Split contexts by concern — a single mega-context forces unrelated consumers to re-render together.
- Always expose context through a custom hook that throws a helpful error if used outside its provider:

```tsx
const ThemeContext = React.createContext<Theme | null>(null);

export function useTheme(): Theme {
  const ctx = React.useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}
```

## Composition Patterns

- Prefer **composition** (passing components as props or children) over runtime configuration props like `variant="large"` for structural differences.
- Use the **Compound Component** pattern for related components that share implicit state (e.g., `<Tabs>`, `<Tab>`, `<TabPanel>`).
- Use **render props** or **slot props** (`renderHeader`, `renderFooter`) when consumers need to customise a region of a component.
