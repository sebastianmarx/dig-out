import { useEffect } from "react";
import { Link, useParams } from "react-router";

import { api } from "../../lib/api";
import { useStore } from "../../lib/store";
import { Lobby } from "../lobby/Lobby";
import { WaitingRoom } from "../lobby/WaitingRoom";
import { GameScreen } from "./GameScreen";

export function GameRoute() {
  const { gameId = "" } = useParams();
  const identity = useStore((s) => s.identity);
  const open = useStore((s) => s.open);
  const lobby = useStore((s) => s.lobby);
  const game = useStore((s) => s.game);
  const closed = useStore((s) => s.closed);

  useEffect(() => {
    if (!identity) return;
    // Opening an invite link joins the waiting room; for running games this just fails (spectator).
    void api.joinById(identity, gameId).catch(() => undefined).finally(() => open(gameId));
  }, [identity, gameId, open]);

  if (!identity) return <Lobby />;
  if (closed)
    return (
      <main className="p-6 text-center">
        <p className="mb-4">Dieses Spiel gibt es nicht mehr.</p>
        <Link to="/" className="text-teal underline">
          Zur Lobby
        </Link>
      </main>
    );
  if (game) return <GameScreen />;
  if (lobby) return <WaitingRoom lobby={lobby} />;
  return <main className="p-6 text-center text-muted">Verbinde…</main>;
}
