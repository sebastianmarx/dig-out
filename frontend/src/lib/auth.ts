// Minimal Amazon Cognito client (USER_PASSWORD_AUTH over TLS) – no SDK needed.
// Tokens live in localStorage; the strict CSP keeps third-party scripts out.

import { getConfig } from "./config";

const KEY = "digout.tokens";

interface Tokens {
  access: string;
  refresh: string;
  expires: number; // unix seconds
}

export class AuthError extends Error {}

const MESSAGES: Record<string, string> = {
  NotAuthorizedException: "Name oder Passwort falsch",
  UsernameExistsException: "Dieser Name ist schon vergeben",
  InvalidPasswordException: "Passwort zu schwach (mind. 10 Zeichen, Groß-/Kleinbuchstaben und Ziffer)",
  UserLambdaValidationException: "Plattform-Passwort falsch oder ungültiger Name",
  TooManyRequestsException: "Zu viele Versuche – bitte kurz warten",
};

async function cognito<T>(target: string, body: Record<string, unknown>): Promise<T> {
  const config = getConfig();
  if (config.mode !== "aws") throw new AuthError("Kein Cognito im Entwicklungsmodus");
  const response = await fetch(`https://cognito-idp.${config.region}.amazonaws.com/`, {
    method: "POST",
    headers: { "Content-Type": "application/x-amz-json-1.1", "X-Amz-Target": `AWSCognitoIdentityProviderService.${target}` },
    body: JSON.stringify({ ClientId: config.clientId, ...body }),
  });
  const json = await response.json();
  if (!response.ok) {
    const type = String(json.__type ?? "").split("#").pop() ?? "";
    throw new AuthError(MESSAGES[type] ?? json.message ?? "Anmeldung fehlgeschlagen");
  }
  return json as T;
}

interface AuthResult {
  AuthenticationResult: { AccessToken: string; RefreshToken?: string; ExpiresIn: number };
}

function store(result: AuthResult, refresh?: string): Tokens {
  const r = result.AuthenticationResult;
  const tokens = { access: r.AccessToken, refresh: r.RefreshToken ?? refresh ?? "", expires: Date.now() / 1000 + r.ExpiresIn };
  localStorage.setItem(KEY, JSON.stringify(tokens));
  return tokens;
}

function load(): Tokens | null {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? "null") as Tokens | null;
  } catch {
    return null;
  }
}

export async function signIn(username: string, password: string): Promise<void> {
  store(await cognito<AuthResult>("InitiateAuth", { AuthFlow: "USER_PASSWORD_AUTH", AuthParameters: { USERNAME: username, PASSWORD: password } }));
}

export async function signUp(username: string, password: string, platformPassword: string): Promise<void> {
  await cognito("SignUp", {
    Username: username,
    Password: password,
    ValidationData: [{ Name: "platformPassword", Value: platformPassword }],
  });
  await signIn(username, password);
}

export function signOut(): void {
  localStorage.removeItem(KEY);
}

/** A valid access token (refreshed when it is about to expire), or null when signed out. */
export async function accessToken(): Promise<string | null> {
  const tokens = load();
  if (!tokens) return null;
  if (tokens.expires - 60 > Date.now() / 1000) return tokens.access;
  try {
    const result = await cognito<AuthResult>("InitiateAuth", { AuthFlow: "REFRESH_TOKEN_AUTH", AuthParameters: { REFRESH_TOKEN: tokens.refresh } });
    return store(result, tokens.refresh).access;
  } catch {
    signOut();
    return null;
  }
}

/** Identity from the stored access token (sub + username claims). */
export function tokenIdentity(): { id: string; name: string } | null {
  const tokens = load();
  if (!tokens) return null;
  try {
    const payload = JSON.parse(atob(tokens.access.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
    return { id: String(payload.sub), name: String(payload.username) };
  } catch {
    return null;
  }
}
