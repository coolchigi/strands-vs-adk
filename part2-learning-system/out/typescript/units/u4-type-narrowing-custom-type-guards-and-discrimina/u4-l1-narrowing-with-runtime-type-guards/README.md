# Narrowing with Runtime Type Guards

*Type Narrowing, Custom Type Guards, and Discriminated Unions*

## By the end of this lesson you can

- Narrow union types using typeof, truthiness checks, equality checks, and the in operator
- Explain why typeof null evaluates to 'object' and how to safely narrow null from object unions

## Where we are

Earlier lessons introduced union types and optional properties for representing values that can take multiple shapes. We also saw functions accepting unknown or union inputs, requiring validation before safely accessing specific properties.

## The idea

Narrowing occurs when TypeScript deduces a more specific type for a value based on the structure of the code ([source](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)). In TypeScript, checking against the string returned by JavaScript's typeof operator acts as a type guard ([source](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)). TypeScript expects typeof to return one of eight string values: 'string', 'number', 'bigint', 'boolean', 'symbol', 'undefined', 'object', or 'function' ([source](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)). A union type can be narrowed by checking the JavaScript typeof operator against a type name such as 'string' ([source](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)).

JavaScript has a historical quirk where typeof null evaluates to 'object' ([source](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)). Because typeof null evaluates to 'object', narrowing with typeof strs === 'object' on a union like string | string[] | null leaves null in the type ([source](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)). To remove null safely, a union type containing null can be narrowed by performing an equality check against null ([source](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)). Furthermore, checking loosely whether a value is not equal to null using != null narrows out both null and undefined from the type ([source](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)). Checking for undefined using an inequality check narrows an optional property to its defined type ([source](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)).

TypeScript also uses switch statements and equality operators including ===, !==, ==, and != to narrow types ([source](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)). In conditionals, values like 0, NaN, the empty string, 0n, null, and undefined coerce to false, while all other values coerce to true ([source](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)). Boolean negations using the ! operator filter out truthy types from the negated branches ([source](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)). Double-boolean negation (!!) causes TypeScript to infer a literal boolean type true on truthy values, whereas the Boolean function infers the broader boolean type ([source](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)).

When dealing with objects in a union, JavaScript's in operator provides another narrowing tool ([source](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)). Using the in operator to test 'value' in x narrows the true branch to union types with an optional or required property named value, and the false branch to types with an optional or missing property ([source](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)).

## Worked example

Consider a function that formats an incoming message value that can be a string, a list of strings, or null:

```typescript
type InputMessage = string | string[] | null;

function formatMessage(msg: InputMessage): string {
  // 1. Narrow out null using an equality check
  if (msg === null) {
    return "(empty)";
  }
  // msg is now string | string[]

  // 2. Narrow using typeof
  if (typeof msg === "string") {
    return msg.trim();
  }
  // msg is now string[]
  return msg.join(", ");
}
```

If we had checked `typeof msg === "object"` first without checking `msg === null`, TypeScript would keep `null` in the union because `typeof null === "object"` in JavaScript. By handling `msg === null` first, `null` is removed, leaving only valid object/array types.

## Your turn

In `payload.ts`, implement two functions that safely narrow union types:
1. `formatPayload(payload: string | number | string[] | null): string`: 
   - If `payload === null`, return `"none"`.
   - If `typeof payload === "number"`, return `payload.toFixed(2)`.
   - If `typeof payload === "string"`, check truthiness: if it is empty (`!payload`), return `"empty string"`; otherwise return `payload.trim()`.
   - Otherwise (`payload` is `string[]`), join the items with `", "`.
2. `extractData(response: { error: string } | { data: string }): string`: 
   - Use the `in` operator to check if `"error"` is in `response`. If so, return `"Error: " + response.error`.
   - Otherwise, return response.data.

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
