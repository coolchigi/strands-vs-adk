import test from "node:test";
import assert from "node:assert/strict";
import type { Identifiable, EntityStore } from "./repository.ts";
import { updateRecord, getProperty } from "./repository.ts";

test("EntityStore constrains T to Identifiable", () => {
  interface User extends Identifiable {
    id: string;
    name: string;
  }
  const store: EntityStore<User> = {
    items: [{ id: "u-1", name: "Alice" }],
    findById(id: string) {
      return this.items.find((item) => item.id === id);
    },
  };
  const found = store.findById("u-1");
  assert.equal(found?.name, "Alice");

  // @ts-expect-error EntityStore requires T to extend Identifiable
  type InvalidStore = EntityStore<{ name: string }>;
});

test("updateRecord requires an id and preserves the specific input type", () => {
  interface User extends Identifiable {
    id: string;
    name: string;
  }
  const user: User = { id: "u-1", name: "Alice" };
  const updated: User = updateRecord(user);
  assert.equal(updated.name, "Alice");

  const invalid = { name: "No ID" };
  // @ts-expect-error invalid object missing id property
  updateRecord(invalid);
});

test("getProperty retrieves property value and restricts key to valid properties", () => {
  const user = { id: "u-1", name: "Alice", active: true };
  const name: string = getProperty(user, "name");
  const active: boolean = getProperty(user, "active");
  assert.equal(name, "Alice");
  assert.equal(active, true);

  // @ts-expect-error missing is not a key of user
  getProperty(user, "missing");
});
