import { useEffect, useMemo, useState } from "react";

import { PLAYER_COLORS } from "../../lib/assets";
import { Labels } from "../../lib/labels";
import { useStore } from "../../lib/store";

/** Everything the game components need, derived from the latest server message. */
export function useGame() {
  const game = useStore((s) => s.game)!;
  const data = useStore((s) => s.data);
  const act = useStore((s) => s.act);
  const busy = useStore((s) => s.busy);
  const labels = useMemo(() => (data ? new Labels(data, game) : null), [data, game]);
  const view = game.view;
  const me = view.me;
  const seats = game.lobby.seats;

  const characterOf = (playerId: string) => seats.find((s) => s.user_id === playerId)?.character ?? "char.01";
  const colorOf = (playerId: string) => PLAYER_COLORS[(view.players.find((p) => p.id === playerId)?.seat ?? 0) % 6];
  const isMyDecision = !!me && view.phase === "running" && (view.pending ? view.pending.player === me.id : view.turn.player === me.id);

  return { game, view, me, data, labels, legal: game.legal, act, busy, characterOf, colorOf, isMyDecision };
}

export function useCountdown(deadline: number | null): number | null {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 500);
    return () => clearInterval(timer);
  }, []);
  return deadline ? Math.max(0, Math.ceil(deadline - now / 1000)) : null;
}
