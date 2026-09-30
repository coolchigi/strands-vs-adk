import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

test("tsconfig.json exists and has valid compilerOptions", () => {
  const raw = readFileSync("tsconfig.json", "utf8");
  const config = JSON.parse(raw);
  assert.ok(config && typeof config === "object", "tsconfig.json must contain a JSON object");
  assert.ok(config.compilerOptions && typeof config.compilerOptions === "object", "tsconfig.json must include a compilerOptions object");
});

test("target compiler option is configured to es2015 for downleveling", () => {
  const raw = readFileSync("tsconfig.json", "utf8");
  const config = JSON.parse(raw);
  assert.equal(
    config.compilerOptions?.target?.toLowerCase(),
    "es2015",
    "compilerOptions.target must be set to 'es2015' to downlevel JavaScript output to ECMAScript 2015"
  );
});

test("strict mode is enabled in compilerOptions", () => {
  const raw = readFileSync("tsconfig.json", "utf8");
  const config = JSON.parse(raw);
  assert.equal(
    config.compilerOptions?.strict,
    true,
    "compilerOptions.strict must be true to activate all strict mode type-checking checks"
  );
});
