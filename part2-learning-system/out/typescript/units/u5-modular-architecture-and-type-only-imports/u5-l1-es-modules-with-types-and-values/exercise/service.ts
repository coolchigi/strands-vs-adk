import type { User } from "./guards.ts";
import { isUser } from "./guards.ts";
import type { ApiResponse } from "./api.ts";
import { formatResponse } from "./api.ts";

export interface ServiceResult {
  formatted: string;
  valid: boolean;
}

// TODO: Implement renderUserResponse so it returns valid: true only if response.status is "success" and isUser(response.data) is true, and formatted as formatResponse(response).
export default function renderUserResponse(_response: ApiResponse<User>): ServiceResult {
  return { formatted: "", valid: false };
}
