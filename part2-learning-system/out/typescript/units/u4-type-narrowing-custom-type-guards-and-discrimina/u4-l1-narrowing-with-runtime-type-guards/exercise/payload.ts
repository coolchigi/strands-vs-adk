export function formatPayload(payload: string | number | string[] | null): string {
  // TODO: Check if payload is null with === null and return "none"
  // TODO: Narrow payload using typeof for "number" and return payload.toFixed(2)
  // TODO: Narrow payload using typeof for "string" and truthiness check (!payload -> "empty string", else payload.trim())
  // TODO: Return joined array elements for string[]
  return "";
}

export function extractData(response: { error: string } | { data: string }): string {
  // TODO: Narrow using 'error' in response to return "Error: " + response.error, else response.data
  return "";
}
