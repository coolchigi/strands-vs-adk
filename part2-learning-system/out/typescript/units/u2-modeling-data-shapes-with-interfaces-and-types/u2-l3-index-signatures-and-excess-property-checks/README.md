# Index Signatures and Excess Property Checks

*Modeling Data Shapes with Interfaces and Types*

## By the end of this lesson you can

- Define index signatures for dictionary structures with consistent return types
- Debug excess property check errors on object literal assignments using index signatures and intermediate variables

## Where we are

Earlier lessons showed how to define object interfaces and type aliases with explicit and optional properties. We also saw how TypeScript checks types structurally rather than nominally.

## The idea

When working with dictionary-like structures such as HTTP headers or custom settings, property names may not be known ahead of time, but the value shape is known ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html)). In these cases, you can use an index signature to describe the types of possible values ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html)). TypeScript limits index signature properties to `string`, `number`, `symbol`, template string patterns, or union types consisting purely of these types ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html), [source](https://www.typescriptlang.org/docs/handbook/interfaces.html)). An index signature can also be marked `readonly` to disallow assignment to indexed properties ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html)).

A string index signature enforces that all explicitly defined properties in the interface match the index signature's return type ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html), [source](https://www.typescriptlang.org/docs/handbook/interfaces.html)). In addition, when using both numeric and string indexers on the same type, the return type of the numeric indexer must be a subtype of the type returned by the string indexer ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html), [source](https://www.typescriptlang.org/docs/handbook/interfaces.html)).

Object literals receive special treatment in TypeScript: assigning an object literal to a variable or passing it as an argument triggers excess property checking ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html), [source](https://www.typescriptlang.org/docs/handbook/interfaces.html)). If the object literal has any properties that the target type does not specify, the compiler produces an error ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html), [source](https://www.typescriptlang.org/docs/handbook/interfaces.html)).

There are two primary ways to resolve excess property checking errors when extra properties are legitimate. First, adding a string index signature to the target interface allows the type to accept arbitrary extra properties without error ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html), [source](https://www.typescriptlang.org/docs/handbook/interfaces.html)). Second, assigning the object literal to an intermediate variable before passing it bypasses excess property checks, provided the object shares at least one common property with the target type ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html), [source](https://www.typescriptlang.org/docs/handbook/interfaces.html)). Excess property checks can also be bypassed using a type assertion ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html)).

## Worked example

Consider modeling an environment configuration dictionary where keys are variable names and values are strings, but where you also have a fixed `NODE_ENV` property. We also want to pass request options without failing excess property checks.

Step 1: Define an index signature with consistent property types:
```ts
export interface EnvConfig {
  NODE_ENV: string;
  [key: string]: string;
}
```
Because `[key: string]: string` is declared, the explicit `NODE_ENV` property must also be a `string`.

Step 2: Compare passing an object literal directly versus through an intermediate variable:
```ts
export interface FetchOptions {
  timeout?: number;
  retries?: number;
}

export function fetchResource(url: string, options: FetchOptions): string {
  return `${url}?retries=${options.retries ?? 0}`;
}

// Error: Object literal may only specify known properties, and 'extraTag' does not exist in type 'FetchOptions'.
// fetchResource('/api/users', { retries: 2, extraTag: 'admin' });

// Solution: Assigning to an intermediate variable bypasses excess property checks
const rawOptions = { retries: 2, extraTag: 'admin' };
fetchResource('/api/users', rawOptions); // OK: rawOptions has 'retries', satisfying FetchOptions structurally
```

Step 3: Alternatively, add an index signature if the options type should natively accept extra metadata:
```ts
export interface ExtensibleOptions {
  timeout?: number;
  retries?: number;
  [key: string]: unknown;
}

// Works directly as a literal because of [key: string]: unknown
const result: ExtensibleOptions = { retries: 3, traceId: 'xyz-123' };
```

## Your turn

In `http.ts`, define two dictionary interfaces and two helper functions for an HTTP client:
1. Define `HttpHeaders` as an interface that has an explicit optional property `contentType?: string` and a string index signature returning `string | undefined` so arbitrary headers can be set.
2. Define `RequestOptions` as an interface with `url: string`, `method?: string`, and `headers?: HttpHeaders`. To allow arbitrary custom request options without triggering excess property checks, include a string index signature returning `unknown`.
3. Implement `buildHeaders(customHeaders: Record<string, string>): HttpHeaders` which merges `{ contentType: 'application/json' }` with `customHeaders`.
4. Implement `sendWithIntermediate(options: { url: string; debugToken: string }): { url: string; method: string }` which assigns its argument to an intermediate variable and passes it to `createRequest` (a function that expects `SimpleRequestOptions` without `debugToken`), returning the result.

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
