import { useEffect, useState } from "react";
import { useNavigate } from "react-router";

import { Button, Picture } from "../../components/ui";
import { assets } from "../../lib/assets";
import { PENDING_TITLES } from "../../lib/labels";
import { useStore } from "../../lib/store";
import { ActionBar } from "./ActionBar";
import { Board } from "./Board";
import { DecisionDialog } from "./DecisionDialog";
import { EventLog } from "./EventLog";
import { GangSheet } from "./GangSheet";
import { Hand } from "./Hand";
import { PlayerBar } from "./PlayerBar";
import { RoomSheet } from "./RoomSheet";
import { useCountdown, useGame } from "./useGame";

export function GameScreen() {
  const { view, game, labels, me, characterOf, isMyDecision } = useGame();
  const [selected, setSelected] = useState<string[]>([]);
  const [showLog, setShowLog] = useState(false);
  // Dev only: ?room=<place> opens a room sheet on load (screenshot checks).
  const [room, setRoom] = useState<string | null>(() =>
    import.meta.env.DEV ? new URLSearchParams(location.search).get("room") : null,
  );
  const [showGangs, setShowGangs] = useState(false);
  const error = useStore((s) => s.error);
  const clearError = useStore((s) => s.clearError);
  const connected = useStore((s) => s.connected);
  const seconds = useCountdown(game.deadline);
  const navigate = useNavigate();

  useEffect(() => setSelected([]), [view.version]);
  useEffect(() => {
    if (!error) return;
    const timer = setTimeout(clearError, 3500);
    return () => clearTimeout(timer);
  }, [error, clearError]);

  if (!labels) return <main className="p-6 text-center text-muted">Lade Spieldaten…</main>;

  const pending = view.pending;
  const status =
    view.phase === "finished"
      ? `${labels.player(view.winner)} ist ausgebrochen!`
      : pending
        ? isMyDecision
          ? PENDING_TITLES[pending.kind]
          : `Warte auf ${labels.player(pending.player)}: ${PENDING_TITLES[pending.kind]}`
        : view.turn.player === me?.id
          ? `Dein Zug · ${view.turn.actions_left} Aktion${view.turn.actions_left === 1 ? "" : "en"}`
          : `${labels.player(view.turn.player)} ist am Zug`;

  return (
    <div className="mx-auto flex h-full w-full max-w-3xl flex-col overflow-x-hidden">
      <PlayerBar />
      <div className="min-h-0 flex-1">
        <Board onRoom={setRoom} />
      </div>
      <div className="flex items-center gap-2 border-t border-line bg-panel px-3 py-2 text-sm">
        <button className="min-h-9 rounded-lg px-2 text-muted hover:text-ink" onClick={() => navigate("/")}>
          ← Lobby
        </button>
        <span className={`size-2 shrink-0 rounded-full ${connected ? "bg-teal" : "bg-danger"}`} title={connected ? "verbunden" : "getrennt"} />
        <span className={`min-w-0 flex-1 truncate font-semibold ${isMyDecision ? "text-lamp" : ""}`}>{status}</span>
        {seconds !== null && view.phase === "running" && (
          <span className={`tabular-nums ${seconds <= 10 ? "text-danger" : "text-muted"}`}>{seconds}s</span>
        )}
        <button className="min-h-9 rounded-lg px-2 text-muted hover:text-ink" onClick={() => setShowLog(true)}>
          Verlauf
        </button>
      </div>
      <ActionBar onRoom={setRoom} onGangs={() => setShowGangs(true)} />
      <Hand selected={selected} setSelected={setSelected} />

      <DecisionDialog selected={selected} />
      {showLog && <EventLog onClose={() => setShowLog(false)} />}
      {room && <RoomSheet place={room} onClose={() => setRoom(null)} />}
      {showGangs && <GangSheet onClose={() => setShowGangs(false)} />}
      {error && (
        <div className="fixed inset-x-4 top-4 z-50 mx-auto max-w-md rounded-xl bg-danger p-3 text-sm shadow-xl" role="alert">
          {error}
        </div>
      )}
      {view.phase === "finished" && view.winner && (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-4 bg-black/80 p-6 text-center">
          <Picture img={assets.pose(characterOf(view.winner), "victory")} alt="" className="max-h-[50vh]" />
          <h1 className="text-3xl font-black text-lamp">{labels.player(view.winner)} ist ausgebrochen!</h1>
          <Button variant="primary" onClick={() => navigate("/")}>
            Zur Lobby
          </Button>
        </div>
      )}
    </div>
  );
}
