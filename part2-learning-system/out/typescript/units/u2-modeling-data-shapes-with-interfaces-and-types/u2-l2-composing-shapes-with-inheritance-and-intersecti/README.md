# Composing Shapes with Inheritance and Intersections

*Modeling Data Shapes with Interfaces and Types*

## By the end of this lesson you can

- Compose object shapes using interface extends and type intersection (&)
- Predict type conflicts resulting in never when intersecting types with incompatible property definitions

## Where we are

Earlier lessons established how to describe object shapes using interfaces and type aliases, including optional and readonly modifiers. We also saw how union types let values accept one of several possible types.

## The idea

Interfaces can extend other interfaces using the `extends` keyword to copy members and compose shapes into reusable components ([source](https://www.typescriptlang.org/docs/handbook/interfaces.html)). The `extends` keyword allows an interface to copy and build upon members from other named types, adding whatever new members are needed ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html)) ([source](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)). An interface can also extend multiple types simultaneously ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html)). Extending interfaces with `extends` is often more performant for the compiler than composing type aliases with intersections ([source](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)).

TypeScript also provides intersection types to combine existing object types using the `&` operator ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html)) ([source](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)). When you intersect two or more types, the resulting type contains all the properties of every constituent type ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html)).

When intersecting types have conflicting property types, the conflicting property types are merged automatically ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html)). TypeScript expects the property to satisfy both types simultaneously, which can result in the property having type `never` ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html)). For instance, if type `A` has an `id: string` and type `B` has an `id: number`, the intersection `A & B` yields an `id` property of type `string & number`, which collapses to `never` because no value can be both a string and a number simultaneously ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html)).

## Worked example

Suppose we are modeling permissions and base records for a system.

First, we extract common timestamp tracking into a reusable interface:
```ts
export interface Timestamped {
  createdAt: Date;
  updatedAt: Date;
}
```

Next, an entity interface extends `Timestamped` to inherit those fields and add unique fields:
```ts
export interface Document extends Timestamped {
  id: string;
  title: string;
}
```
A `Document` now requires `createdAt`, `updatedAt`, `id`, and `title`.

To combine independent capability sets without class inheritance, we can use type intersections:
```ts
export type Reader = {
  canRead: boolean;
};

export type Writer = {
  canWrite: boolean;
};

export type Editor = Reader & Writer;
```
An `Editor` requires both `canRead` and `canWrite`.

Finally, consider what happens when intersecting incompatible shapes:
```ts
export type LegacyId = { id: string };
export type ModernId = { id: number };
export type MergedId = LegacyId & ModernId;
```
Because `id` must satisfy `string & number`, TypeScript resolves `MergedId['id']` to `never`. If a function attempts to assign any value (such as a string or number) to `id` on a `MergedId` object, the compiler reports an error because no value can ever be assigned to `never`.

## Your turn

In `models.ts`:
1. Define and export an interface `Timestamped` containing `createdAt: Date` and `updatedAt: Date`.
2. Update `User` and `Post` so that both inherit from `Timestamped` using `extends`.
3. Define and export types `Permission` and `AuditDetails`, then compose them into `AdminRole` using the `&` intersection operator.
   - `Permission` must have `role: string` and `canDelete: boolean`.
   - `AuditDetails` must have `lastLogin: Date`.
4. Define and export a type `ConflictingId` that intersects `{ id: string } & { id: number }`, and export a type alias `ConflictCheck = ConflictingId['id']` which collapses to `never`.
5. Implement and export `createAuditedUser(user: User, admin: AdminRole)` which returns a merged object containing all properties of `user` and `admin`.

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
