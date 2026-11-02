import { Button, Picture, Sheet } from "../../components/ui";
import { assets } from "../../lib/assets";
import { blockedReason, diceFor, ROOM_ACTIONS } from "../../lib/rooms";
import type { Action } from "../../lib/types";
import { useGame } from "./useGame";

/** Everything about one room: what it offers, what you can do here right now, how to get here. */
export function RoomSheet({ place, onClose }: { place: string; onClose: () => void }) {
  const { view, data, labels, legal, act, busy, me, characterOf } = useGame();
  if (!data || !labels) return null;
  const def = data.board.places.find((p) => p.id === place)!;
  const myPlace = view.players.find((p) => p.id === me?.id)?.place;
  const here = view.players.filter((p) => p.place === place);
  const run = (a: Action) => {
    act(a);
    onClose();
  };

  const capabilities: { type: string; icon: string; label: string; hint: string }[] = [
    { type: "search", icon: "🔍", label: `Suchen: ${def.search} Karte${def.search === 1 ? "" : "n"} ziehen`, hint: "1× pro Zug" },
    ...(def.craft_allowed
      ? [{ type: "craft", icon: "🔨", label: "Herstellen", hint: "2 Kettenglieder + Spitze → Spitzhacke, + Behälter → Schaufel, + Klinge → 2 Messer" }]
      : []),
    ...def.actions.map((a) => ({ type: a, ...ROOM_ACTIONS[a] })),
  ];

  const variants = (type: string) => {
    if (myPlace !== place) return [];
    const all = legal.filter((a) => a.type === type);
    return type === "sell" ? all.filter((a) => (a.cards as string[]).length > 1 || all.length === 1) : all;
  };
  const moveHere = legal.find((a) => a.type === "choose_place" && a.place === place);
  const cautious = legal.find((a) => a.type === "move_cautious" && a.place === place);

  return (
    <Sheet title={`${diceFor(data, place).join(" / ")} · ${def.name}`} onClose={onClose}>
      <div className="mb-3 flex gap-3">
        <Picture img={assets.place(place)} alt="" className="size-24 shrink-0" />
        <div className="text-sm">
          <p className="flex items-center gap-1">
            Würfel:
            {diceFor(data, place).map((f) => (
              <Picture key={f} img={assets.dice(f)} alt={String(f)} className="size-6" />
            ))}
          </p>
          <p className="text-muted">Suchen: {def.search} Karte(n)</p>
          <p className="text-muted">Herstellen: {def.craft_allowed ? "ja" : "nein"}</p>
          {myPlace === place && <p className="mt-1 font-semibold text-lamp">Du bist hier</p>}
        </div>
      </div>

      {moveHere && (
        <Button variant="primary" className="mb-3 w-full" disabled={busy} onClick={() => run(moveHere)}>
          Hierhin gehen
        </Button>
      )}

      <h3 className="mb-1 text-xs font-semibold tracking-wide text-muted uppercase">Was man hier tun kann</h3>
      <ul className="mb-3 flex flex-col gap-2">
        {capabilities.map((c) => {
          const options = variants(c.type);
          const reason = options.length ? null : blockedReason(c.type, place, view, data, legal) ?? "Gerade nicht möglich";
          return (
            <li key={c.type} className="rounded-xl bg-panel-2 p-2">
              <p className="text-sm font-semibold">
                {c.icon} {c.label}
              </p>
              <p className="text-xs text-muted">{c.hint}</p>
              {options.map((a, i) => (
                <Button key={i} variant="primary" className="mt-1 w-full text-left" disabled={busy} onClick={() => run(a)}>
                  {labels.action(a)}
                </Button>
              ))}
              {c.type === "sell" && options.length > 0 && (
                <p className="mt-1 text-xs text-muted">Einzelne Karten: in der Hand antippen und „Verkaufen“ wählen.</p>
              )}
              {reason && <p className="mt-1 text-xs text-danger/90">⛔ {reason}</p>}
            </li>
          );
        })}
      </ul>

      {myPlace !== place && view.turn.player === me?.id && !view.pending && (
        <div className="mb-3 rounded-xl border border-line p-2 text-sm">
          <p>
            Normal kommst du nur per Würfel hierher (bei {diceFor(data, place).join(" oder ")}).
          </p>
          {cautious ? (
            <Button className="mt-2 w-full" disabled={busy} onClick={() => run(cautious)}>
              Gezielt hierhin schleichen (2 Aktionen = ganzer Zug)
            </Button>
          ) : (
            <p className="mt-1 text-xs text-muted">Gezielt hinschleichen kostet 2 Aktionen – dafür reicht dein Zug nicht mehr.</p>
          )}
        </div>
      )}

      <h3 className="mb-1 text-xs font-semibold tracking-wide text-muted uppercase">Hier sind</h3>
      <div className="flex flex-wrap gap-2">
        {here.length === 0 && <span className="text-sm text-muted">niemand</span>}
        {here.map((p) => (
          <span key={p.id} className="flex items-center gap-1 rounded-full bg-panel-2 py-0.5 pr-2 pl-0.5 text-sm">
            <Picture img={assets.portrait(characterOf(p.id))} alt="" className="size-7 rounded-full" />
            {labels.player(p.id)}
          </span>
        ))}
      </div>
    </Sheet>
  );
}
