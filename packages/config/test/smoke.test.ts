import { describe, expect, it } from "vitest";

import { LOCAL_STACK_SERVICES, PRODUCT_NAME, ROLE_HOME_ROUTE } from "../src";

describe("config package", () => {
  it("exposes the local stack inventory", () => {
    expect(PRODUCT_NAME).toBe("RTLS Analytics Platform");
    expect(LOCAL_STACK_SERVICES).toHaveLength(7);
  });

  it("maps roles to home routes", () => {
    expect(ROLE_HOME_ROUTE.Administrator).toBe("/admin");
    expect(ROLE_HOME_ROUTE["General User"]).toBe("/operations");
  });
});
