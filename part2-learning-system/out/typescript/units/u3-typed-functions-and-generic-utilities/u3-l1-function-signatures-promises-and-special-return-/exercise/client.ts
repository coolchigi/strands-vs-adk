// TODO: Annotate return type as never, and throw an Error with message
export function fail(message: string): void {
}

// TODO: Annotate raw as unknown. If typeof raw is string return raw, otherwise return JSON.stringify(raw)
export function parsePayload(raw: string): string {
  return raw;
}

// TODO: Annotate logger callback type as (msg: string) => void and return type as void. Invoke logger with message.
export function logResponse(message: string, logger: () => void): void {
}

// TODO: Annotate return type as Promise<number>. If endpoint does not start with "/", call fail("Invalid endpoint"); otherwise return 200.
export async function fetchStatus(endpoint: string): Promise<void> {
}
