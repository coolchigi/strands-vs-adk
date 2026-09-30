import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { formatResponse } from "./api.ts";
import type { ApiResponse } from "./api.ts";

test("formatResponse handles loading status", () => {
  const loading: ApiResponse<number> = { status: "loading" };
  assert.equal(formatResponse(loading), "Loading...");
});

test("formatResponse handles success status", () => {
  const success: ApiResponse<{ id: number }> = {
    status: "success",
    data: { id: 42 },
  };
  assert.equal(formatResponse(success), 'Data: {"id":42}');
});

test("formatResponse handles error status", () => {
  const error: ApiResponse<unknown> = {
    status: "error",
    error: "Network failure",
  };
  assert.equal(formatResponse(error), "Error: Network failure");
});

test("default branch enforces exhaustive check using never", () => {
  const source = fs.readFileSync(new URL("./api.ts", import.meta.url), "utf-8");
  assert.match(
    source,
    /const\s+\w+\s*:\s*never\s*=\s*\w+;?/, 
    "The default case must assign the unhandled response to a const typed as never"
  );
});
