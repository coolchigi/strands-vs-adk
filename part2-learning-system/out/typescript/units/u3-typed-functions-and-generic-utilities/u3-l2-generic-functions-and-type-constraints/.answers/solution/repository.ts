export interface Identifiable {
  id: string;
}

export interface EntityStore<T extends Identifiable> {
  items: T[];
  findById(id: string): T | undefined;
}

export function updateRecord<T extends Identifiable>(record: T): T {
  return record;
}

export function getProperty<T, K extends keyof T>(item: T, key: K): T[K] {
  return item[key];
}
