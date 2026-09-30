export function fail(message: string): never {
  throw new Error(message);
}

export function parsePayload(raw: unknown): string {
  if (typeof raw === "string") {
    return raw;
  }
  return JSON.stringify(raw);
}

export function logResponse(message: string, logger: (msg: string) => void): void {
  logger(message);
}

export async function fetchStatus(endpoint: string): Promise<number> {
  if (!endpoint.startsWith("/")) {
    fail("Invalid endpoint");
  }
  return 200;
}
