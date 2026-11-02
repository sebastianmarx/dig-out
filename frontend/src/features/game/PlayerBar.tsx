import { Picture } from "../../components/ui";
import { assets } from "../../lib/assets";
import { useGame } from "./useGame";

export function PlayerBar() {
  const { view, labels, characterOf, colorOf } = useGame();
  if (!labels) return null;
  const decider = view.pending?.player ?? view.turn.player;

  return (
    <div className="flex gap-2 overflow-x-auto border-b border-line bg-panel px-2 py-2">
      {view.players.map((p) => {
        const stage = Math.min(5, Math.floor((p.points / view.win_points) * 5));
        const active = p.id === decider && view.phase === "running";
        return (
          <div
            key={p.id}
            className={`flex min-w-36 shrink-0 gap-2 rounded-xl p-1.5 ${active ? "bg-panel-2 ring-2 ring-lamp" : "bg-night/40"}`}
          >
            <Picture
              img={assets.portrait(characterOf(p.id))}
              alt=""
              className="size-11 shrink-0 rounded-full border-2 bg-panel object-cover"
              style={{ borderColor: colorOf(p.id) }}
            />
            <div className="min-w-0 text-xs leading-tight">
              <p className="truncate font-semibold" style={{ color: colorOf(p.id) }}>
                {labels.player(p.id)}
              </p>
              <Picture img={assets.tunnel(stage)} alt="" className="my-0.5 h-4 w-16 rounded-sm object-cover" />
              <p className="text-muted">
                <span className="text-ink">{p.points}</span>/{view.win_points} Pkt ·{" "}
                {p.hand_count === null ? "?" : p.hand_count} Karten
              </p>
              <p className="text-muted">
                {"🩹".repeat(p.beatings)}
                {p.beatings > 0 && " "}
                🚬 {p.cigarettes}
                {p.gang && (
                  <span className="ml-1 inline-flex items-center gap-0.5 text-lamp">
                    <Picture img={assets.gang(p.gang)} alt="" className="size-4" />
                    {labels.gang(p.gang)}
                  </span>
                )}
                {p.protected && <span className="ml-1">🛡</span>}
              </p>
              {p.background && <p className="truncate text-teal">{labels.background(p.background)}</p>}
            </div>
          </div>
        );
      })}
    </div>
  );
}
