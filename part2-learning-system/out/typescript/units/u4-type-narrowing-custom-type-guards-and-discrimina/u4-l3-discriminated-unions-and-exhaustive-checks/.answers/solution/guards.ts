export interface User {
  id: number;
  name: string;
}

export interface Post {
  id: number;
  title: string;
  authorId: number;
}

export function isUser(data: unknown): data is User {
  if (typeof data === "object" && data !== null && "id" in data && "name" in data) {
    return typeof data.id === "number" && typeof data.name === "string";
  }
  return false;
}

export function isPost(data: unknown): data is Post {
  if (
    typeof data === "object" &&
    data !== null &&
    "id" in data &&
    "title" in data &&
    "authorId" in data
  ) {
    return (
      typeof data.id === "number" &&
      typeof data.title === "string" &&
      typeof data.authorId === "number"
    );
  }
  return false;
}
