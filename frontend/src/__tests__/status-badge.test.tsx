/**
 * Tests for StatusBadge component:
 * - RUNNING/STARTING/BUSY → animated dot
 * - IDLE → no dot, renders "IDLE"
 * - STALE → amber text
 * - Known terminal states render correctly
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatusBadge } from "@/components/StatusBadge";

describe("StatusBadge", () => {
  it('renders "IDLE" status correctly (no animated dot)', () => {
    const { container } = render(<StatusBadge status="IDLE" />);
    expect(screen.getByText("IDLE")).toBeInTheDocument();
    // no animated pulse dot
    expect(container.querySelector(".animate-pulse")).toBeNull();
  });

  it('renders "RUNNING" with an animated dot', () => {
    const { container } = render(<StatusBadge status="RUNNING" />);
    expect(screen.getByText("RUNNING")).toBeInTheDocument();
    expect(container.querySelector(".animate-pulse")).toBeTruthy();
  });

  it('renders "BUSY" with an animated dot', () => {
    const { container } = render(<StatusBadge status="BUSY" />);
    expect(screen.getByText("BUSY")).toBeInTheDocument();
    expect(container.querySelector(".animate-pulse")).toBeTruthy();
  });

  it('renders "STALE" without an animated dot', () => {
    const { container } = render(<StatusBadge status="STALE" />);
    expect(screen.getByText("STALE")).toBeInTheDocument();
    expect(container.querySelector(".animate-pulse")).toBeNull();
  });

  it("converts underscores to spaces in display text", () => {
    render(<StatusBadge status="STOP_REQUESTED" />);
    expect(screen.getByText("STOP REQUESTED")).toBeInTheDocument();
  });

  it("uppercases the status string", () => {
    render(<StatusBadge status="stopped" />);
    expect(screen.getByText("STOPPED")).toBeInTheDocument();
  });
});
