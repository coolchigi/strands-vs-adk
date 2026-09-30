// TODO: annotate parameter 'input' as string and return 0 if Number.parseInt returns NaN
export function parseScore(input): number {
  return Number.parseInt(input, 10);
}

// TODO: handle null and undefined explicitly; return 'Hello, guest!' when name is null or undefined, or 'Hello, ' + name.trim() + '!'
export function formatGreeting(name: string | null | undefined): string {
  return "Hello, " + name.trim() + "!";
}
