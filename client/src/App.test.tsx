import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import App from "./App";

describe("App shell", () => {
  it("renders header, main content container and footer", () => {
    render(<App />);
    expect(screen.getByRole("banner")).toBeInTheDocument();
    expect(screen.getByRole("main")).toBeInTheDocument();
    expect(screen.getByRole("contentinfo")).toBeInTheDocument();
  });

  it("renders the ticker copy", () => {
    render(<App />);
    expect(
      screen.getByText("New! AI study assets for Database Systems"),
    ).toBeInTheDocument();
    expect(screen.getByText("100% Private & Local")).toBeInTheDocument();
  });

  it("lays out banner before main before contentinfo", () => {
    render(<App />);
    const banner = screen.getByRole("banner");
    const main = screen.getByRole("main");
    const contentinfo = screen.getByRole("contentinfo");
    const follows = (a: HTMLElement, b: HTMLElement) =>
      (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0;
    expect(follows(banner, main)).toBe(true);
    expect(follows(main, contentinfo)).toBe(true);
  });
});
