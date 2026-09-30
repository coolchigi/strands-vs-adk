export interface Timestamped {
  createdAt: Date;
  updatedAt: Date;
}

export interface User extends Timestamped {
  readonly id: number;
  username: string;
  email: string;
  bio?: string;
  avatarUrl?: string;
}

export interface Post extends Timestamped {
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

export type AdminRole = Permission & AuditDetails;

export type ConflictingId = { id: string } & { id: number };
export type ConflictCheck = ConflictingId['id'];

export function createAuditedUser(
  user: User,
  admin: AdminRole
): User & AdminRole {
  return { ...user, ...admin };
}
