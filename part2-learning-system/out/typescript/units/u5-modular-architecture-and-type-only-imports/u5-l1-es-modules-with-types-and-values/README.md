# ES Modules with Types and Values

*Modular Architecture and Type-Only Imports*

## By the end of this lesson you can

- Export and import functions, objects, and type definitions using standard ES Module syntax
- Organize module public APIs using named exports, default exports, and wildcard re-exports

## Where we are

In previous lessons, we created domain interfaces such as User and Post alongside custom type guards like isUser and isPost to safely validate unknown data at runtime. We also defined generic discriminated union types like ApiResponse to represent asynchronous loading, success, and error states. Now we will organize these types, guards, and utilities into reusable modules using ECMAScript Module syntax.

## The idea

ECMAScript Modules (ESM) are built into JavaScript and provide dedicated import and export syntax to share code across files ([source](https://www.typescriptlang.org/docs/handbook/modules/theory.html)). In TypeScript, any file with a top-level import or export declaration is treated as a module ([source](https://www.typescriptlang.org/docs/handbook/2/modules.html)).

Variables, functions, and classes can be exported individually without the default keyword and imported using curly braces ([source](https://www.typescriptlang.org/docs/handbook/2/modules.html)). Specific named bindings can be imported from an ES Module using curly braces enclosing the binding name ([source](https://www.typescriptlang.org/docs/handbook/modules/theory.html)). TypeScript types and interfaces can be exported and imported using the standard ES Module syntax used for values ([source](https://www.typescriptlang.org/docs/handbook/2/modules.html)). Type aliases, interfaces, enums, and namespaces can be exported using an export modifier or referenced alongside JavaScript declarations in named export lists ([source](https://www.typescriptlang.org/docs/handbook/modules/reference.html)). Exported types and other TypeScript declarations can be imported using standard ECMAScript import syntax ([source](https://www.typescriptlang.org/docs/handbook/modules/reference.html)).

Imported identifiers can be renamed using the `as` keyword ([source](https://www.typescriptlang.org/docs/handbook/2/modules.html)). All exports from a module can be imported into a single namespace object using the `* as` syntax ([source](https://www.typescriptlang.org/docs/handbook/2/modules.html)). When using namespace imports or exports, exported types can be accessed on the namespace when used in a type position ([source](https://www.typescriptlang.org/docs/handbook/modules/reference.html)).

A file can specify its primary export using the `export default` syntax ([source](https://www.typescriptlang.org/docs/handbook/2/modules.html)). In ES Module syntax, a module can define a default export using the `export default` keywords ([source](https://www.typescriptlang.org/docs/handbook/modules/theory.html)). Default and named imports can be combined in a single import statement ([source](https://www.typescriptlang.org/docs/handbook/2/modules.html)). Furthermore, a module can re-export all exports from another module using the `export * from` syntax ([source](https://www.typescriptlang.org/docs/handbook/modules/theory.html)).

## Worked example

Suppose we want to structure a module hierarchy for a web app domain with models, a utility service, and a central barrel entry point.

### Step 1: Export types and values using named exports
In `models.ts`, we export interfaces and helper functions with the `export` keyword:
```ts
export interface Account {
  id: string;
  balance: number;
}

export function formatBalance(account: Account): string {
  return `$${account.balance.toFixed(2)}`;
}
```

### Step 2: Combine imports and provide a default export
In `accountService.ts`, we import the interface and helper from `models.ts`. We then define and export a primary function with `export default`:
```ts
import type { Account } from "./models.ts";
import { formatBalance } from "./models.ts";

export interface AccountSummary {
  id: string;
  summary: string;
}

export default function summarizeAccount(account: Account): AccountSummary {
  return {
    id: account.id,
    summary: formatBalance(account),
  };
}
```

### Step 3: Organize a public API using a barrel file
In `index.ts`, we re-export all named exports from the submodules using wildcard re-exports (`export * from ...`) and forward the default export:
```ts
export * from "./models.ts";
export * from "./accountService.ts";
export { default } from "./accountService.ts";
```

### Step 4: Consume the public API
Consumers can now import everything from the central `index.ts` entry point in a single statement:
```ts
import summarizeAccount, { formatBalance } from "./index.ts";
import type { Account, AccountSummary } from "./index.ts";

const userAccount: Account = { id: "acc-101", balance: 250 };
const summary: AccountSummary = summarizeAccount(userAccount);
```

## Your turn

Organize your web app's domain code into modules and expose them through a clean barrel entry point:
1. In `service.ts`, complete the default export function `renderUserResponse(response: ApiResponse<User>): ServiceResult`. It should compute `formatted` using `formatResponse(response)`, and compute `valid` as `true` only if `response.status === "success"` and `isUser(response.data)` is `true` (otherwise `false`).
2. In `index.ts`, use wildcard re-exports (`export * from ...`) to re-export all exports from `./guards.ts`, `./api.ts`, and `./service.ts`.
3. In `index.ts`, re-export the default export from `./service.ts` as the default export of `index.ts`.

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
