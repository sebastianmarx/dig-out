import { Button, Picture } from "../../components/ui";
import { assets } from "../../lib/assets";
import { useGame } from "./useGame";

interface Props {
  selected: string[];
  setSelected: (ids: string[]) => void;
}

/** Own hand. Tapping selects cards for free choices: sell, dig, discard, train, play. */
export function Hand({ selected, setSelected }: Props) {
  const { me, view, data, labels, legal, act, busy } = useGame();
  if (!me || !data || !labels) return <div className="bg-panel p-3 text-center text-sm text-muted">Zuschauer</div>;

  const toggle = (id: string) => setSelected(selected.includes(id) ? selected.filter((s) => s !== id) : [...selected, id]);
  const defs = selected.map((id) => me.hand.find((c) => c.id === id)?.card ?? "");
  const single = selected.length === 1 ? data.cards[defs[0]] : null;
  const has = (type: string) => legal.some((a) => a.type === type);
  const pending = view.pending?.player === me.id ? view.pending : null;

  const buttons: [string, () => void][] = [];
  if (selected.length) {
    if (pending?.kind === "discard" && selected.length === pending.data.count)
      buttons.push(["Abwerfen", () => act({ type: "discard", cards: selected })]);
    if (!pending && has("sell")) buttons.push([`Verkaufen (${selected.length})`, () => act({ type: "sell", cards: selected })]);
    if (!pending && has("dig") && defs.every((d) => data.cards[d]?.kind === "tool"))
      buttons.push(["Graben", () => act({ type: "dig", tools: selected })]);
    if (single && !pending) {
      for (const a of legal.filter((x) => (x.type === "play_card" && x.card === selected[0]) || (x.type === "train" && x.weapon === selected[0])))
        buttons.push([labels.action(a), () => act(a)]);
    }
  }

  return (
    <div className="border-t border-line bg-panel pb-[env(safe-area-inset-bottom)]">
      {(selected.length > 0 || pending?.kind === "discard") && (
        <div className="flex flex-wrap items-center gap-1.5 px-2 pt-2">
          <span className="flex-1 text-xs text-muted">
            {pending?.kind === "discard"
              ? `Wähle ${pending.data.count} Karte(n) zum Abwerfen (${selected.length} gewählt)`
              : single
                ? `${single.name}${single.text ? ` – ${single.text}` : ""}`
                : `${selected.length} Karten gewählt`}
          </span>
          {buttons.map(([label, run]) => (
            <Button key={label} variant="primary" disabled={busy} className="min-h-9 py-1" onClick={run}>
              {label}
            </Button>
          ))}
        </div>
      )}
      <div className="flex gap-1.5 overflow-x-auto p-2">
        <div
          className={`flex w-20 shrink-0 flex-col justify-between rounded-lg border p-1.5 text-[11px] leading-tight ${
            me.background_revealed ? "border-line opacity-60" : "border-teal bg-teal/10"
          }`}
          title={data.backgrounds[me.background]?.text}
        >
          <span className="text-muted">Hintergrund</span>
          <span className="font-semibold">{labels.background(me.background)}</span>
          <span className="text-[10px] text-muted">{me.background_revealed ? "aufgedeckt" : "verdeckt"}</span>
        </div>
        {me.hand.map(({ id, card }) => {
          const def = data.cards[card];
          const isSelected = selected.includes(id);
          return (
            <button
              key={id}
              onClick={() => toggle(id)}
              title={def?.text}
              className={`relative flex w-20 shrink-0 flex-col items-center rounded-lg border p-1 transition ${
                isSelected ? "-translate-y-1.5 border-lamp bg-lamp/15" : "border-line bg-night/40"
              }`}
            >
              <Picture img={assets.card(card)} alt="" className="aspect-square w-full" />
              <span className="line-clamp-2 text-center text-[11px] leading-tight">{def?.name ?? card}</span>
              <span className="absolute top-1 right-1 rounded bg-black/60 px-1 text-[10px]">🚬{def?.value}</span>
            </button>
          );
        })}
        {me.hand.length === 0 && <p className="p-3 text-sm text-muted">Keine Karten</p>}
      </div>
    </div>
  );
}
