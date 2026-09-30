export interface User {
  // TODO: declare readonly id: number, username: string, email: string, optional bio?: string, and optional avatarUrl?: string
  id: number;
  username: string;
  email: string;
  bio: string;
  avatarUrl: string;
}

export type Post = {
  // TODO: declare readonly id: number, readonly authorId: number, title: string, and content: string
  id: number;
  authorId: number;
  title: string;
  content: string;
};

export function formatUserProfile(user: User): string {
  // TODO: return "<username> (<email>): <bio>" when bio is defined, or "<username> (<email>)" when omitted
  return "";
}

export function formatPostPreview(post: Post): string {
  // TODO: return "[Post #<id> by <authorId>] <title>"
  return "";
}
