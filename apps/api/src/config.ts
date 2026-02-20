export interface AppConfig {
  port: number;
  oddsSourceUrl?: string;
  alertEdgeThreshold: number;
  pollIntervalMs: number;
  betmgm: {
    enabled: boolean;
    market: string;
    lang: string;
    offering: string;
    upcomingDays: number;
  };
  pinnacle: {
    enabled: boolean;
    apiKey?: string;
    deviceUuid?: string;
    leagueId: number;
    brandId: number;
  };
}

function parseBoolean(value: string | undefined, fallback: boolean): boolean {
  if (value === undefined) {
    return fallback;
  }

  return ["1", "true", "yes", "on"].includes(value.toLowerCase());
}

export function getConfig(): AppConfig {
  return {
    port: Number(process.env.PORT ?? 4000),
    oddsSourceUrl: process.env.ODDS_SOURCE_URL || undefined,
    alertEdgeThreshold: Number(process.env.ALERT_EDGE_THRESHOLD ?? 3),
    pollIntervalMs: Number(process.env.POLL_INTERVAL_MS ?? 4000),
    betmgm: {
      enabled: parseBoolean(process.env.BETMGM_ENABLED, false),
      market: process.env.BETMGM_MARKET ?? "SE",
      lang: process.env.BETMGM_LANG ?? "sv_SE",
      offering: process.env.BETMGM_OFFERING ?? "betmgmse",
      upcomingDays: Number(process.env.BETMGM_UPCOMING_DAYS ?? 2)
    },
    pinnacle: {
      enabled: parseBoolean(process.env.PINNACLE_ENABLED, false),
      apiKey: process.env.PINNACLE_API_KEY || undefined,
      deviceUuid: process.env.PINNACLE_DEVICE_UUID || undefined,
      leagueId: Number(process.env.PINNACLE_LEAGUE_ID ?? 12),
      brandId: Number(process.env.PINNACLE_BRAND_ID ?? 0)
    }
  };
}
