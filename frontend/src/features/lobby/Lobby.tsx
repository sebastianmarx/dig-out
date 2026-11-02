import { useEffect, useState } from "react";
import { useNavigate } from "react-router";

import { Brand } from "../../components/Brand";
import { Button } from "../../components/ui";
import { api, ApiError, clearIdentity } from "../../lib/api";
import { forgetGame, recentGames } from "../../lib/recent";
import { useStore } from "../../lib/store";
import type { LobbyGame } from "../../lib/types";
import { Login } from "../login/Login";

export function Lobby() {
  const identity = useStore((s) => s.identity);
  const navigate = useNavigate();
  const [games, setGames] = useState<LobbyGame[]>([]);
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [recent, setRecent] = useState(recentGames);

  useEffect(() => {
    if (!identity) return;
    let alive = true;
    const load = () =>
      api
        .openGames(identity)
        .then((g) => alive && setGames(g))
        .catch(() => alive && setError("Server nicht erreichbar"));
    void load();
    const timer = setInterval(load, 3000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [identity]);

  if (!identity) return <Login />;

  const run = async (promise: Promise<LobbyGame>) => {
    try {
      const game = await promise;
      navigate(`/g/${game.id}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Fehler");
    }
  };

  return (
    <main className="mx-auto flex max-w-lg flex-col gap-5 px-4 py-6">
      <Brand />
      <div className="flex items-center justify-between text-sm text-muted">
        <span>
          Angemeldet als <strong className="text-ink">{identity.name}</strong>
        </span>
        <button
          className="min-h-11 underline"
          onClick={() => {
            clearIdentity();
            location.reload();
          }}
        >
          Abmelden
        </button>
      </div>

      <Button
        variant="primary"
        onClick={() => void run(api.createGame(identity))}
      >
        Neues Spiel erstellen
      </Button>

      <form
        className="flex flex-col gap-2 rounded-2xl bg-panel p-3"
        onSubmit={(e) => {
          e.preventDefault();
          void run(api.joinByCode(identity, code.trim()));
        }}
      >
        <label htmlFor="join-code" className="text-sm text-muted">
          Einem Spiel beitreten: den 6-stelligen Spielcode eingeben, den der
          Gastgeber im Warteraum sieht.
        </label>
        <div className="flex gap-2">
          <input
            id="join-code"
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            placeholder="z. B. K7QX2M"
            maxLength={6}
            aria-label="Spielcode"
            className="min-h-11 min-w-0 flex-1 rounded-xl border border-line bg-night px-3 font-mono tracking-widest uppercase outline-none focus:border-orange"
          />
          <Button disabled={code.trim().length !== 6}>Beitreten</Button>
        </div>
      </form>

      {error && <p className="rounded-xl bg-danger/20 p-3 text-sm">{error}</p>}

      {recent.length > 0 && (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-semibold tracking-wide text-muted uppercase">
            Deine Spiele
          </h2>
          {recent.map((g) => (
            <div
              key={g.id}
              className="flex items-center gap-2 rounded-xl bg-panel px-3"
            >
              <button
                className="min-h-14 flex-1 truncate text-left"
                onClick={() => navigate(`/g/${g.id}`)}
              >
                {g.label}
              </button>
              <button
                className="min-h-11 min-w-11 text-muted"
                aria-label="Aus der Liste entfernen"
                onClick={() => {
                  forgetGame(g.id);
                  setRecent(recentGames());
                }}
              >
                ×
              </button>
            </div>
          ))}
        </section>
      )}

      <section className="flex flex-col gap-2">
        <h2 className="text-sm font-semibold tracking-wide text-muted uppercase">
          Offene Spiele
        </h2>
        {games.length === 0 && (
          <p className="text-sm text-muted">Gerade wartet niemand.</p>
        )}
        {games.map((g) => (
          <button
            key={g.id}
            className="flex min-h-14 items-center justify-between rounded-xl bg-panel px-4 text-left hover:bg-panel-2"
            onClick={() => void run(api.joinById(identity, g.id))}
          >
            <span>
              <span className="font-semibold">
                {g.seats[0]?.name ?? "?"}s Spiel
              </span>
              <span className="block text-xs text-muted">
                {g.seats.map((s) => s.name).join(", ")}
              </span>
            </span>
            <span className="text-sm text-muted">{g.seats.length}/6</span>
          </button>
        ))}
      </section>
    </main>
  );
}
