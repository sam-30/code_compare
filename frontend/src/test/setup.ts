import "@testing-library/jest-dom";

// Recharts ResponsiveContainer requires ResizeObserver, which JSDOM doesn't provide.
globalThis.ResizeObserver = class {
  observe() {}
  unobserve() {}
  disconnect() {}
};
