# TypeScript for JavaScript Developers: Building Typed Web Applications

A progressive curriculum designed for JavaScript developers to master TypeScript's type system, strict compiler configuration, data modeling, generics, narrowing, and module structures while constructing the data and API layer of a web application.

## Who this is for

```text
Subject: TypeScript (language)
Goal: learn TypeScript so I can build a small web app
Starting from: I know JavaScript well but have never used TypeScript
Wants to be able to: a small web app with a backend API
```

## What you'll be able to do

- Configure TypeScript projects with strict compiler safety settings and downleveling targets
- Model application data structures using interfaces, type aliases, modifiers, inheritance, and index signatures
- Author reusable typed asynchronous functions, generic utilities, and constrained generic data accessors
- Safely narrow untyped and union data using runtime guards, custom type predicates, and exhaustive discriminated unions
- Modularize web applications and APIs using ECMAScript modules and type-only imports compatible with modern bundlers

Written against TypeScript 7.0 ([source](https://www.typescriptlang.org/download)).

What this course covers comes from the official documentation, shaped by what you said you want to do. Every fact in a lesson links to the page it came from. `SOURCES.md` lists them all.

## How to use it

```bash
learn next      # where you are, and what's next
learn check     # run the current exercise's tests
learn hint      # one hint at a time
learn quiz      # answer, then see the answers
learn review    # questions you missed, when they're due again
```

No `learn` command? Type `python3 learn.py` wherever it says `learn` (`py learn.py` on Windows), and everything works the same from this folder. Each lesson's exercise says what you need installed to run its tests.

## Units

### u1. Strict Compiler Configuration and Compilation

1. [Compiler CLI and Strict Type Validation](units/u1-strict-compiler-configuration-and-compilation/u1-l1-compiler-cli-and-strict-type-validation/README.md)
2. [Configuring tsconfig.json and Target Downleveling](units/u1-strict-compiler-configuration-and-compilation/u1-l2-configuring-tsconfig-json-and-target-downlevelin/README.md)

**Project:** Create a baseline project repository containing tsconfig.json configured with strict mode, noEmitOnError, and downleveling target, verifying that tsc without arguments successfully compiles valid files and prevents emit when intentional type errors are introduced.

### u2. Modeling Data Shapes with Interfaces and Types

1. [Interfaces, Type Aliases, and Property Modifiers](units/u2-modeling-data-shapes-with-interfaces-and-types/u2-l1-interfaces-type-aliases-and-property-modifiers/README.md)
2. [Composing Shapes with Inheritance and Intersections](units/u2-modeling-data-shapes-with-interfaces-and-types/u2-l2-composing-shapes-with-inheritance-and-intersecti/README.md)
3. [Index Signatures and Excess Property Checks](units/u2-modeling-data-shapes-with-interfaces-and-types/u2-l3-index-signatures-and-excess-property-checks/README.md)

**Project:** Build an in-memory data schema for a blogging web application containing User, Post, Category, and Tag models using interface extension, intersection types for audit timestamps, and an index-signature-backed configuration map with immutable identifier properties.

### u3. Typed Functions and Generic Utilities

1. [Function Signatures, Promises, and Special Return Types](units/u3-typed-functions-and-generic-utilities/u3-l1-function-signatures-promises-and-special-return-/README.md)
2. [Generic Functions and Type Constraints](units/u3-typed-functions-and-generic-utilities/u3-l2-generic-functions-and-type-constraints/README.md)

**Project:** Develop a typed CRUD service module with generic asynchronous methods (find, create, update, delete) that enforce entity constraints with extends { id: string }, type-safe property extractors, and fail-fast never error handlers.

### u4. Type Narrowing, Custom Type Guards, and Discriminated Unions

1. [Narrowing with Runtime Type Guards](units/u4-type-narrowing-custom-type-guards-and-discrimina/u4-l1-narrowing-with-runtime-type-guards/README.md)
2. [User-Defined Type Guards and Predicates](units/u4-type-narrowing-custom-type-guards-and-discrimina/u4-l2-user-defined-type-guards-and-predicates/README.md)
3. [Discriminated Unions and Exhaustive Checks](units/u4-type-narrowing-custom-type-guards-and-discrimina/u4-l3-discriminated-unions-and-exhaustive-checks/README.md)

**Project:** Build a network state manager and action dispatcher for the web app that processes discriminated union actions, validates raw incoming API messages with custom type guard predicates, and ensures exhaustive action handling at compile time.

### u5. Modular Architecture and Type-Only Imports

1. [ES Modules with Types and Values](units/u5-modular-architecture-and-type-only-imports/u5-l1-es-modules-with-types-and-values/README.md)
2. [Type-Only Imports and Bundler Optimization](units/u5-modular-architecture-and-type-only-imports/u5-l2-type-only-imports-and-bundler-optimization/README.md)

**Project:** Refactor the entire web application project into a modular architecture consisting of separate files for models, type guards, API client utilities, and state reducers, utilizing type-only imports throughout to ensure complete bundler elision and compiling cleanly under strict tsconfig settings.
