import { describe, it, expect } from "vitest";
import request from "supertest";
import { createApp } from "../src/app.js";

describe("CORS lockdown", () => {
  it("allows preflight from localhost:5173", async () => {
    const app = createApp();
    const res = await request(app)
      .options("/api/document/process")
      .set("Origin", "http://localhost:5173")
      .set("Access-Control-Request-Method", "POST");
    expect(res.headers["access-control-allow-origin"]).toBe("http://localhost:5173");
  });

  it("does not allow disallowed origins", async () => {
    const app = createApp();
    const res = await request(app)
      .options("/api/document/process")
      .set("Origin", "https://evil.example");
    expect(res.headers["access-control-allow-origin"]).toBeUndefined();
  });
});

describe("Rate limiting on uploads", () => {
  it("blocks the 6th upload within the window with ERR_429_RATE_LIMIT", async () => {
    const app = createApp();
    const upload = () =>
      request(app)
        .post("/api/document/process")
        .set("Origin", "http://localhost:5173")
        .attach("file", Buffer.from("%PDF-1.7\n"), "doc.pdf");

    for (let i = 0; i < 5; i++) {
      await upload();
    }
    const sixth = await upload();
    expect(sixth.status).toBe(429);
    expect(sixth.body.error).toBe("ERR_429_RATE_LIMIT");
  });
});
