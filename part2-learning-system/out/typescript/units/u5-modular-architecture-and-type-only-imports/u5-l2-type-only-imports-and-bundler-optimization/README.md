# Type-Only Imports and Bundler Optimization

*Modular Architecture and Type-Only Imports*

## By the end of this lesson you can

- Declare type-only imports (import type) and inline type imports to distinguish types from runtime values
- Debug compiler errors caused by using identifiers imported via import type in runtime value positions

## Where we are

Earlier lessons demonstrated how to define entity interfaces and type guards in dedicated modules, and how to import them into service files. You also learned how discriminated unions narrow response types across API handling boundaries.

## The idea

An `import type` declaration restricts the statement to only importing types ([source](https://www.typescriptlang.org/docs/handbook/2/modules.html)). Even values can be imported with `import type`, but because they will not exist in emitted JavaScript, they can only be referenced in non-emitting type positions ([source](https://www.typescriptlang.org/docs/handbook/modules/reference.html)). Using an identifier imported via `import type` as a value causes a TypeScript compiler error ([source](https://www.typescriptlang.org/docs/handbook/2/modules.html)).

A type-only import declaration cannot specify both a default import and named bindings together because of ambiguity over what the `type` keyword modifies ([source](https://www.typescriptlang.org/docs/handbook/modules/reference.html)).

Individual imports within a statement can be prefixed with `type` to declare inline type imports ([source](https://www.typescriptlang.org/docs/handbook/2/modules.html)). Type-only imports and inline type imports enable transpilers like Babel, swc, and esbuild to recognize which imports can be safely stripped ([source](https://www.typescriptlang.org/docs/handbook/2/modules.html)). Import declarations using `import type`, exports using `export type { ... }`, and individual specifiers prefixed with `type` are guaranteed to be elided from compiled JavaScript ([source](https://www.typescriptlang.org/docs/handbook/modules/reference.html)).

## Worked example

Suppose you have a module `session.ts` that exports an interface `Session` and a runtime helper `createSession`:

```ts
export interface Session {
  token: string;
  userId: number;
}

export function createSession(userId: number): Session {
  return { token: "abc-123", userId };
}
```

If a consumer file needs the `Session` type for annotations and `createSession` as a runtime function, importing both under `import type` causes an error:

```ts
import type { Session, createSession } from "./session.ts";

const session: Session = createSession(1); // Compiler Error: 'createSession' cannot be used as a value because it was imported using 'import type'.
```

Because `createSession` was declared with `import type`, TypeScript forbids its use in value positions and transpilers strip the import entirely ([source](https://www.typescriptlang.org/docs/handbook/modules/reference.html), [source](https://www.typescriptlang.org/docs/handbook/2/modules.html)).

To resolve this while keeping transpilers informed about which imports to strip, use an inline type import ([source](https://www.typescriptlang.org/docs/handbook/2/modules.html)):

```ts
import { createSession, type Session } from "./session.ts";

const session: Session = createSession(1); // OK
```

In the emitted JavaScript, transpilers elide `Session` and retain `createSession` ([source](https://www.typescriptlang.org/docs/handbook/modules/reference.html)).

## Your turn

In `service.ts`, fix the import from `./guards.ts` so runtime guard functions (`isUser` and `isPost`) are imported as values, while entity interfaces (`User` and `Post`) are imported as inline types. Then implement `renderPostResponse` to validate that `response.status === "success" && isPost(response.data)` and format the response using `formatResponse(response)`.

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
