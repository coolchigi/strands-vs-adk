export function formatPayload(payload: string | number | string[] | null): string {
  if (payload === null) {
    return "none";
  }
  if (typeof payload === "number") {
    return payload.toFixed(2);
  }
  if (typeof payload === "string") {
    if (!payload) {
      return "empty string";
    }
    return payload.trim();
  }
  return payload.join(", ");
}

export function extractData(response: { error: string } | { data: string }): string {
  if ("error" in response) {
    return "Error: " + response.error;
  }
  return response.data;
}
