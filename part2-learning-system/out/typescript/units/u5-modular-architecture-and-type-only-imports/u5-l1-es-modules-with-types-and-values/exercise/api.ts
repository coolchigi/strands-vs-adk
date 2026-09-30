export interface LoadingResponse {
  status: "loading";
}

export interface SuccessResponse<T> {
  status: "success";
  data: T;
}

export interface ErrorResponse {
  status: "error";
  error: string;
}

export type ApiResponse<T> = LoadingResponse | SuccessResponse<T> | ErrorResponse;

export function formatResponse<T>(response: ApiResponse<T>): string {
  switch (response.status) {
    case "loading":
      return "Loading...";
    case "success":
      return `Data: ${JSON.stringify(response.data)}`;
    case "error":
      return `Error: ${response.error}`;
    default: {
      const _exhaustiveCheck: never = response;
      return _exhaustiveCheck;
    }
  }
}
