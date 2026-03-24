import { describe, expect, it } from "vitest";

import type { AuthenticatedUser, RuntimeServiceDefinition } from "../src";

describe("contracts", () => {
  it("supports runtime service definitions", () => {
    const service: RuntimeServiceDefinition = {
      name: "api",
      label: "API",
      purpose: "Serves HTTP and WebSocket traffic."
    };

    expect(service.name).toBe("api");
  });

  it("supports authenticated user contracts", () => {
    const user: AuthenticatedUser = {
      id: "user-1",
      email: "alex@example.com",
      display_name: "Alex",
      role: "Administrator",
      status: "active"
    };

    expect(user.role).toBe("Administrator");
  });
});
