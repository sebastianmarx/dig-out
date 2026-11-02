import { useNavigate } from "react-router";

import { Button, Picture } from "../../components/ui";
import { api } from "../../lib/api";
import { assets } from "../../lib/assets";
import { useStore } from "../../lib/store";
import type { LobbyGame } from "../../lib/types";

const CHARACTERS: [string, string][] = [
  ["char.01", "Der Riese"],
  ["char.02", "Die Alte"],
  ["char.03", "Der Nerd"],
  ["char.04", "Die Tätowierte"],
  ["char.05", "Der Dandy"],
  ["char.06", "Der Junge"],
];

export function WaitingRoom({ lobby }: { lobby: LobbyGame }) {
  const identity = useStore((s) => s.identity)!;
  const lobbyOp = useStore((s) => s.lobbyOp);
  const navigate = useNavigate();
  const mine = lobby.seats.find((s) => s.user_id === identity.id);
  const isHost = lobby.host === identity.id;
  const canStart = lobby.seats.length >= 2 && lobby.seats.every((s) => s.ready);
  const link = `${location.origin}/g/${lobby.id}`;

  return (
    <main className="mx-auto flex max-w-lg flex-col gap-5 px-4 py-6">
      <header className="text-center">
        <p className="text-sm text-muted">Spielcode</p>
        <p className="font-mono text-4xl font-bold tracking-[0.3em]">{lobby.code}</p>
        <button
          className="mt-1 min-h-11 text-sm text-teal underline"
          onClick={() =>
            navigator.share ? void navigator.share({ title: "Dig Out", url: link }) : void navigator.clipboard?.writeText(link)
          }
        >
          Einladungslink teilen
        </button>
      </header>

      <section className="flex flex-col gap-2">
        {lobby.seats.map((seat) => (
          <div key={seat.user_id} className="flex items-center gap-3 rounded-xl bg-panel p-2">
            {seat.character ? (
              <Picture img={assets.portrait(seat.character)} alt="" className="size-12 rounded-full bg-panel-2 object-cover" />
            ) : (
              <div className="size-12 rounded-full bg-panel-2" />
            )}
            <span className="flex-1 font-semibold">
              {seat.name} {seat.user_id === lobby.host && <span className="text-xs text-lamp">(Gastgeber)</span>}
            </span>
            <span className={`text-sm ${seat.ready ? "text-teal" : "text-muted"}`}>{seat.ready ? "bereit" : "wählt…"}</span>
          </div>
        ))}
      </section>

      {mine && (
        <section>
          <h2 className="mb-2 text-sm font-semibold tracking-wide text-muted uppercase">Deine Figur</h2>
          <div className="grid grid-cols-3 gap-2">
            {CHARACTERS.map(([id, name]) => {
              const takenBy = lobby.seats.find((s) => s.character === id && s.user_id !== identity.id);
              const selected = mine.character === id;
              return (
                <button
                  key={id}
                  disabled={!!takenBy || mine.ready}
                  onClick={() => lobbyOp("character", { character: id })}
                  className={`flex flex-col items-center gap-1 rounded-xl p-2 transition disabled:opacity-35 ${
                    selected ? "bg-orange/30 ring-2 ring-orange" : "bg-panel hover:bg-panel-2"
                  }`}
                >
                  <Picture img={assets.portrait(id)} alt="" className="aspect-square w-full rounded-lg object-cover" />
                  <span className="text-xs">{name}</span>
                </button>
              );
            })}
          </div>
        </section>
      )}

      <section className="flex items-center gap-2 rounded-xl bg-panel p-3 text-sm">
        <span className="flex-1">⏱ Zeitlimit pro Zug</span>
        {isHost ? (
          <select
            aria-label="Zeitlimit"
            value={Number(lobby.options.turn_seconds ?? 0)}
            onChange={(e) => lobbyOp("timer", { timer: Number(e.target.value) })}
            className="min-h-11 rounded-lg border border-line bg-night px-2"
          >
            <option value={0}>ohne Limit</option>
            <option value={60}>60 Sekunden</option>
            <option value={90}>90 Sekunden</option>
            <option value={120}>120 Sekunden</option>
          </select>
        ) : (
          <span className="text-muted">{lobby.options.turn_seconds ? `${lobby.options.turn_seconds} s` : "ohne Limit"}</span>
        )}
      </section>

      <div className="flex flex-col gap-2">
        {mine && (
          <Button
            variant={mine.ready ? "secondary" : "primary"}
            disabled={!mine.character}
            onClick={() => lobbyOp(mine.ready ? "unready" : "ready")}
          >
            {mine.ready ? "Doch nicht bereit" : "Bereit"}
          </Button>
        )}
        {isHost && (
          <Button variant="primary" disabled={!canStart} onClick={() => lobbyOp("start")}>
            Spiel starten
          </Button>
        )}
        <Button
          variant="ghost"
          onClick={() => void api.leave(identity, lobby.id).finally(() => navigate("/"))}
        >
          Warteraum verlassen
        </Button>
      </div>
    </main>
  );
}
