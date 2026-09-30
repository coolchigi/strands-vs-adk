import test from "node:test";
import assert from "node:assert/strict";
import { formatPayload, extractData } from "./payload.ts";

test("formatPayload formats null correctly", () => {
  assert.equal(formatPayload(null), "none", "null should format as 'none'");
});

test("formatPayload formats numbers with two decimal places", () => {
  assert.equal(formatPayload(42), "42.00", "42 should format as '42.00'");
  assert.equal(formatPayload(3.14159), "3.14", "3.14159 should format as '3.14'");
});

test("formatPayload formats strings with truthiness handling", () => {
  assert.equal(formatPayload(""), "empty string", "empty string should format as 'empty string'");
  assert.equal(formatPayload("  hello  "), "hello", "strings should be trimmed");
});

test("formatPayload formats string arrays", () => {
  assert.equal(formatPayload(["alpha", "beta"]), "alpha, beta", "arrays should be joined with ', '");
});

test("extractData narrows using the in operator", () => {
  assert.equal(extractData({ error: "Not found" }), "Error: Not found", "should format error response");
  assert.equal(extractData({ data: "User data" }), "User data", "should return data directly");
});
