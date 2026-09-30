import type { User } from "./guards.ts";
import { isUser } from "./guards.ts";
import type { ApiResponse } from "./api.ts";
import { formatResponse } from "./api.ts";

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
