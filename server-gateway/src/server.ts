import { createApp } from "./app.js";
import { env } from "./config/env.config.js";

const app = createApp();

app.listen(env.port, () => {
  console.log(`gateway listening on http://localhost:${env.port}`);
});
