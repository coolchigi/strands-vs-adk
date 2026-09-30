export interface Identifiable {
  id: string;
}

// TODO: Constrain T to Identifiable: EntityStore<T extends Identifiable>
export interface EntityStore<T = any> {
  items: T[];
  findById(id: string): T | undefined;
}

// TODO: Write updateRecord with type parameter T constrained to Identifiable:
// <T extends Identifiable>(record: T): T
export function updateRecord(record: any): any {
  return undefined;
}

// TODO: Write getProperty with type parameters <T, K extends keyof T>(item: T, key: K): T[K]
export function getProperty(item: any, key: any): any {
  return undefined;
}
