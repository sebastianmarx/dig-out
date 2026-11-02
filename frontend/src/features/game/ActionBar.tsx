import { useState } from "react";

import { Button, Sheet } from "../../components/ui";
import type { Action } from "../../lib/types";
import { useGame } from "./useGame";

const GENERAL: [string, string][] = [
  ["play_card", "🃏 Karte spielen"],
  ["extort", "🔪 Erpressen"],
  ["reveal_background", "🎭 Hintergrund"],
];

/** Turn controls. Room actions live in the room sheet (tap a room or "Aktionen hier"). */
export function ActionBar({ onRoom, onGangs }: { onRoom: (place: string) => void; onGangs: () => void }) {
  const { view, legal, labels, act, busy, me, data } = useGame();
  const [open, setOpen] = useState<[string, Action[]] | null>(null);
  if (!labels || !me || !data) return null;
  const myPlace = view.players.find((p) => p.id === me.id)?.place ?? "";
  const myTurn = view.turn.player === me.id && !view.pending && view.phase === "running";

  if (!myTurn)
    return (
      <div className="flex gap-1.5 border-t border-line bg-panel px-2 py-2">
        <Button className="flex-1" onClick={() => onRoom(myPlace)}>
          📍 {labels.place(myPlace)}
        </Button>
        <Button className="flex-1" onClick={onGangs}>
          🛡 Gangs
        </Button>
      </div>
    );

  const rolls = legal.filter((a) => a.type === "move_roll");
  const endTurn = legal.find((a) => a.type === "end_turn");
  const pick = (label: string, actions: Action[]) => (actions.length === 1 ? act(actions[0]) : setOpen([label, actions]));

  return (
    <div className="grid grid-cols-3 gap-1.5 border-t border-line bg-panel px-2 py-2">
      <Button variant="primary" className="col-span-2" disabled={busy} onClick={() => onRoom(myPlace)}>
        📍 {labels.place(myPlace)}: Aktionen hier
      </Button>
      <Button
        variant="primary"
        disabled={busy || rolls.length === 0}
        title="Würfeln: die Augenzahl zeigt zwei Räume, du wählst einen"
        onClick={() => pick("Würfeln", rolls)}
      >
        🎲 Würfeln
      </Button>
      {GENERAL.map(([type, label]) => {
        const actions = legal.filter((a) => a.type === type);
        return (
          <Button key={type} disabled={busy || actions.length === 0} className="px-2" onClick={() => pick(label, actions)}>
            {label}
          </Button>
        );
      })}
      <Button className="px-2" onClick={onGangs}>
        🛡 Gangs
      </Button>
      {endTurn && (
        <Button
          variant={view.turn.actions_left === 0 ? "primary" : "secondary"}
          disabled={busy}
          className="col-span-2"
          onClick={() => act(endTurn)}
        >
          Zug beenden {view.turn.actions_left > 0 && `(${view.turn.actions_left} Aktion${view.turn.actions_left === 1 ? "" : "en"} übrig)`}
        </Button>
      )}

      {open && (
        <Sheet title={open[0]} onClose={() => setOpen(null)}>
          <div className="flex flex-col gap-2">
            {open[1].map((a, i) => (
              <Button
                key={i}
                className="text-left"
                onClick={() => {
                  act(a);
                  setOpen(null);
                }}
              >
                {labels.action(a)}
              </Button>
            ))}
          </div>
        </Sheet>
      )}
    </div>
  );
}
