import { Button, Picture, Sheet } from "../../components/ui";
import { assets } from "../../lib/assets";
import { PENDING_TITLES } from "../../lib/labels";
import type { PendingOption } from "../../lib/types";
import { useCountdown, useGame } from "./useGame";

/** Modal for decisions that are mine to make (except discarding, which uses the hand selection). */
export function DecisionDialog({ selected }: { selected: string[] }) {
  const { view, game, legal, labels, act, busy, me } = useGame();
  const seconds = useCountdown(game.deadline);
  const pending = view.pending;
  if (!labels || !me || !pending || pending.player !== me.id || pending.kind === "discard") return null;

  const d = pending.data;

  if (pending.kind === "choose_place") {
    // Non-modal: the board stays visible with both reachable rooms glowing.
    return (
      <div className="fixed inset-x-2 bottom-56 z-30 mx-auto flex max-w-md flex-col gap-2 rounded-2xl border border-lamp bg-panel/95 p-3 shadow-2xl">
        <p className="flex items-center gap-2 text-sm font-semibold">
          <Picture img={assets.dice(Number(d.roll))} alt="" className="size-8" />
          Gewürfelt: {String(d.roll)} – wohin? Tippe einen leuchtenden Raum.
        </p>
        <div className="flex gap-2">
          {legal.map((a, i) => (
            <Button key={i} variant={a.type === "reroll" ? "secondary" : "primary"} className="flex-1" disabled={busy} onClick={() => act(a)}>
              {labels.action(a)}
            </Button>
          ))}
        </div>
      </div>
    );
  }

  let context: string | null = null;
  switch (pending.kind) {
    case "extort_response":
      context = `${labels.player(d.attacker)} will deine ${labels.tool(d.tool)} und zeigt ${labels.card(d.weapon)}.`;
      break;
    case "combat":
      context = `Du musst ${d.owed} Waffe(n) spielen – oder aufgeben. Es geht um: ${labels.tool(d.tool)}.`;
      break;
    case "beaten":
      context = `${labels.player(d.source)} verpasst dir ${d.amount} Prügel.`;
      break;
  }

  if (pending.kind === "choose_card") {
    const options = (d.options as PendingOption[]) ?? [];
    const phone = d.mode === "phone";
    const give = selected[0];
    return (
      <Sheet title={PENDING_TITLES.choose_card}>
        <p className="mb-3 text-sm text-muted">
          {phone ? "Wähle unten eine eigene Karte zum Tauschen und dann eine Karte hier." : "Wähle eine Karte, die du nimmst."}
        </p>
        <div className="grid grid-cols-3 gap-2">
          {options.map((o) => (
            <button
              key={o.id}
              disabled={busy || (phone && !give)}
              onClick={() => act({ type: "pick_card", card: o.id, give: phone ? give : null })}
              className="flex flex-col items-center rounded-lg border border-line p-1 disabled:opacity-40"
            >
              <Picture img={assets.card(o.card)} alt="" className="aspect-square w-full" />
              <span className="text-xs">{labels.card(o.card)}</span>
              <span className="text-[10px] text-muted">{labels.player(o.owner)}</span>
            </button>
          ))}
        </div>
      </Sheet>
    );
  }

  return (
    <Sheet title={`${PENDING_TITLES[pending.kind]}${seconds !== null ? ` · ${seconds}s` : ""}`}>
      {context && <p className="mb-3 text-sm">{context}</p>}
      <div className="flex flex-col gap-2">
        {legal.map((a, i) => (
          <Button
            key={i}
            disabled={busy}
            variant={a.type === "yield" || a.type === "take_beating" ? "secondary" : "primary"}
            onClick={() => act(a)}
          >
            {labels.action(a)}
          </Button>
        ))}
      </div>
    </Sheet>
  );
}
