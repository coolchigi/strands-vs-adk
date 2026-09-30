# Generic Functions and Type Constraints

*Typed Functions and Generic Utilities*

## By the end of this lesson you can

- Write generic functions and generic types with type parameter constraints using extends
- Constrain a generic type parameter to valid keys of another type using extends keyof

## Where we are

Earlier lessons established that TypeScript uses interfaces to describe object shapes and contracts for HTTP requests and responses. We also learned how function parameters and return types enforce specific values and structures at compile time.

## The idea

A generic type parameter constraint can be defined by using an interface along with the `extends` keyword on the type variable ([source](https://www.typescriptlang.org/docs/handbook/2/generics.html)). An `extends` clause can be used in a generic function to constrain a type parameter to a specific subset of types ([source](https://www.typescriptlang.org/docs/handbook/2/functions.html)). The type of a generic function lists the type parameters first, followed by parameter and return types ([source](https://www.typescriptlang.org/docs/handbook/2/generics.html)).

When calling a generic function, the TypeScript compiler can automatically infer the type argument based on the argument passed in ([source](https://www.typescriptlang.org/docs/handbook/2/generics.html)). Constraining a generic type parameter to a shape does not allow returning an arbitrary object matching that constraint if the return type is typed as the parameter itself ([source](https://www.typescriptlang.org/docs/handbook/2/functions.html)). Default types for a type parameter must satisfy any constraint specified on that type parameter ([source](https://www.typescriptlang.org/docs/handbook/2/generics.html)).

A generic parameter can be moved to the whole interface so that it is visible to all members and locked in when the interface type argument is specified ([source](https://www.typescriptlang.org/docs/handbook/2/generics.html)). In addition, a type parameter can be constrained by another type parameter, such as ensuring a key exists on an object type using `extends keyof` ([source](https://www.typescriptlang.org/docs/handbook/2/generics.html)).

## Worked example

### Step 1: Constrain a Generic Type Parameter with an Interface

Suppose we need a function that accepts any entity having an `id` field and logs it. Without a constraint, accessing `.id` on an unconstrained type `T` triggers a compiler error. We create an interface and use `extends` to enforce the shape:

```ts
interface Identifiable {
  id: string;
}

function touchRecord<T extends Identifiable>(record: T): T {
  console.log(`Touched entity ${record.id}`);
  return record;
}
```

Because `T` extends `Identifiable`, TypeScript knows `record.id` is valid. Crucially, the return type is `T`, meaning caller-specific properties (like `name` or `email`) are preserved rather than collapsed to `Identifiable`.

### Step 2: Constrain a Type Parameter with `extends keyof`

To safely read an arbitrary property from an object, we must prevent callers from passing property names that do not exist on that object. We constrain a second type parameter `K` to `keyof T`:

```ts
function readField<T, K extends keyof T>(target: T, key: K): T[K] {
  return target[key];
}

const user = { id: "user-1", username: "alice", age: 30 };
const name = readField(user, "username"); // Inferred type of name is string
// readField(user, "password"); // Error: Argument of type '"password"' is not assignable
```

Here, the compiler infers `T` as `{ id: string; username: string; age: number }` and constrains `K` to `"id" | "username" | "age"`. The return type `T[K]` accurately resolves to the specific property type.

### Step 3: Constrain Generic Interfaces

We can move the constrained parameter to an interface so all members share the same entity type:

```ts
interface Store<T extends Identifiable> {
  items: T[];
  findById(id: string): T | undefined;
}
```

Any type supplied to `Store` must satisfy `Identifiable`, ensuring consistency across the store's state and methods.

## Your turn

In `repository.ts`:
1. Update the `EntityStore<T>` interface so that its type parameter `T` is constrained to types implementing `Identifiable` using `extends`.
2. Implement `updateRecord<T extends Identifiable>(record: T): T` as a generic function constrained by `Identifiable` that returns the passed record.
3. Implement `getProperty<T, K extends keyof T>(item: T, key: K): T[K]` with type parameters constrained using `extends keyof` so that it returns `item[key]`.

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
