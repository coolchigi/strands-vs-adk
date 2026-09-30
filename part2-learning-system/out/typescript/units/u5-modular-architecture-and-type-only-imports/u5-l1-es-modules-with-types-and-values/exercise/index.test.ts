import test from "node:test";
import assert from "node:assert/strict";
import type { User, ApiResponse, ServiceResult } from "./index.ts";
import * as index from "./index.ts";
import renderUserResponse from "./service.ts";

test("service.ts default export formats and validates correctly", () => {
  const userResponse: ApiResponse<User> = {
    status: "success",
    data: { id: 1, name: "Alice" },
  };
  const result = renderUserResponse(userResponse);
  assert.equal(
    result.formatted,
    'Data: {"id":1,"name":"Alice"}',
    "renderUserResponse must format response using formatResponse"
  );
  assert.equal(
    result.valid,
    true,
    "renderUserResponse must set valid to true for valid user data"
  );
});

test("service.ts default export marks invalid user data as invalid", () => {
  const invalidResponse: ApiResponse<User> = {
    status: "success",
    data: { id: 1 } as unknown as User,
  };
  const result = renderUserResponse(invalidResponse);
  assert.equal(
    result.valid,
    false,
    "renderUserResponse must set valid to false when isUser check fails"
  );
});

test("index.ts re-exports isUser and isPost from guards.ts", () => {
  assert.equal(
    typeof (index as Record<string, unknown>).isUser,
    "function",
    "isUser should be re-exported from index.ts using wildcard re-export"
  );
  assert.equal(
    typeof (index as Record<string, unknown>).isPost,
    "function",
    "isPost should be re-exported from index.ts using wildcard re-export"
  );
});

test("index.ts re-exports formatResponse from api.ts", () => {
  assert.equal(
    typeof (index as Record<string, unknown>).formatResponse,
    "function",
    "formatResponse should be re-exported from index.ts using wildcard re-export"
  );
});

test("index.ts re-exports default export from service.ts", () => {
  assert.equal(
    typeof index.default,
    "function",
    "index.ts must re-export the default export from service.ts"
  );
  const response: ApiResponse<User> = {
    status: "success",
    data: { id: 2, name: "Bob" },
  };
  const fn = index.default as (res: ApiResponse<User>) => ServiceResult;
  const result = fn(response);
  assert.deepEqual(
    result,
    { formatted: 'Data: {"id":2,"name":"Bob"}', valid: true },
    "Re-exported default function should format and validate response"
  );
});
