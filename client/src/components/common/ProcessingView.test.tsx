import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ProcessingView from "./ProcessingView";

describe("ProcessingView", () => {
  it("renders one box per chunk", () => {
    render(<ProcessingView chunksTotal={5} chunksDone={0} />);
    const boxes = screen.getByTestId("chunk-boxes").children;
    expect(boxes).toHaveLength(5);
  });

  it("marks completed boxes as done", () => {
    render(<ProcessingView chunksTotal={4} chunksDone={2} />);
    const boxes = screen.getByTestId("chunk-boxes").children;
    expect(boxes[0].className).toContain("chunk-done");
    expect(boxes[1].className).toContain("chunk-done");
    expect(boxes[2].className).toContain("chunk-pending");
    expect(boxes[3].className).toContain("chunk-pending");
  });

  it("shows the k/n counter", () => {
    render(<ProcessingView chunksTotal={7} chunksDone={3} />);
    expect(screen.getByTestId("chunk-counter")).toHaveTextContent("3/7");
  });
});

describe("ProcessingView cancel", () => {
  it("renders the kill button when onCancel is given", () => {
    render(<ProcessingView chunksTotal={3} chunksDone={1} onCancel={() => {}} />);
    expect(screen.getByTestId("kill-job")).toBeInTheDocument();
  });

  it("hides the kill button without onCancel", () => {
    render(<ProcessingView chunksTotal={3} chunksDone={1} />);
    expect(screen.queryByTestId("kill-job")).not.toBeInTheDocument();
  });

  it("invokes onCancel on click", () => {
    const onCancel = vi.fn();
    render(<ProcessingView chunksTotal={3} chunksDone={1} onCancel={onCancel} />);
    fireEvent.click(screen.getByTestId("kill-job"));
    expect(onCancel).toHaveBeenCalledOnce();
  });
});
