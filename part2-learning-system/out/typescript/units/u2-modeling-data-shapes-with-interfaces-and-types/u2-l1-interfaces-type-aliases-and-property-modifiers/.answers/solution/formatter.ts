export function parseScore(input: string): number {
  const parsed = Number.parseInt(input, 10);
  return Number.isNaN(parsed) ? 0 : parsed;
}

export function formatGreeting(name: string | null | undefined): string {
  if (name === null || name === undefined) {
    return "Hello, guest!";
  }
  return "Hello, " + name.trim() + "!";
}
