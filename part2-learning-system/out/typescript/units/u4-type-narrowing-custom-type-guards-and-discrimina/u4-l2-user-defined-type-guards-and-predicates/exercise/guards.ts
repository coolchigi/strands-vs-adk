export interface User {
  id: number;
  name: string;
}

export interface Post {
  id: number;
  title: string;
  authorId: number;
}

export function isUser(data: unknown): boolean {
  // TODO: annotate return type as `data is User` and return true if data has a numeric id and string name
  return false;
}

export function isPost(data: unknown): boolean {
  // TODO: annotate return type as `data is Post` and return true if data has a numeric id, string title, and numeric authorId
  return false;
}
