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
    const phrases = screen.getAllByText("Turn syllabi into structured study plans");
    expect(phrases.length).toBeGreaterThanOrEqual(1);
    const privacy = screen.getAllByText("100% local — your PDFs never leave your machine");
    expect(privacy.length).toBeGreaterThanOrEqual(1);
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

  it("renders ModeSelector with all three tabs", () => {
    render(<App />);
    expect(screen.getByRole("button", { name: "Summary" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "PYQ" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Syllabus Graph" })).toBeInTheDocument();
  });
});
