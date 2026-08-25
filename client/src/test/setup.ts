import "@testing-library/jest-dom/vitest";

// node >= 22 ships an experimental global localStorage getter that returns
// undefined unless --localstorage-file is passed; give jsdom tests a real store
if (typeof window !== "undefined" && !window.localStorage) {
  class MemoryStorage {
    private store = new Map<string, string>();
    getItem(key: string): string | null {
      return this.store.has(key) ? this.store.get(key)! : null;
    }
    setItem(key: string, value: string): void {
      this.store.set(key, String(value));
    }
    removeItem(key: string): void {
      this.store.delete(key);
    }
    clear(): void {
      this.store.clear();
    }
  }
  Object.defineProperty(window, "localStorage", {
    value: new MemoryStorage(),
    configurable: true,
  });
}
