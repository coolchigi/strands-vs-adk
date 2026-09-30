# Sources

Every claim a lesson teaches, the words it rests on, and where they are.

## [https://www.typescriptlang.org/docs/handbook/2/basic-types.html](https://www.typescriptlang.org/docs/handbook/2/basic-types.html)

official, fetched 2026-09-28

- The TypeScript compiler can compile a source file directly by executing tsc followed by the filename.  
  > tsc hello.ts
- The --noEmitOnError compiler flag instructs TypeScript not to generate or update JavaScript output files when type-checking errors are encountered.  
  > In that case, you can use the noEmitOnError compiler option.
Try changing your hello.ts file and running tsc with that flag:
sh
tsc --noEmitOnError hello.ts
You’ll notice that hello.js never gets updated.
- Downleveling allows TypeScript to transpile newer ECMAScript syntax to older ECMAScript versions using the target option.  
  > TypeScript has the ability to rewrite code from newer versions of ECMAScript to older ones such as ECMAScript 3 or ECMAScript 5 (a.k.a. ES5).
This process of moving from a newer or “higher” version of ECMAScript down to an older or “lower” one is sometimes called downleveling.
By default TypeScript targets ES5, an extremely old version of ECMAScript.
We could have chosen something a little bit more recent by using the target option.
- Targeting ES2015 via the --target es2015 flag compiles TypeScript down to ECMAScript 2015 compatible code.  
  > Running with --target es2015 changes TypeScript to target ECMAScript 2015, meaning code should be able to run wherever ECMAScript 2015 is supported.
So running tsc --target es2015 hello.ts gives us the following output:
- The CLI flag strict or the tsconfig.json setting "strict": true turns on all strict type-checking flags at once.  
  > The strict flag in the CLI, or "strict": true in a tsconfig.json toggles them all on simultaneously, but we can opt out of them individually.
- Enabling the noImplicitAny flag raises errors whenever a variable's type is implicitly inferred as any.  
  > Turning on the noImplicitAny flag will issue an error on any variables whose type is implicitly inferred as any.
- The strictNullChecks flag enforces explicit handling of null and undefined, preventing them from being implicitly assignable to any other type.  
  > By default, values like null and undefined are assignable to any other type.
This can make writing some code easier, but forgetting to handle null and undefined is the cause of countless bugs in the world - some consider it a billion dollar mistake!
The strictNullChecks flag makes handling null and undefined more explicit, and spares us from worrying about whether we forgot to handle null and undefined.

## [https://www.typescriptlang.org/docs/handbook/2/everyday-types.html](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)

official, fetched 2026-09-28

- Object types are defined by listing their properties along with their types.  
  > To define an object type, we simply list its properties and their types.
- Properties can be marked as optional in object types by appending a question mark (?) after the property name.  
  > Object types can also specify that some or all of their properties are optional. To do this, add a ? after the property name:
- An interface declaration serves as a way to define and name an object type.  
  > An interface declaration is another way to name an object type:
- Interfaces can only declare object shapes and cannot be used to rename primitives.  
  > Interfaces may only be used to declare the shapes of objects, not rename primitives.
- Interfaces can be composed and extended using the extends keyword.  
  > interface Bear extends Animal {
  honey: boolean;
}
- Types can be composed and extended using type intersection (&).  
  > type Bear = Animal & { 
  honey: boolean;
}
- Extending interfaces using the extends keyword is often more performant for the compiler than composing type aliases with intersections.  
  > Using interfaces with extends can often be more performant for the compiler than type aliases with intersections
- Function parameter type annotations are written immediately following the parameter name to indicate the acceptable types of inputs.  
  > When you declare a function, you can add type annotations after each parameter to declare what types of parameters the function accepts.
Parameter type annotations go after the parameter name:
- Function return type annotations are positioned directly after the function parameter list.  
  > You can also add return type annotations.
Return type annotations appear after the parameter list:
- When annotating the return type of a function that returns a promise, use the Promise type.  
  > If you want to annotate the return type of a function which returns a promise, you should use the Promise type:
- An async function returning a number can be explicitly annotated with a return type of Promise<number>.  
  > async function
getFavoriteNumber
():
Promise
<number> {
return 26;
}
- Narrowing occurs when TypeScript deduces a more specific type for a value based on code structure.  
  > Narrowing occurs when TypeScript can deduce a more specific type for a value based on the structure of the code.
- A union type can be narrowed by checking the JavaScript typeof operator against a type name such as 'string'.  
  > if (typeof
id
=== "string") {
// In this branch, id is of type 'string'
console
.
log
(
id
.
toUpperCase
());
} else {
// Here, id is of type 'number'
console
.
log
(
id
);
}
- Checking for undefined using an inequality check narrows an optional property to its defined type.  
  > if (
obj
.
last
!==
undefined
) {
// OK
console
.
log
(
obj
.
last
.
toUpperCase
());
}
- A union type containing null can be narrowed by performing an equality check against null.  
  > function
doSomething
(
x
: string | null) {
if (
x
=== null) {
// do nothing
} else {
console
.
log
("Hello, " +
x
.
toUpperCase
());
}
}

## [https://www.typescriptlang.org/docs/handbook/2/narrowing.html](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)

official, fetched 2026-09-28

- When narrowing reduces a union type so that all possible types are eliminated, TypeScript represents that unreachable state with the never type.  
  > When narrowing, you can reduce the options of a union to a point where you have removed all possibilities and have nothing left.
In those cases, TypeScript will use a never type to represent a state which shouldn’t exist.
- The never type can be assigned to every type, but no type other than never itself is assignable to never.  
  > The never type is assignable to every type; however, no type is assignable to never (except never itself).
- Narrowing can be combined with assigning to a never-typed variable in a switch statement's default branch to achieve exhaustive checking.  
  > This means you can use narrowing and rely on never turning up to do exhaustive checking in a switch statement.
- A user-defined type guard function uses a type predicate as its return type annotation.  
  > To define a user-defined type guard, we simply need to define a function whose return type is a type predicate:
- A return type predicate must follow the syntax parameterName is Type, referencing a parameter from the function's signature.  
  > A predicate takes the form parameterName is Type, where parameterName must be the name of a parameter from the current function signature.
- Checking a value against the string returned by JavaScript's typeof operator acts as a type guard in TypeScript.  
  > In TypeScript, checking against the value returned by typeof is a type guard.
- TypeScript expects typeof to return one of eight string values: 'string', 'number', 'bigint', 'boolean', 'symbol', 'undefined', 'object', or 'function'.  
  > TypeScript expects this to return a certain set of strings:
"string"
"number"
"bigint"
"boolean"
"symbol"
"undefined"
"object"
"function"
- Because typeof null evaluates to 'object' in JavaScript, narrowing with typeof strs === 'object' on a union like string | string[] | null leaves null in the type.  
  > luckily, TypeScript lets us know that strs was only narrowed down to string[] | null instead of just string[].
- Values such as 0, NaN, the empty string, 0n, null, and undefined coerce to false, while all other values coerce to true in JavaScript conditionals.  
  > Values like
0
NaN
"" (the empty string)
0n (the bigint version of zero)
null
undefined
all coerce to false, and other values get coerced to true.
- Double-boolean negation (!!) causes TypeScript to infer a literal boolean type true on truthy values, whereas the Boolean function infers the broader boolean type.  
  > You can always coerce values to booleans by running them through the Boolean function, or by using the shorter double-Boolean negation. (The latter has the advantage that TypeScript infers a narrow literal boolean type true, while inferring the first as type boolean.)
- Boolean negations using the ! operator filter out truthy types from the negated branches.  
  > One last word on narrowing by truthiness is that Boolean negations with ! filter out from negated branches.
- TypeScript narrows types using switch statements and equality operators including ===, !==, ==, and !=.  
  > TypeScript also uses switch statements and equality checks like ===, !==, ==, and != to narrow types.
- Checking loosely whether a value is not equal to null using != null narrows out both null and undefined from the type.  
  > checking whether something == null actually not only checks whether it is specifically the value null - it also checks whether it’s potentially undefined. The same applies to == undefined: it checks whether a value is either null or undefined.
- Using the in operator to test 'value' in x narrows the true branch to union types with an optional or required property named value, and the false branch to types with an optional or missing property.  
  > The “true” branch narrows x’s types which have either an optional or required property value, and the “false” branch narrows to types which have an optional or missing property value.
- When a user-defined type guard with parameterName is Type is used in an if/else check, TypeScript narrows the variable to the specified type in the if branch and eliminates that type in the else branch.  
  > Notice that TypeScript not only knows that pet is a Fish in the if branch;
it also knows that in the else branch, you don’t have a Fish, so you must have a Bird.
- When every type within a union contains a shared property with literal types, TypeScript recognizes it as a discriminated union and can narrow out members of the union.  
  > When every type in a union contains a common property with literal types, TypeScript considers that to be a discriminated union, and can narrow out the members of the union.
- Discriminated union members can be narrowed in both if checks and switch statements by checking their discriminant property.  
  > The same checking works with switch statements as well.
- When narrowing reduces a union's possibilities so completely that no types remain, TypeScript represents that state with the never type.  
  > When narrowing, you can reduce the options of a union to a point where you have removed all possibilities and have nothing left. In those cases, TypeScript will use a never type to represent a state which shouldn’t exist.
- Exhaustive checking in a switch statement can be enforced by assigning the unhandled discriminated union variable to a const typed as never in the default case.  
  > This means you can use narrowing and rely on never turning up to do exhaustive checking in a switch statement.
For example, adding a default to our getArea function which tries to assign the shape to never will not raise an error when every possible case has been handled.
- Adding an unhandled case to a discriminated union that has an exhaustive check assigning to never will cause a TypeScript compile error.  
  > default:
const
_exhaustiveCheck
: never =
shape
;
Type 'Triangle' is not assignable to type 'never'.2322Type 'Triangle' is not assignable to type 'never'.
return
_exhaustiveCheck
;

## [https://www.typescriptlang.org/docs/handbook/2/functions.html](https://www.typescriptlang.org/docs/handbook/2/functions.html)

official, fetched 2026-09-28

- In a function type expression, parameter names are required; omitting a parameter name and writing only a type name makes the identifier become the parameter name typed as any.  
  > Note that the parameter name is required. The function type (string) => void means “a function with a parameter named string of type any“!
- An extends clause can be used in a generic function to constrain a type parameter to a specific subset of types.  
  > We constrain the type parameter to that type by writing an extends clause:
- Constraining a generic type parameter to a shape does not allow returning an arbitrary object matching that constraint if the return type is typed as the parameter itself.  
  > The problem is that the function promises to return the same kind of object as was passed in, not just some object matching the constraint.
- The void type indicates the return type of functions that do not return a value, and it is automatically inferred when return statements return no explicit value or are absent.  
  > It’s the inferred type any time a function doesn’t have any return statements, or doesn’t return any explicit value from those return statements:
- The unknown type can hold any value, but unlike any, TypeScript does not allow operations to be performed on unknown values without narrowing.  
  > This is similar to the any type, but is safer because it’s not legal to do anything with an unknown value:
- The never return type signifies that a function never finishes normally, such as when throwing an exception or terminating the program.  
  > In a return type, this means that the function throws an exception or terminates execution of the program.
- A function that is contextually typed with a void return type is permitted to return a value, but that returned value is ignored.  
  > Contextual typing with a return type of void does not force functions to not return something. Another way to say this is a contextual function type with a void return type (type voidFunc = () => void), when implemented, can return any other value, but it will be ignored.
- A function defined literally with a void return type annotation is forbidden from returning any value.  
  > There is one other special case to be aware of, when a literal function definition has a void return type, that function must not return anything.

## [https://www.typescriptlang.org/docs/handbook/2/objects.html](https://www.typescriptlang.org/docs/handbook/2/objects.html)

official, fetched 2026-09-28

- Object types can be named using an interface declaration or a type alias.  
  > or they can be named by using either an interface:
ts
interface
Person
{
name
: string;
age
: number;
}
function
greet
(
person
:
Person
) {
return "Hello " +
person
.
name
;
}
Try
or a type alias:
ts
type
Person
= {
name
: string;
age
: number;
};
- Properties can be marked as optional by appending a question mark (?) to their names.  
  > In those cases, we can mark those properties as optional by adding a question mark (?) to the end of their names.
- When strictNullChecks is enabled, reading from an optional property will indicate that its value is potentially undefined.  
  > We can also read from those properties - but when we do under strictNullChecks, TypeScript will tell us they’re potentially undefined.
- Marking an object property with the readonly modifier prevents reassignment to that property during type-checking.  
  > While it won’t change any behavior at runtime, a property marked as readonly can’t be written to during type-checking.
- The readonly modifier prevents re-writing the property itself, but it does not make nested object contents immutable.  
  > Using the readonly modifier doesn’t necessarily imply that a value is totally immutable - or in other words, that its internal contents can’t be changed.
It just means the property itself can’t be re-written to.
- TypeScript does not consider readonly modifiers when evaluating compatibility between types, meaning readonly properties can change value via aliasing.  
  > TypeScript doesn’t factor in whether properties on two types are readonly when checking whether those types are compatible, so readonly properties can also change via aliasing.
- An interface can copy and build upon members of other types using the extends keyword.  
  > The extends keyword on an interface allows us to effectively copy members from other named types, and add whatever new members we want.
- An interface can extend multiple types simultaneously.  
  > interfaces can also extend from multiple types.
- Intersection types combine existing object types using the & operator.  
  > TypeScript provides another construct called intersection types that is mainly used to combine existing object types.
An intersection type is defined using the & operator.
- When intersecting types have conflicting property types, the conflicting property types are merged, which can result in the property having type never.  
  > In the case of intersection types, properties with different types will be merged automatically. When the type is used later, TypeScript will expect the property to satisfy both types simultaneously, which may produce unexpected results.
- Index signatures describe types of values when property names are not known ahead of time.  
  > Sometimes you don’t know all the names of a type’s properties ahead of time, but you do know the shape of the values.
In those cases you can use an index signature to describe the types of possible values
- Index signature properties can only be string, number, symbol, template string patterns, or union types consisting purely of these types.  
  > Only some types are allowed for index signature properties: string, number, symbol, template string patterns, and union types consisting only of these.
- When using both number and string index signatures, the type returned by the numeric indexer must be a subtype of the string indexer's return type.  
  > Note that when using both `number` and `string` indexers, the type returned from a numeric indexer must be a subtype of the type returned from the string indexer.
- A string index signature requires that all explicitly defined properties match the index signature's return type.  
  > While string index signatures are a powerful way to describe the “dictionary” pattern, they also enforce that all properties match their return type.
- Index signatures can be marked readonly to disallow assignment to indexed properties.  
  > Finally, you can make index signatures readonly in order to prevent assignment to their indices:
- Assigning an object literal with properties not present on the target type triggers an excess property checking error.  
  > Object literals get special treatment and undergo excess property checking when assigning them to other variables, or passing them as arguments.
If an object literal has any properties that the “target type” doesn’t have, you’ll get an error:
- Excess property checks on object literals can be bypassed using a type assertion.  
  > Getting around these checks is actually really simple.
The easiest method is to just use a type assertion:
ts
let
mySquare
=
createSquare
({
width
: 100,
opacity
: 0.5 } as
SquareConfig
);
- Adding a string index signature to an interface allows it to accept extra properties without triggering excess property check errors.  
  > However, a better approach might be to add a string index signature if you’re sure that the object can have some extra properties that are used in some special way.
- Assigning an object literal to an intermediate variable before passing it bypasses excess property checks, provided they share at least one common property.  
  > One final way to get around these checks, which might be a bit surprising, is to assign the object to another variable:
Since assigning squareOptions won’t undergo excess property checks, the compiler won’t give you an error:

## [https://www.typescriptlang.org/docs/handbook/2/modules.html](https://www.typescriptlang.org/docs/handbook/2/modules.html)

official, fetched 2026-09-28

- In TypeScript, any file with a top-level import or export declaration is treated as a module.  
  > In TypeScript, just as in ECMAScript 2015, any file containing a top-level import or export is considered a module.
- A file can specify its primary export using the 'export default' syntax.  
  > A file can declare a main export via export default:
- Variables, functions, and classes can be exported individually without the default keyword and imported using curly braces.  
  > In addition to the default export, you can have more than one export of variables and functions via the export by omitting default:
- Imported identifiers can be renamed using the 'as' keyword.  
  > An import can be renamed using a format like import {old as new}:
- Default and named imports can be combined in a single import statement.  
  > You can mix and match the above syntax into a single import:
ts
// @filename: maths.ts
export const
pi
= 3.14;
export default class
RandomNumberGenerator
{}
// @filename: app.ts
import
RandomNumberGenerator
, {
pi
as
π
} from "./maths.js";
- All exports from a module can be imported into a single namespace object using the '* as' syntax.  
  > You can take all of the exported objects and put them into a single namespace using * as name:
- TypeScript types and interfaces can be exported and imported using the standard ES Module syntax used for values.  
  > Types can be exported and imported using the same syntax as JavaScript values:
- An 'import type' declaration restricts the statement to only importing types.  
  > import type
Which is an import statement which can only import types:
- Using an identifier imported via 'import type' as a value causes a TypeScript compiler error.  
  > 'createCatName' cannot be used as a value because it was imported using 'import type'.
- Individual imports within a statement can be prefixed with 'type' to declare inline type imports.  
  > TypeScript 4.5 also allows for individual imports to be prefixed with type to indicate that the imported reference is a type:
- Type-only imports and inline type imports enable transpilers like Babel, swc, and esbuild to recognize which imports can be safely stripped.  
  > Together these allow a non-TypeScript transpiler like Babel, swc or esbuild to know what imports can be safely removed.

## [https://www.typescriptlang.org/tsconfig/](https://www.typescriptlang.org/tsconfig/)

official, fetched 2026-09-28

- When type annotations are missing and TypeScript cannot infer a variable's type, it defaults to type any.  
  > In some cases where no type annotations are present, TypeScript will fall back to a type of any for a variable when it cannot infer the type.
- Enabling the noImplicitAny compiler option causes TypeScript to issue an error whenever it would have defaulted to inferring any.  
  > Turning on noImplicitAny however TypeScript will issue an error whenever it would have inferred any:
- When strictNullChecks is disabled, null and undefined are effectively ignored by TypeScript's type system.  
  > When strictNullChecks is false, null and undefined are effectively ignored by the language.
- When strictNullChecks is enabled, null and undefined are treated as distinct types, causing type errors if they are used where a concrete value is expected.  
  > When strictNullChecks is true, null and undefined have their own distinct types and you’ll get a type error if you try to use them where a concrete value is expected.
- Enabling the strict flag activates all strict mode family options to enforce stronger guarantees of program correctness.  
  > The strict flag enables a wide range of type checking behavior that results in stronger guarantees of program correctness.
Turning this on is equivalent to enabling all of the strict mode family options, which are outlined below.
- Even with the strict flag enabled, individual strict mode family checks can be turned off independently as needed.  
  > You can then turn off individual strict mode family checks as needed.

## [https://www.typescriptlang.org/docs/handbook/compiler-options.html](https://www.typescriptlang.org/docs/handbook/compiler-options.html)

official, fetched 2026-09-28

- Invoking tsc locally without arguments compiles the nearest project defined by a tsconfig.json file.  
  > Running tsc locally will compile the closest project defined by a tsconfig.json, or you can compile a set of TypeScript
files by passing in a glob of files you want.
- Passing input files directly on the command line causes tsc to ignore tsconfig.json configuration files.  
  > When input files are specified on the command line, tsconfig.json files are
ignored.
- The --noEmitOnError compiler flag suppresses output file emission whenever type checking errors are reported.  
  > Disable emitting files if any type checking errors are reported.
- The --noImplicitAny compiler option triggers error reporting for expressions and declarations that have an implied any type.  
  > Enable error reporting for expressions and declarations with an implied any type.
- The --noImplicitAny option defaults to true when strict mode is active, and false otherwise.  
  > true if strict; false otherwise.
- The --strictNullChecks flag ensures null and undefined are considered during type checking.  
  > When type checking, take into account null and undefined.
- The --strict flag enables all strict type-checking options at once.  
  > Enable all strict type-checking options.
- The --target compiler flag specifies the JavaScript language version for emitted JavaScript and includes corresponding compatible library declarations.  
  > Set the JavaScript language version for emitted JavaScript and include compatible library declarations.

## [https://www.typescriptlang.org/docs/handbook/tsconfig-json.html](https://www.typescriptlang.org/docs/handbook/tsconfig-json.html)

official, fetched 2026-09-28

- A tsconfig.json file designates the root files and compiler options needed to compile a TypeScript project.  
  > The tsconfig.json file specifies the root files and the compiler options required to compile the project.
- Invoking tsc without specifying input files prompts the compiler to search for tsconfig.json starting in the current directory and continuing up through parent directories.  
  > By invoking tsc with no input files, in which case the compiler searches for the tsconfig.json file starting in the current directory and continuing up the parent directory chain.
- Invoking tsc with the --project or -p flag and no input files compiles using the tsconfig.json file in a specified directory or a specific configuration json file.  
  > By invoking tsc with no input files and a --project (or just -p) command line option that specifies the path of a directory containing a tsconfig.json file, or a path to a valid .json file containing the configurations.
- Specifying input files directly on the command line causes tsc to ignore tsconfig.json files.  
  > When input files are specified on the command line, tsconfig.json files are ignored.
- If the compilerOptions setting is omitted, TypeScript applies the compiler default values.  
  > The "compilerOptions" property can be omitted, in which case the compiler’s defaults are used.

## [https://www.typescriptlang.org/docs/handbook/interfaces.html](https://www.typescriptlang.org/docs/handbook/interfaces.html)

official, fetched 2026-09-28

- In TypeScript, interfaces fill the role of naming types and defining contracts within code as well as with external code.  
  > In TypeScript, interfaces fill the role of naming these types, and are a powerful way of defining contracts within your code as well as contracts with code outside of your project.
- The type checker does not require properties in an interface to match any specific order, as long as the required properties are present and match their required types.  
  > It’s worth pointing out that the type checker does not require that these properties come in any sort of order, only that the properties the interface requires are present and have the required type.
- Optional properties on an interface are declared by placing a ? at the end of the property name.  
  > Interfaces with optional properties are written similar to other interfaces, with each optional property denoted by a ? at the end of the property name in the declaration.
- The const keyword is used for immutable variables, whereas readonly is used for immutable properties.  
  > Variables use const whereas properties use readonly.
- Object literals undergo excess property checking when assigned to variables or passed as arguments, producing an error if they contain properties absent from the target type.  
  > Object literals get special treatment and undergo excess property checking when assigning them to other variables, or passing them as arguments.
If an object literal has any properties that the “target type” doesn’t have, you’ll get an error
- Adding a string index signature to an interface allows an object to include arbitrary extra properties without triggering excess property check errors.  
  > However, a better approach might be to add a string index signature if you’re sure that the object can have some extra properties that are used in some special way.
- Assigning an object literal to an intermediate variable bypasses excess property checks when passing it to a function, provided there is at least one common property with the target type.  
  > Since squareOptions won’t undergo excess property checks, the compiler won’t give you an error.
- Supported index signature types in TypeScript include string, number, symbol, and template strings.  
  > There are four types of supported index signatures: string, number, symbol and template strings.
- When both numeric and string indexers are used, the return type of the numeric indexer must be a subtype of the type returned by the string indexer.  
  > It is possible to support many types of indexers, but the type returned from a numeric indexer must be a subtype of the type returned from the string indexer.
- A string index signature requires that all explicitly defined properties in the interface have types compatible with the index signature's return type.  
  > While string index signatures are a powerful way to describe the “dictionary” pattern, they also enforce that all properties match their return type.
- Interfaces can extend other interfaces using the extends keyword to copy members and compose shapes into reusable components.  
  > Like classes, interfaces can extend each other.
This allows you to copy the members of one interface into another, which gives you more flexibility in how you separate your interfaces into reusable components.

## [https://www.typescriptlang.org/docs/handbook/2/generics.html](https://www.typescriptlang.org/docs/handbook/2/generics.html)

official, fetched 2026-09-28

- A generic type parameter constraint can be defined by using an interface along with the extends keyword on the type variable.  
  > Here, we’ll create an interface that has a single .length property and then we’ll use this interface and the extends keyword to denote our constraint:
- A type parameter can be constrained by another type parameter, such as ensuring a key exists on an object type using extends keyof.  
  > You can declare a type parameter that is constrained by another type parameter.
- When calling a generic function, the TypeScript compiler can automatically infer the type argument based on the argument passed in.  
  > Here we use type argument inference — that is, we want the compiler to set the value of Type for us automatically based on the type of the argument we pass in:
- Generic type parameter defaults must satisfy any constraint specified on that type parameter.  
  > Default types for a type parameter must satisfy the constraint for the type parameter, if it exists.
- The type of a generic function lists the type parameters first, followed by parameter and return types.  
  > The type of generic functions is just like those of non-generic functions, with the type parameters listed first, similarly to function declarations:
- A generic parameter can be moved to the whole interface so that it is visible to all members and locked in when the interface type argument is specified.  
  > This makes the type parameter visible to all the other members of the interface.

## [https://www.typescriptlang.org/docs/handbook/modules/reference.html](https://www.typescriptlang.org/docs/handbook/modules/reference.html)

official, fetched 2026-09-28

- Type aliases, interfaces, enums, and namespaces can be exported using an export modifier or referenced alongside JavaScript declarations in named export lists.  
  > Type aliases, interfaces, enums, and namespaces can be exported from a module with an export modifier, like any standard JavaScript declaration:
- Exported types and other TypeScript declarations can be imported using standard ECMAScript import syntax.  
  > Exported types (and other TypeScript-specific declarations) can be imported with standard ECMAScript imports:
- When using namespace imports or exports, exported types can be accessed on the namespace when used in a type position.  
  > When using namespace imports or exports, exported types are available on the namespace when referenced in a type position:
- Import declarations using `import type`, exports using `export type { ... }`, and individual specifiers prefixed with `type` are guaranteed to be elided from compiled JavaScript.  
  > Import declarations written with import type, export declarations written with export type { ... }, and import or export specifiers prefixed with the type keyword are all guaranteed to be elided from the output JavaScript.
- Values can be imported with `import type`, but because they will not exist in emitted JavaScript, they can only be referenced in non-emitting type positions.  
  > Even values can be imported with import type, but since they won’t exist in the output JavaScript, they can only be used in non-emitting positions:
- A type-only import declaration cannot specify both a default import and named bindings together because of ambiguity over what the `type` keyword modifies.  
  > A type-only import declaration may not declare both a default import and named bindings, since it appears ambiguous whether type applies to the default import or to the entire import declaration.

## [https://www.typescriptlang.org/docs/handbook/modules/theory.html](https://www.typescriptlang.org/docs/handbook/modules/theory.html)

official, fetched 2026-09-28

- ECMAScript Modules are built into JavaScript and provide dedicated import and export syntax to share code across files.  
  > ECMAScript Modules (ESM) is the module system built into the language, supported in modern browsers and in Node.js since v12. It uses dedicated import and export syntax:
- In ES Module syntax, a module can define a default export using the export default keywords.  
  > export default "Hello from a.js";
- Specific named bindings can be imported from an ES Module using curly braces enclosing the binding name.  
  > import { sayHello } from "greetings";
- A module can re-export all exports from another module using the export * from syntax.  
  > export * from "./utils.js";
