# Compiler CLI and Strict Type Validation

*Strict Compiler Configuration and Compilation*

## By the end of this lesson you can

- Compile TypeScript source files via the command line using tsc and verify that --noEmitOnError suppresses output when errors occur
- Identify type errors triggered by --noImplicitAny and --strictNullChecks when handling unannotated variables and nullish values

## Where we are

In JavaScript, functions accept arguments without type annotations, and variables can hold null or undefined without static type checks. Runtime errors frequently occur when unvalidated nullish values or unexpected types are accessed during execution. TypeScript introduces compile-time type verification to catch these issues before code runs in production.

## The idea

The TypeScript compiler can compile a source file directly by executing tsc followed by the filename ([source](https://www.typescriptlang.org/docs/handbook/2/basic-types.html)). The --noEmitOnError compiler flag suppresses output file emission whenever type checking errors are reported ([source](https://www.typescriptlang.org/docs/handbook/compiler-options.html)). This flag instructs TypeScript not to generate or update JavaScript output files when type-checking errors are encountered ([source](https://www.typescriptlang.org/docs/handbook/2/basic-types.html)).

When type annotations are missing and TypeScript cannot infer a variable's type, it defaults to type any ([source](https://www.typescriptlang.org/tsconfig/)). The --noImplicitAny compiler option triggers error reporting for expressions and declarations that have an implied any type ([source](https://www.typescriptlang.org/docs/handbook/compiler-options.html)). Enabling the noImplicitAny flag raises errors whenever a variable's type is implicitly inferred as any ([source](https://www.typescriptlang.org/docs/handbook/2/basic-types.html)). Turning on this option causes TypeScript to issue an error whenever it would have defaulted to inferring any ([source](https://www.typescriptlang.org/tsconfig/)). The --noImplicitAny option defaults to true when strict mode is active, and false otherwise ([source](https://www.typescriptlang.org/docs/handbook/compiler-options.html)).

When strictNullChecks is disabled, null and undefined are effectively ignored by TypeScript's type system ([source](https://www.typescriptlang.org/tsconfig/)). The --strictNullChecks flag ensures null and undefined are considered during type checking ([source](https://www.typescriptlang.org/docs/handbook/compiler-options.html)). This flag enforces explicit handling of null and undefined, preventing them from being implicitly assignable to any other type ([source](https://www.typescriptlang.org/docs/handbook/2/basic-types.html)). When strictNullChecks is enabled, null and undefined are treated as distinct types, causing type errors if they are used where a concrete value is expected ([source](https://www.typescriptlang.org/tsconfig/)).

## Worked example

Consider a converted JavaScript file named `greeter.ts` with unannotated variables and unhandled nulls:

```ts
function greet(name) {
  return "Hello, " + name.toUpperCase();
}

let currentUser = null;
greet(currentUser);
```

### Step 1: Running the compiler with strict flags
Execute the compiler from the terminal:
```bash
tsc --noEmitOnError --noImplicitAny --strictNullChecks greeter.ts
```

### Step 2: Analyzing compiler output
The compiler flags two issues:
1. `error TS7006: Parameter 'name' implicitly has an 'any' type.` Because `name` has no annotation and cannot be inferred, TypeScript defaults to `any`, which `--noImplicitAny` rejects.
2. `error TS2345: Argument of type 'null' is not assignable to parameter of type 'string'.` Because `--strictNullChecks` treats `null` as distinct from other types, `currentUser` (typed as `null`) cannot be passed where a string is expected.

Because `--noEmitOnError` was passed, no `greeter.js` file is generated or updated.

### Step 3: Resolving the type errors
Add explicit annotations and handle the nullish possibility:
```ts
function greet(name: string | null): string {
  if (name === null) {
    return "Hello, guest";
  }
  return "Hello, " + name.toUpperCase();
}

let currentUser: string | null = null;
greet(currentUser);
```

### Step 4: Re-compiling
Run the command again:
```bash
tsc --noEmitOnError --noImplicitAny --strictNullChecks greeter.ts
```
The command completes with zero errors and emits the clean JavaScript output file `greeter.js`.

## Your turn

Fix the utility functions in `formatter.ts` to satisfy strict compiler flags:
1. In `parseScore`, add an explicit parameter type annotation `input: string` so it no longer triggers an implicit `any` error, and return `0` if `Number.parseInt(input, 10)` results in `NaN`.
2. In `formatGreeting`, handle `null` and `undefined` safely by returning `"Hello, guest!"` when `name` is nullish, preventing runtime errors and satisfying `--strictNullChecks`.

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
