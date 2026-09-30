# Interfaces, Type Aliases, and Property Modifiers

*Modeling Data Shapes with Interfaces and Types*

## By the end of this lesson you can

- Define application entity shapes using interface declarations and type aliases
- Apply optional (?) and readonly modifiers to object properties to prevent unwanted reassignment and support optional fields

## Where we are

Earlier lessons established how TypeScript checks primitive types such as string and number, and how strict null checks guard against null or undefined values. We also saw how functions declare parameter and return types to make expected values explicit.

## The idea

Object types are defined by listing their properties along with their types ([source](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)). In TypeScript, object types can be named using an interface declaration or a type alias ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html)). An interface declaration serves as a way to define and name an object type ([source](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)). Interfaces fill the role of naming types and defining contracts within code as well as contracts with external code ([source](https://www.typescriptlang.org/docs/handbook/interfaces.html)). However, interfaces can only declare object shapes and cannot be used to rename primitives ([source](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)). When checking an interface, the type checker does not require properties to match any specific order, as long as the required properties are present and match their required types ([source](https://www.typescriptlang.org/docs/handbook/interfaces.html)).

Properties can be marked as optional in object types by appending a question mark (?) after the property name ([source](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)). Optional properties on an interface are declared by placing a ? at the end of the property name in the declaration ([source](https://www.typescriptlang.org/docs/handbook/interfaces.html)). Properties can also be marked as optional by appending a ? to their names in type aliases ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html)). When strictNullChecks is enabled, reading from an optional property will indicate that its value is potentially undefined ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html)).

To restrict property modification, the const keyword is used for immutable variables, whereas readonly is used for immutable properties ([source](https://www.typescriptlang.org/docs/handbook/interfaces.html)). Marking an object property with the readonly modifier prevents reassignment to that property during type-checking ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html)). The readonly modifier prevents re-writing the property itself, but it does not make nested object contents immutable ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html)). Furthermore, TypeScript does not consider readonly modifiers when evaluating compatibility between types, meaning readonly properties can change value via aliasing ([source](https://www.typescriptlang.org/docs/handbook/2/objects.html)).

## Worked example

### Step 1: Declare an entity shape using an interface with property modifiers

Suppose we need an `Article` contract where the identifier should never be overwritten after creation, and a subtitle is optional:

```ts
interface Article {
  readonly id: number;
  title: string;
  subtitle?: string;
}
```

Here, `readonly` tells TypeScript to disallow reassigning `article.id = 2` during type-checking. The `?` on `subtitle?` indicates callers may omit the subtitle.

### Step 2: Declare a companion entity shape using a type alias

We can also name object types using a type alias:

```ts
type Author = {
  readonly id: number;
  name: string;
  bio?: string;
};
```

Both `interface` and `type` allow us to name object structures. Type aliases use an equals sign (`= { ... }`), whereas interface declarations do not.

### Step 3: Consume optional properties safely

Under strict null checks, reading `subtitle` yields `string | undefined`. We must guard access when handling optional properties:

```ts
function formatHeadline(article: Article): string {
  if (article.subtitle !== undefined) {
    return `${article.title} - ${article.subtitle}`;
  }
  return article.title;
}
```

If we try to reassign `article.id = 99`, the compiler rejects the write because of the `readonly` modifier. However, omitting `subtitle` is completely valid because of `?`.

## Your turn

Define data contracts for a web application in `models.ts`:

1. Export an interface `User` with:
   - `readonly id: number`
   - `username: string`
   - `email: string`
   - `bio?: string` (optional)
   - `avatarUrl?: string` (optional)

2. Export a type alias `Post` with:
   - `readonly id: number`
   - `readonly authorId: number`
   - `title: string`
   - `content: string`

3. Export `formatUserProfile(user: User): string` which returns `"<username> (<email>): <bio>"` if `user.bio` is present, or `"<username> (<email>)"` if `user.bio` is undefined.

4. Export `formatPostPreview(post: Post): string` which returns `"[Post #<id> by <authorId>] <title>"`.

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
