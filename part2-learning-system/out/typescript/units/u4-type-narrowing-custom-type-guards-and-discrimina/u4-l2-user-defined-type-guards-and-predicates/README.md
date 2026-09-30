# User-Defined Type Guards and Predicates

*Type Narrowing, Custom Type Guards, and Discriminated Unions*

## By the end of this lesson you can

- Write user-defined type guard functions returning type predicates (parameterName is Type) to validate unknown API inputs

## Where we are

Earlier lessons showed how TypeScript narrows types inside conditional blocks using standard JavaScript checks like typeof and the in operator. We also saw that network responses and unvalidated payloads often enter an application typed as unknown, requiring validation before accessing properties.

## The idea

A user-defined type guard function uses a type predicate as its return type annotation ([source](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)). A return type predicate must follow the syntax parameterName is Type, referencing a parameter from the function's signature ([source](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)).

When a user-defined type guard with parameterName is Type is used in an if/else check, TypeScript narrows the variable to the specified type in the if branch and eliminates that type in the else branch ([source](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)).

## Worked example

Suppose an API returns an untyped JSON payload that we expect to be an `Article` with a string `title` and a numeric `views` count.

First, define the target interface:
```ts
interface Article {
  title: string;
  views: number;
}
```

Second, write the type guard function. Instead of returning `boolean`, we annotate the return type with the predicate `data is Article`, matching the parameter name `data`:
```ts
function isArticle(data: unknown): data is Article {
  if (typeof data !== "object" || data === null) {
    return false;
  }
  return (
    "title" in data &&
    typeof (data as Record<string, unknown>).title === "string" &&
    "views" in data &&
    typeof (data as Record<string, unknown>).views === "number"
  );
}
```

Third, consume the guard in application code:
```ts
function processPayload(payload: unknown) {
  if (isArticle(payload)) {
    // Inside this if branch, TypeScript narrows `payload` to `Article`
    console.log(payload.title.toUpperCase(), payload.views.toFixed(0));
  } else {
    // In the else branch, `Article` is eliminated
    console.error("Invalid payload shape");
  }
}
```
Because `isArticle` returns a type predicate, TypeScript safely enables property access on `payload` inside the `if` block without requiring explicit type assertions.

## Your turn

In guards.ts, implement two user-defined type guard functions: `isUser(data: unknown): data is User` and `isPost(data: unknown): data is Post`.

1. Annotate `isUser` with the return type predicate `data is User`. It must return `true` only when `data` is a non-null object with an `id` property of type `number` and a `name` property of type `string`.
2. Annotate `isPost` with the return type predicate `data is Post`. It must return `true` only when `data` is a non-null object with an `id` property of type `number`, a `title` property of type `string`, and an `authorId` property of type `number`.

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
