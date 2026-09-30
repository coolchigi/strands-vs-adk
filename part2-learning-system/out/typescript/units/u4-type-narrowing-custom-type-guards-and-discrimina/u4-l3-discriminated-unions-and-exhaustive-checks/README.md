# Discriminated Unions and Exhaustive Checks

*Type Narrowing, Custom Type Guards, and Discriminated Unions*

## By the end of this lesson you can

- Construct discriminated unions with common literal discriminant properties
- Enforce compile-time exhaustive switch checking over discriminated unions using the never type in the default case

## Where we are

Earlier lessons established how TypeScript narrows union types using control flow analysis and custom type predicates. We also saw how checking object shapes helps refine general types into specific structures.

## The idea

When every type within a union contains a shared property with literal types, TypeScript recognizes it as a discriminated union and can narrow out members of the union ([source](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)). Discriminated union members can be narrowed in both if checks and switch statements by checking their discriminant property ([source](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)).

When narrowing reduces a union's possibilities so completely that no types remain, TypeScript represents that unreachable state with the never type ([source](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)) ([source](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)). The never type can be assigned to every type, but no type other than never itself is assignable to never ([source](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)).

Narrowing can be combined with assigning to a never-typed variable in a switch statement's default branch to achieve exhaustive checking ([source](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)). Exhaustive checking in a switch statement can be enforced by assigning the unhandled discriminated union variable to a const typed as never in the default case ([source](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)). Adding an unhandled case to a discriminated union that has an exhaustive check assigning to never will cause a TypeScript compile error ([source](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)).

## Worked example

Consider modeling geometric shapes where each shape has its own dimensions.

First, define interfaces that share a common literal discriminant property, such as `kind`:

```typescript
interface Circle {
  kind: "circle";
  radius: number;
}

interface Square {
  kind: "square";
  sideLength: number;
}

type Shape = Circle | Square;
```

Next, write a function that calculates the area using a `switch` statement on `shape.kind`. Inside each case branch, TypeScript narrows `shape` to the matching variant:

```typescript
function getArea(shape: Shape): number {
  switch (shape.kind) {
    case "circle":
      return Math.PI * shape.radius ** 2;
    case "square":
      return shape.sideLength ** 2;
    default: {
      const _exhaustiveCheck: never = shape;
      return _exhaustiveCheck;
    }
  }
}
```

In the `default` block, all possibilities of `Shape` have been handled, so TypeScript narrows `shape` to `never`. Assigning `shape` to `_exhaustiveCheck: never` succeeds.

If we later expand `Shape` to include `Triangle` (`kind: "triangle"`) but forget to add `case "triangle":`, TypeScript reaches `default` with `shape` typed as `Triangle`. Because `Triangle` is not assignable to `never`, the compiler raises an error at build time before any broken code reaches production.

## Your turn

Model an API response as a discriminated union and implement an exhaustive switch statement.

1. In `api.ts`, update `SuccessResponse<T>` so that its discriminant `status` has the literal type `"success"` and includes `data: T`.
2. Update `ErrorResponse` so that its discriminant `status` has the literal type `"error"` and includes `error: string`.
3. Implement `formatResponse<T>(response: ApiResponse<T>): string` using a `switch (response.status)`:
   - When `"loading"`: return `"Loading..."`
   - When `"success"`: return `"Data: " + JSON.stringify(response.data)`
   - When `"error"`: return `"Error: " + response.error`
   - In the `default` branch: enforce exhaustive checking by assigning `response` to a constant typed as `never` (`const _exhaustiveCheck: never = response;`) and return `_exhaustiveCheck`.

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
