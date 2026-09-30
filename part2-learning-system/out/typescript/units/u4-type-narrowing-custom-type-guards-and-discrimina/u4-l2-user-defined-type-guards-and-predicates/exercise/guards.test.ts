import test from "node:test";
import assert from "node:assert/strict";
import { isUser, isPost } from "./guards.ts";
import type { User, Post } from "./guards.ts";

test("isUser validates valid user and enables type narrowing", () => {
  const payload: unknown = { id: 1, name: "Alice" };
  assert.equal(isUser(payload), true, "isUser should return true for valid User");
  if (isUser(payload)) {
    const user: User = payload;
    assert.equal(user.name, "Alice", "narrowed user name should match");
    assert.equal(user.id, 1, "narrowed user id should match");
  } else {
    assert.fail("payload should have been narrowed to User");
  }
});

test("isUser rejects invalid user payloads", () => {
  assert.equal(isUser(null), false, "isUser should reject null");
  assert.equal(isUser("user"), false, "isUser should reject primitives");
  assert.equal(isUser({ id: "1", name: "Alice" }), false, "isUser should reject non-number id");
  assert.equal(isUser({ id: 1 }), false, "isUser should reject missing name");
  assert.equal(isUser({ id: 1, name: 42 }), false, "isUser should reject non-string name");
});

test("isPost validates valid post and enables type narrowing", () => {
  const payload: unknown = { id: 10, title: "Hello World", authorId: 1 };
  assert.equal(isPost(payload), true, "isPost should return true for valid Post");
  if (isPost(payload)) {
    const post: Post = payload;
    assert.equal(post.title, "Hello World", "narrowed post title should match");
    assert.equal(post.authorId, 1, "narrowed post authorId should match");
  } else {
    assert.fail("payload should have been narrowed to Post");
  }
});

test("isPost rejects invalid post payloads", () => {
  assert.equal(isPost(null), false, "isPost should reject null");
  assert.equal(isPost(123), false, "isPost should reject number");
  assert.equal(isPost({ id: 10, title: "Hello" }), false, "isPost should reject missing authorId");
  assert.equal(isPost({ id: 10, title: 100, authorId: 1 }), false, "isPost should reject non-string title");
  assert.equal(isPost({ id: "10", title: "Hello", authorId: 1 }), false, "isPost should reject non-number id");
});
