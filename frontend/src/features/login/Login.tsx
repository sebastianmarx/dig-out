import { useState } from "react";

import { Brand } from "../../components/Brand";
import { Button } from "../../components/ui";
import { loadIdentity } from "../../lib/api";
import { AuthError, signIn, signUp } from "../../lib/auth";
import { getConfig } from "../../lib/config";
import { useStore } from "../../lib/store";

const NAME_RE = /^[\w äöüÄÖÜß.-]{1,20}$/;
const inputClass = "min-h-11 rounded-xl border border-line bg-night px-3 text-base outline-none focus:border-orange";

export function Login() {
  return (
    <main className="mx-auto flex min-h-full max-w-md flex-col justify-center gap-6 px-4 py-6">
      <Brand />
      {getConfig().mode === "aws" ? <AccountLogin /> : <DevLogin />}
    </main>
  );
}

// Development: just a display name.
function DevLogin() {
  const login = useStore((s) => s.login);
  const [name, setName] = useState("");
  const valid = NAME_RE.test(name.trim());
  return (
    <form
      className="flex flex-col gap-3 rounded-2xl bg-panel p-4"
      onSubmit={(e) => {
        e.preventDefault();
        if (valid) login(name.trim());
      }}
    >
      <label className="text-sm text-muted" htmlFor="name">
        Dein Name (Entwicklungs-Login)
      </label>
      <input id="name" autoFocus maxLength={20} value={name} onChange={(e) => setName(e.target.value)} className={inputClass} />
      <Button variant="primary" disabled={!valid}>
        Los geht’s
      </Button>
    </form>
  );
}

// AWS: Cognito account; registering needs the platform password again (checked server-side).
function AccountLogin() {
  const setIdentity = useStore((s) => s.setIdentity);
  const [mode, setMode] = useState<"login" | "register">("login");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [platform, setPlatform] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const valid = NAME_RE.test(name.trim()) && password.length >= 10 && (mode === "login" || platform.length > 0);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      if (mode === "login") await signIn(name.trim(), password);
      else await signUp(name.trim(), password, platform);
      setIdentity(loadIdentity());
    } catch (e) {
      setError(e instanceof AuthError ? e.message : "Verbindung fehlgeschlagen");
    } finally {
      setBusy(false);
    }
  };

  return (
    <form
      className="flex flex-col gap-3 rounded-2xl bg-panel p-4"
      onSubmit={(e) => {
        e.preventDefault();
        if (valid && !busy) void submit();
      }}
    >
      <div className="grid grid-cols-2 gap-1 rounded-xl bg-night p-1">
        {(["login", "register"] as const).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => setMode(m)}
            className={`min-h-10 rounded-lg text-sm font-semibold ${mode === m ? "bg-panel-2" : "text-muted"}`}
          >
            {m === "login" ? "Anmelden" : "Registrieren"}
          </button>
        ))}
      </div>
      <input aria-label="Name" placeholder="Name" autoComplete="username" maxLength={20} value={name} onChange={(e) => setName(e.target.value)} className={inputClass} />
      <input
        aria-label="Passwort"
        placeholder="Passwort (mind. 10 Zeichen)"
        type="password"
        autoComplete={mode === "login" ? "current-password" : "new-password"}
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        className={inputClass}
      />
      {mode === "register" && (
        <input
          aria-label="Plattform-Passwort"
          placeholder="Plattform-Passwort"
          type="password"
          value={platform}
          onChange={(e) => setPlatform(e.target.value)}
          className={inputClass}
        />
      )}
      {error && <p className="rounded-lg bg-danger/20 p-2 text-sm">{error}</p>}
      <Button variant="primary" disabled={!valid || busy}>
        {busy ? "Moment…" : mode === "login" ? "Anmelden" : "Konto erstellen"}
      </Button>
    </form>
  );
}
