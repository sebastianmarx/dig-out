// Runtime configuration. Development: local devserver with name-only login.
// AWS: /config.json is written by scripts/deploy.py (Cognito client, WebSocket URL).

export type AppConfig =
  | { mode: "dev" }
  | { mode: "aws"; region: string; clientId: string; wsUrl: string };

let config: AppConfig = { mode: "dev" };

export async function loadConfig(): Promise<AppConfig> {
  if (import.meta.env.DEV) return config;
  const response = await fetch("/config.json", { cache: "no-store" });
  config = (await response.json()) as AppConfig;
  return config;
}

export function getConfig(): AppConfig {
  return config;
}
