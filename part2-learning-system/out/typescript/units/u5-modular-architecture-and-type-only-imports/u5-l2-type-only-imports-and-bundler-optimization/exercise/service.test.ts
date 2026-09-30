import test from "node:test";
import assert from "node:assert/strict";
import renderUserResponse, { renderPostResponse } from "./service.ts";
import type { ApiResponse } from "./api.ts";
import type { User, Post } from "./guards.ts";

test("renderUserResponse formats and validates user data", () => {
  const userResponse: ApiResponse<User> = {
    status: "success",
    data: { id: 1, name: "Alice" },
  };
  const result = renderUserResponse(userResponse);
  assert.strictEqual(result.valid, true, "User response should be valid");
  assert.strictEqual(
    result.formatted,
    'Data: {"id":1,"name":"Alice"}',
    "User response should be formatted"
  );
});

test("renderPostResponse formats and validates post data", () => {
  const postResponse: ApiResponse<Post> = {
    status: "success",
    data: { id: 101, title: "TypeScript Imports", authorId: 1 },
  };
  const result = renderPostResponse(postResponse);
  assert.strictEqual(result.valid, true, "Post response should be valid");
  assert.strictEqual(
    result.formatted,
    'Data: {"id":101,"title":"TypeScript Imports","authorId":1}',
    "Post response should be formatted"
  );
});

test("renderPostResponse handles error responses", () => {
  const errorResponse: ApiResponse<Post> = {
    status: "error",
    error: "Post not found",
  };
  const result = renderPostResponse(errorResponse);
  assert.strictEqual(result.valid, false, "Error response should not be valid");
  assert.strictEqual(
    result.formatted,
    "Error: Post not found",
    "Error response should be formatted"
  );
});
