import test from "node:test";
import assert from "node:assert/strict";
import { fail, parsePayload, logResponse, fetchStatus } from "./client.ts";

type AssertNever<T extends never> = T;
type _FailCheck = AssertNever<ReturnType<typeof fail>>;

type AssertPromiseNumber<T extends Promise<number>> = T;
type _FetchCheck = AssertPromiseNumber<ReturnType<typeof fetchStatus>>;

test("fail throws an Error with the given message", () => {
  assert.throws(
    () => fail("network timeout"),
    { message: "network timeout" },
    "fail should throw an Error with the specified message"
  );
});

test("parsePayload accepts unknown data and returns string", () => {
  assert.equal(parsePayload("ready"), "ready", "string payload should be returned as-is");
  assert.equal(parsePayload({ code: 1 }), '{"code":1}', "non-string payload should be stringified");
  assert.equal(parsePayload(42), "42", "number payload should be stringified");
});

test("logResponse executes the void callback with the message", () => {
  const logs: string[] = [];
  logResponse("event received", (msg: string): void => {
    logs.push(msg);
  });
  assert.deepEqual(logs, ["event received"], "logResponse should invoke the logger callback with the message");
});

test("fetchStatus returns 200 for a valid endpoint", async () => {
  const result = await fetchStatus("/health");
  assert.equal(result, 200, "fetchStatus should return status code 200");
});

test("fetchStatus rejects when endpoint does not start with /", async () => {
  await assert.rejects(
    async () => {
      await fetchStatus("invalid");
    },
    { message: "Invalid endpoint" },
    "fetchStatus should throw an error via fail for invalid endpoints"
  );
});
