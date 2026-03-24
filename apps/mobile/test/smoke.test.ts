import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

describe("mobile workspace baseline", () => {
  it("declares the RTLS Expo app metadata", () => {
    const appJsonPath = join(process.cwd(), "app.json");
    const appJson = JSON.parse(readFileSync(appJsonPath, "utf8")) as {
      expo: { name: string; slug: string };
    };

    expect(appJson.expo.name).toBe("RTLS Analytics Platform");
    expect(appJson.expo.slug).toBe("rtls-analytics-platform");
  });
});
