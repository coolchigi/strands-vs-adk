export interface User {
  readonly id: number;
  username: string;
  email: string;
  bio?: string;
  avatarUrl?: string;
}

export type Post = {
  readonly id: number;
  readonly authorId: number;
  title: string;
  content: string;
};

export function formatUserProfile(user: User): string {
  if (user.bio !== undefined) {
    return `${user.username} (${user.email}): ${user.bio}`;
  }
  return `${user.username} (${user.email})`;
}

export function formatPostPreview(post: Post): string {
  return `[Post #${post.id} by ${post.authorId}] ${post.title}`;
}
