import test from "node:test";
import assert from "node:assert/strict";
import { parseScore, formatGreeting } from "./formatter.ts";

test("parseScore parses valid integer strings", () => {
  assert.equal(parseScore("42"), 42, "parseScore('42') should return 42");
  assert.equal(parseScore("-7"), -7, "parseScore('-7') should return -7");
});

test("parseScore returns 0 for non-numeric strings", () => {
  assert.equal(parseScore("abc"), 0, "parseScore('abc') should return 0 instead of NaN");
  assert.equal(parseScore(""), 0, "parseScore('') should return 0 instead of NaN");
});

test("formatGreeting returns greeting for valid name", () => {
  assert.equal(formatGreeting("Alice"), "Hello, Alice!", "formatGreeting('Alice') should greet Alice");
  assert.equal(formatGreeting("  Bob  "), "Hello, Bob!", "formatGreeting should trim whitespace");
});

test("formatGreeting handles null and undefined safely", () => {
  assert.equal(formatGreeting(null), "Hello, guest!", "formatGreeting(null) should return fallback guest greeting");
  assert.equal(formatGreeting(undefined), "Hello, guest!", "formatGreeting(undefined) should return fallback guest greeting");
});
