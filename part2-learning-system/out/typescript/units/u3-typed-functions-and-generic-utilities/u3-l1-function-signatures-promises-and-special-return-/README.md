# Function Signatures, Promises, and Special Return Types

*Typed Functions and Generic Utilities*

## By the end of this lesson you can

- Annotate function parameters, return values, and asynchronous Promise return types
- Specify function types using void, unknown, and never for callbacks, untyped inputs, and terminal error functions

## Where we are

Earlier lessons established how to define object shapes and request configurations using interfaces with optional and index properties. We also set up TypeScript's strict type-checking configuration and learned how to export ES modules for Node.js.

## The idea

Function parameter type annotations are written immediately following the parameter name to indicate the acceptable types of inputs ([source](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)). Function return type annotations are positioned directly after the function parameter list ([source](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)). When annotating the return type of a function that returns a promise, use the Promise type ([source](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)). An async function returning a number can be explicitly annotated with a return type of Promise<number> ([source](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)).

In a function type expression, parameter names are required; omitting a parameter name and writing only a type name makes the identifier become the parameter name typed as any ([source](https://www.typescriptlang.org/docs/handbook/2/functions.html)). The void type indicates the return type of functions that do not return a value, and it is automatically inferred when return statements return no explicit value or are absent ([source](https://www.typescriptlang.org/docs/handbook/2/functions.html)). A function defined literally with a void return type annotation is forbidden from returning any value ([source](https://www.typescriptlang.org/docs/handbook/2/functions.html)). A function that is contextually typed with a void return type is permitted to return a value, but that returned value is ignored ([source](https://www.typescriptlang.org/docs/handbook/2/functions.html)).

The unknown type can hold any value, but unlike any, TypeScript does not allow operations to be performed on unknown values without narrowing ([source](https://www.typescriptlang.org/docs/handbook/2/functions.html)). The never return type signifies that a function never finishes normally, such as when throwing an exception or terminating the program ([source](https://www.typescriptlang.org/docs/handbook/2/functions.html)).

## Worked example

Suppose we are building helper utilities for an API client module.

### Step 1: Create a terminal failure function
When an operation cannot proceed, we throw an error. Because this function never finishes normally, we annotate its return type with `never`:
```ts
function terminate(reason: string): never {
  throw new Error(reason);
}
```

### Step 2: Handle arbitrary inputs safely
When receiving data from an untrusted source, we annotate the parameter as `unknown`. TypeScript prevents calling methods directly on `unknown` without type narrowing:
```ts
function formatInput(data: unknown): string {
  if (typeof data === "string") {
    return data.trim();
  }
  return JSON.stringify(data);
}
```

### Step 3: Accept a callback that returns nothing
When specifying a callback function type, we must include the parameter name before its type. We use `void` to denote that the caller does not expect a return value:
```ts
function runTask(action: string, notify: (msg: string) => void): void {
  notify(`Starting: ${action}`);
}
```

### Step 4: Annotate an asynchronous operation
Async functions return promises. We annotate the return type with `Promise<number>` to explicitly declare the resolved value:
```ts
async function fetchCount(path: string): Promise<number> {
  if (!path.startsWith("/")) {
    terminate("Path must start with a slash");
  }
  return 42;
}
```

## Your turn

In client.ts, complete four functions for an API client library:
1. fail(message: string): Annotate its return type as never and throw an Error with the given message.
2. parsePayload(raw: unknown): Annotate the raw parameter as unknown and return type as string. If raw is a string, return it; otherwise return JSON.stringify(raw).
3. logResponse(message: string, logger: (msg: string) => void): Annotate logger as a function taking msg: string and returning void, with logResponse returning void. In the body, call logger(message).
4. fetchStatus(endpoint: string): Annotate the return type as Promise<number>. If endpoint does not start with '/', call fail('Invalid endpoint'); otherwise return 200.

The tests run with Node's built-in test runner, so you'll need [Node.js](https://nodejs.org/en/download) 20 or newer, or 22.6 or newer for TypeScript. TypeScript is also type-checked with the TypeScript compiler, which `check` fetches once with npm.

Your files are in `exercise/`. When you think it works:

```bash
learn check
```

Stuck? `learn hint` gives one hint at a time. `learn solution` shows the answer, and records that you looked.

## Check yourself

3 questions. Answer them before you see the answers:

```bash
learn quiz
```
