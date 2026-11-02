import { Button, Picture, Sheet } from "../../components/ui";
import { assets } from "../../lib/assets";
import { gangRequirement } from "../../lib/rooms";
import { useGame } from "./useGame";

/** The six gangs: what each one is good at, what joining costs, who is in it. */
export function GangSheet({ onClose }: { onClose: () => void }) {
  const { view, data, labels, legal, act, busy, me } = useGame();
  if (!data || !labels) return null;
  const myGang = view.players.find((p) => p.id === me?.id)?.gang;
  const myTurn = view.turn.player === me?.id && !view.pending && view.phase === "running";

  return (
    <Sheet title="Gangs" onClose={onClose}>
      <p className="mb-3 text-sm text-muted">
        Jede Gang hat eine eigene Stärke. Beitreten kostet 1 Aktion und verschiedene Accessoires. Du kannst nur in einer
        Gang sein – wechselst du, geht deine alte Gangkarte zurück.
      </p>
      <ul className="flex flex-col gap-2">
        {Object.values(data.gangs).map((gang) => {
          const join = legal.find((a) => a.type === "join_gang" && a.gang === gang.id);
          const members = view.players.filter((p) => p.gang === gang.id);
          const left = view.gang_piles[gang.id] ?? 0;
          const reason =
            myGang === gang.id
              ? "Du bist Mitglied"
              : !myTurn
                ? "Beitreten nur in deinem Zug"
                : left === 0
                  ? "Keine Plätze mehr frei"
                  : view.turn.actions_left < 1
                    ? "Keine Aktion mehr übrig"
                    : "Dir fehlen passende Accessoires";
          return (
            <li key={gang.id} className={`flex gap-3 rounded-xl p-2 ${myGang === gang.id ? "bg-lamp/15 ring-1 ring-lamp" : "bg-panel-2"}`}>
              <Picture img={assets.gang(gang.id)} alt="" className="size-14 shrink-0" />
              <div className="min-w-0 flex-1 text-sm">
                <p className="font-bold">
                  {gang.name} <span className="text-xs font-normal text-muted">· {left} von {gang.cards} Plätzen frei</span>
                </p>
                <p>💪 {gang.text}</p>
                <p className="text-xs text-muted">Beitritt: {gangRequirement(data, gang.id)}</p>
                {members.length > 0 && (
                  <p className="text-xs text-muted">Mitglieder: {members.map((m) => labels.player(m.id)).join(", ")}</p>
                )}
                {join ? (
                  <Button
                    variant="primary"
                    className="mt-1 w-full"
                    disabled={busy}
                    onClick={() => {
                      act(join);
                      onClose();
                    }}
                  >
                    Beitreten (wirft ab: {(join.cards as string[]).map((c) => labels.card(labels.cardOf(c))).join(", ")})
                  </Button>
                ) : (
                  <p className="mt-1 text-xs text-danger/90">⛔ {reason}</p>
                )}
              </div>
            </li>
          );
        })}
      </ul>
    </Sheet>
  );
}
