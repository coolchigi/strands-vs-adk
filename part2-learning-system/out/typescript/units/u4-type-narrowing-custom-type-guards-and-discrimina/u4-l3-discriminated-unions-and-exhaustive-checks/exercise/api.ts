export interface LoadingResponse {
  status: "loading";
}

export interface SuccessResponse<T> {
  // TODO: Add discriminant property 'status' with literal "success", and property 'data' of type T
  status: "pending";
  data?: T;
}

export interface ErrorResponse {
  // TODO: Add discriminant property 'status' with literal "error", and property 'error' of type string
  status: "failed";
  error?: string;
}

export type ApiResponse<T> = LoadingResponse | SuccessResponse<T> | ErrorResponse;

export function formatResponse<T>(response: ApiResponse<T>): string {
  // TODO: Switch on response.status to handle "loading", "success", and "error".
  // In the default branch, assign response to a const typed as never for exhaustive checking.
  return "";
}
