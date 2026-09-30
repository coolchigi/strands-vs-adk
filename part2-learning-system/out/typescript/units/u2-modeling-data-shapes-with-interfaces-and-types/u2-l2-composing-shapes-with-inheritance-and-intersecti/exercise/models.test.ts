import test from 'node:test';
import assert from 'node:assert/strict';
import type { Timestamped, User, Post, AdminRole, ConflictCheck } from './models.ts';
import { createAuditedUser } from './models.ts';

test('User and Post shapes satisfy Timestamped', () => {
  const now = new Date();
  const user: User = {
    id: 1,
    username: 'alex',
    email: 'alex@example.com',
    createdAt: now,
    updatedAt: now,
  };

  const timestampedUser: Timestamped = user;
  assert.equal(timestampedUser.createdAt, now, 'User must satisfy Timestamped createdAt');
  assert.equal(timestampedUser.updatedAt, now, 'User must satisfy Timestamped updatedAt');

  const post: Post = {
    id: 101,
    authorId: 1,
    title: 'First Post',
    content: 'Hello World',
    createdAt: now,
    updatedAt: now,
  };

  const timestampedPost: Timestamped = post;
  assert.equal(timestampedPost.createdAt, now, 'Post must satisfy Timestamped createdAt');
});

test('createAuditedUser combines User and AdminRole intersection', () => {
  const now = new Date();
  const user: User = {
    id: 2,
    username: 'admin_sam',
    email: 'sam@example.com',
    createdAt: now,
    updatedAt: now,
  };

  const admin: AdminRole = {
    role: 'administrator',
    canDelete: true,
    lastLogin: now,
  };

  const audited = createAuditedUser(user, admin);
  assert.equal(audited.username, 'admin_sam', 'Audited user must have User properties');
  assert.equal(audited.role, 'administrator', 'Audited user must have Permission role');
  assert.equal(audited.canDelete, true, 'Audited user must have Permission canDelete');
  assert.equal(audited.lastLogin, now, 'Audited user must have AuditDetails lastLogin');
});

test('conflicting property types produce never', () => {
  // Verifies at compile time that ConflictCheck is never
  type IsNever<T> = [T] extends [never] ? true : false;
  const isConflictNever: IsNever<ConflictCheck> = true;
  assert.equal(isConflictNever, true, 'Conflicting id property should be of type never');
});
