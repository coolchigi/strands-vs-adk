import type { ApiResponse } from "./api.ts";
import { formatResponse } from "./api.ts";
import { isUser, type User, isPost, type Post } from "./guards.ts";

export interface ServiceResult {
  formatted: string;
  valid: boolean;
}

export default function renderUserResponse(response: ApiResponse<User>): ServiceResult {
  const valid = response.status === "success" && isUser(response.data);
  return {
    formatted: formatResponse(response),
    valid,
  };
}

export function renderPostResponse(response: ApiResponse<Post>): ServiceResult {
  const valid = response.status === "success" && isPost(response.data);
  return {
    formatted: formatResponse(response),
    valid,
  };
}
