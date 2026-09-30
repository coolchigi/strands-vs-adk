import type { ApiResponse } from "./api.ts";
import { formatResponse } from "./api.ts";
// TODO: Fix the import from ./guards.ts so runtime guard functions isUser and isPost are imported as values,
// while entity interfaces User and Post are imported as inline types.
import { isUser, type User, type isPost, type Post } from "./guards.ts";

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
  // TODO: Validate that response.status is "success" and isPost(response.data), and format using formatResponse
  const valid = response.status === "success" && isPost(response.data);
  return {
    formatted: "",
    valid,
  };
}
