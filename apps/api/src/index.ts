import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { getConfig } from "./config.js";
import { MockScraper } from "./scraper.mock.js";
import { HttpScraper } from "./scraper.http.js";
import { BetMgmScraper } from "./scraper.betmgm.js";
import { PinnacleScraper } from "./scraper.pinnacle.js";
import { Pipeline } from "./pipeline.js";
import type { OddsScraper } from "./types.js";

const config = getConfig();

const scrapers: OddsScraper[] = [new MockScraper()];
if (config.oddsSourceUrl) {
  scrapers.push(new HttpScraper(config.oddsSourceUrl));
}
if (config.betmgm.enabled) {
  scrapers.push(new BetMgmScraper({
    market: config.betmgm.market,
    lang: config.betmgm.lang,
    offering: config.betmgm.offering,
    upcomingDays: config.betmgm.upcomingDays
  }));
}
if (config.pinnacle.enabled) {
  if (config.pinnacle.apiKey && config.pinnacle.deviceUuid) {
    scrapers.push(new PinnacleScraper({
      apiKey: config.pinnacle.apiKey,
      deviceUuid: config.pinnacle.deviceUuid,
      leagueId: config.pinnacle.leagueId,
      brandId: config.pinnacle.brandId
    }));
  } else {
    console.warn(
      "PINNACLE_ENABLED is true, but PINNACLE_API_KEY or PINNACLE_DEVICE_UUID is missing. Skipping Pinnacle."
    );
  }
}

const pipeline = new Pipeline(scrapers, config.alertEdgeThreshold);
const clients = new Set<ServerResponse>();

function sendJson(res: ServerResponse, status: number, body: unknown): void {
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json");
  res.end(JSON.stringify(body));
}

function onRequest(req: IncomingMessage, res: ServerResponse): void {
  const url = req.url ?? "/";

  if (url === "/health") {
    sendJson(res, 200, { status: "ok", service: "portfolio-api" });
    return;
  }

  if (url === "/api/snapshot") {
    sendJson(res, 200, pipeline.current());
    return;
  }

  if (url === "/api/meta") {
    sendJson(res, 200, {
      pollIntervalMs: config.pollIntervalMs,
      alertEdgeThreshold: config.alertEdgeThreshold,
      sources: scrapers.map((scraper) => scraper.source)
    });
    return;
  }

  if (url === "/api/stream") {
    res.writeHead(200, {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
      "Access-Control-Allow-Origin": "*"
    });
    res.write(`event: snapshot\ndata: ${JSON.stringify(pipeline.current())}\n\n`);

    clients.add(res);
    req.on("close", () => {
      clients.delete(res);
      res.end();
    });
    return;
  }

  sendJson(res, 404, { error: "not_found" });
}

const server = createServer(onRequest);

async function publish(): Promise<void> {
  const snapshot = await pipeline.tick();
  const payload = `event: snapshot\ndata: ${JSON.stringify(snapshot)}\n\n`;

  for (const client of clients) {
    client.write(payload);
  }
}

setInterval(() => {
  void publish();
}, config.pollIntervalMs);

void publish();

server.listen(config.port, () => {
  console.log(
    `portfolio-api running on http://localhost:${config.port} with sources: ${scrapers.map((scraper) => scraper.source).join(", ")}`
  );
});
