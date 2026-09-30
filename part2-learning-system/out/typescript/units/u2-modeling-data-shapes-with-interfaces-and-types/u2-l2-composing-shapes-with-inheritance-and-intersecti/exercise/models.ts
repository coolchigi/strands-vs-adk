// TODO: Export interface Timestamped with createdAt: Date and updatedAt: Date

export interface User {
  // TODO: Extend Timestamped on User
  readonly id: number;
  username: string;
  email: string;
  bio?: string;
  avatarUrl?: string;
}

export interface Post {
  // TODO: Extend Timestamped on Post
  readonly id: number;
  readonly authorId: number;
  title: string;
  content: string;
}

export type Permission = {
  role: string;
  canDelete: boolean;
};

export type AuditDetails = {
  lastLogin: Date;
};

// TODO: Export type AdminRole as intersection of Permission and AuditDetails

// TODO: Export type ConflictingId as { id: string } & { id: number }
// TODO: Export type ConflictCheck as ConflictingId['id']

export function createAuditedUser(
  user: User,
  admin: AdminRole
): User & AdminRole {
  // TODO: Return a merged object containing user and admin properties
  return { ...user, ...admin };
}
