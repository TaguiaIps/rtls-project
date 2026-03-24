import "@testing-library/jest-dom/vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

describe("App", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.restoreAllMocks();
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(null, {
        status: 401
      })
    );
  });

  it("renders the secure sign-in screen when unauthenticated", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /rtls analytics platform/i })).toBeInTheDocument();
    });
    expect(screen.getByText(/secure sign-in/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });
});
