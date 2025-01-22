import express, { type Request, Response, NextFunction } from "express";
import { registerRoutes } from "./routes";
import { setupVite, serveStatic, log } from "./vite";
import { spawn } from "child_process";
import path from "path";

const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: false }));

app.use((req, res, next) => {
  const start = Date.now();
  const path = req.path;
  let capturedJsonResponse: Record<string, any> | undefined = undefined;

  const originalResJson = res.json;
  res.json = function (bodyJson, ...args) {
    capturedJsonResponse = bodyJson;
    return originalResJson.apply(res, [bodyJson, ...args]);
  };

  res.on("finish", () => {
    const duration = Date.now() - start;
    if (path.startsWith("/api")) {
      let logLine = `${req.method} ${path} ${res.statusCode} in ${duration}ms`;
      if (capturedJsonResponse) {
        logLine += ` :: ${JSON.stringify(capturedJsonResponse)}`;
      }

      if (logLine.length > 80) {
        logLine = logLine.slice(0, 79) + "…";
      }

      log(logLine);
    }
  });

  next();
});

// Start Flask server for translations
const startFlaskServer = () => {
  const flaskServer = spawn('python3', [path.join(process.cwd(), 'app', 'translation_server.py')], {
    env: { ...process.env, FLASK_PORT: '5001' }
  });

  flaskServer.stdout.on('data', (data) => {
    log(`[Flask] ${data}`);
  });

  flaskServer.stderr.on('data', (data) => {
    console.error(`[Flask Error] ${data}`);
  });

  flaskServer.on('close', (code) => {
    console.error(`Flask server exited with code ${code}`);
    process.exit(1); // Exit if Flask server dies
  });

  // Give Flask server time to start
  return new Promise((resolve) => setTimeout(resolve, 2000));
};

(async () => {
  // Start Flask server first
  await startFlaskServer();

  const server = registerRoutes(app);

  app.use((err: any, _req: Request, res: Response, _next: NextFunction) => {
    const status = err.status || err.statusCode || 500;
    const message = err.message || "Internal Server Error";

    res.status(status).json({ message });
    throw err;
  });

  // importantly only setup vite in development and after
  // setting up all the other routes so the catch-all route
  // doesn't interfere with the other routes
  if (app.get("env") === "development") {
    await setupVite(app, server);
  } else {
    serveStatic(app);
  }

  // ALWAYS serve the app on port 5000
  // this serves both the API and the client
  const PORT = 5000;
  server.listen(PORT, "0.0.0.0", () => {
    log(`Express server serving on port ${PORT}`);
  });
})();