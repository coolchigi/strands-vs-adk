# Configuring tsconfig.json and Target Downleveling

*Strict Compiler Configuration and Compilation*

## By the end of this lesson you can

- Write a tsconfig.json file enabling strict mode and project compilation
- Configure the target compiler option to downlevel modern JavaScript syntax to ECMAScript 2015

## Where we are

In the previous lesson, you learned how TypeScript uses type annotations to verify values and handle nullable types before code executes. You also saw how type checking catches type mismatches and prevents runtime errors in basic functions.

## The idea

A `tsconfig.json` file designates the root files and compiler options needed to compile a TypeScript project ([source](https://www.typescriptlang.org/docs/handbook/tsconfig-json.html)). When `compilerOptions` is omitted from `tsconfig.json`, TypeScript applies default compiler settings ([source](https://www.typescriptlang.org/docs/handbook/tsconfig-json.html)). Running `tsc` locally without arguments compiles the nearest project defined by a `tsconfig.json` file ([source](https://www.typescriptlang.org/docs/handbook/compiler-options.html)). If you invoke `tsc` without specifying input files, the compiler searches for `tsconfig.json` starting in the current directory and continues up through parent directories ([source](https://www.typescriptlang.org/docs/handbook/tsconfig-json.html)). You can also invoke `tsc` with the `--project` or `-p` flag pointing to a directory or a specific configuration file to compile a project ([source](https://www.typescriptlang.org/docs/handbook/tsconfig-json.html)). In contrast, specifying input files directly on the command line causes `tsc` to ignore `tsconfig.json` files entirely ([source](https://www.typescriptlang.org/docs/handbook/compiler-options.html)) ([source](https://www.typescriptlang.org/docs/handbook/tsconfig-json.html)).

Setting `"strict": true` in `tsconfig.json` turns on all strict mode family options simultaneously ([source](https://www.typescriptlang.org/docs/handbook/2/basic-types.html)) ([source](https://www.typescriptlang.org/docs/handbook/compiler-options.html)). Enabling the strict flag enforces stronger guarantees of program correctness across the codebase ([source](https://www.typescriptlang.org/tsconfig/)). Even when `strict` is set to `true`, individual strict mode family checks can be turned off independently if needed ([source](https://www.typescriptlang.org/docs/handbook/2/basic-types.html)) ([source](https://www.typescriptlang.org/tsconfig/)).

The `target` compiler option specifies the JavaScript language version for emitted JavaScript and includes corresponding compatible library declarations ([source](https://www.typescriptlang.org/docs/handbook/compiler-options.html)). Downleveling allows TypeScript to rewrite and transpile newer ECMAScript syntax to older ECMAScript versions based on this target ([source](https://www.typescriptlang.org/docs/handbook/2/basic-types.html)). For instance, setting `target` to `es2015` compiles TypeScript code down to ECMAScript 2015 compatible code so it runs anywhere ECMAScript 2015 is supported ([source](https://www.typescriptlang.org/docs/handbook/2/basic-types.html)).

## Worked example

Suppose you have a project with modern syntax that you need to compile down to ECMAScript 2015 while enforcing strict type-checking across all project files.

First, define a root `tsconfig.json` file in the project directory:

```json
{
  "compilerOptions": {
    "target": "es2015",
    "strict": true
  }
}
```

- The `target` setting is assigned `"es2015"`. This tells the TypeScript compiler to downlevel newer ECMAScript features (such as modern operators) down to ES2015-compatible output and bring in ES2015 library typings.
- The `strict` setting is assigned `true`. This enables all strict-mode family checks (including `strictNullChecks` and `noImplicitAny`) to guarantee program correctness.

Now, invoking `tsc` without arguments searches the current directory, detects this `tsconfig.json`, and compiles the project according to these options without needing manual CLI flags.

## Your turn

Configure `tsconfig.json` to enable strict mode and project compilation downleveling to ECMAScript 2015. Specifically, set `compilerOptions.target` to `"es2015"` and `compilerOptions.strict` to `true`.

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
