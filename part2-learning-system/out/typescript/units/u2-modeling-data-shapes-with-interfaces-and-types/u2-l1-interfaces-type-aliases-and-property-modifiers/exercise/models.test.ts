import test from "node:test";
import assert from "node:assert/strict";
import { formatUserProfile, formatPostPreview, type User, type Post } from "./models.ts";

test("User interface supports required and optional properties and enforces readonly id", () => {
  const userWithBio: User = {
    id: 1,
    username: "alice",
    email: "alice@example.com",
    bio: "Full-stack developer",
    avatarUrl: "https://example.com/alice.png",
  };

  const userWithoutBio: User = {
    id: 2,
    username: "bob",
    email: "bob@example.com",
  };

  assert.strictEqual(
    formatUserProfile(userWithBio),
    "alice (alice@example.com): Full-stack developer",
    "formatUserProfile should format profile with bio"
  );

  assert.strictEqual(
    formatUserProfile(userWithoutBio),
    "bob (bob@example.com)",
    "formatUserProfile should format profile without bio"
  );

  function _typeCheckUser(u: User): void {
    // @ts-expect-error id property is readonly on User
    u.id = 999;
  }
});

test("Post type alias enforces readonly properties and required fields", () => {
  const post: Post = {
    id: 101,
    authorId: 1,
    title: "TypeScript Overview",
    content: "Interfaces and type aliases define application data shapes.",
  };

  assert.strictEqual(
    formatPostPreview(post),
    "[Post #101 by 1] TypeScript Overview",
    "formatPostPreview should format post preview header"
  );

  function _typeCheckPost(p: Post): void {
    // @ts-expect-error id property is readonly on Post
    p.id = 999;
    // @ts-expect-error authorId property is readonly on Post
    p.authorId = 888;
  }
});
