import { describe, it, expect } from "vitest";
import request from "supertest";
import express from "express";
import { uploadMiddleware, validatePDFHeader } from "../src/middleware/upload.middleware.js";
import { errorMiddleware } from "../src/middleware/error.middleware.js";

function makeApp() {
  const app = express();
  app.post(
    "/upload",
    uploadMiddleware,
    validatePDFHeader,
    (req, res) => res.status(200).json({ bytes: req.file?.buffer.length }),
  );
  app.use(errorMiddleware);
  return app;
}

describe("POST /upload", () => {
  it("accepts a valid %PDF header", async () => {
    const app = makeApp();
    const res = await request(app)
      .post("/upload")
      .attach("file", Buffer.from("%PDF-1.7\n%âãÏÓ\njunk"), "doc.pdf");
    expect(res.status).toBe(200);
  });

  it("rejects spoofed non-PDF bytes with ERR_400_BAD_MIME", async () => {
    const app = makeApp();
    const res = await request(app)
      .post("/upload")
      .attach("file", Buffer.from("MZ\x90\x00spoof"), "fake.pdf");
    expect(res.status).toBe(400);
    expect(res.body.error).toBe("ERR_400_BAD_MIME");
  });

  it("rejects >15MB files with ERR_413_FILE_TOO_LARGE", async () => {
    const app = makeApp();
    const big = Buffer.concat([Buffer.from("%PDF-1.7\n"), Buffer.alloc(15 * 1024 * 1024)]);
    const res = await request(app)
      .post("/upload")
      .attach("file", big, "big.pdf");
    expect(res.status).toBe(413);
    expect(res.body.error).toBe("ERR_413_FILE_TOO_LARGE");
  });

  it("rejects a missing file with ERR_400_NO_FILE", async () => {
    const app = makeApp();
    const res = await request(app).post("/upload").field("note", "hello");
    expect(res.status).toBe(400);
    expect(res.body.error).toBe("ERR_400_NO_FILE");
  });
});