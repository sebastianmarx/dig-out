import { useRef, useState } from "react";

import { Picture } from "../../components/ui";
import { assets } from "../../lib/assets";
import { diceFor, ROOM_ACTIONS } from "../../lib/rooms";
import { useStore } from "../../lib/store";
import type { PlayerPublic } from "../../lib/types";
import { useGame } from "./useGame";

const FIGURE_SCALE = 1.3; // figures a bit larger than true scale so they read on phones
const STANDEE_UNITS = 2.0; // the standee render frames 2 world units of height, feet 5 % above the bottom
const WALL_UNITS = 2.4;

/** The combined prison board: one render, rooms as tappable areas, figures standing in the rooms. */
export function Board({ onRoom }: { onRoom: (place: string) => void }) {
  const { view, data, legal, characterOf, colorOf, me } = useGame();
  const layout = useStore((s) => s.layout);
  const lastEvents = useStore((s) => s.lastEvents);
  const [zoom, setZoom] = useState(1);
  const scroller = useRef<HTMLDivElement>(null);
  if (!data || !layout) return <div className="p-6 text-center text-muted">Lade Spielplan…</div>;

  const { width: W, height: H } = layout.image;
  const raise = WALL_UNITS * layout.unit_height;
  const figureHeight = STANDEE_UNITS * layout.unit_height * FIGURE_SCALE;
  const targets = new Set(legal.filter((a) => a.type === "choose_place").map((a) => String(a.place)));
  const myPlace = view.players.find((p) => p.id === me?.id)?.place;
  const decider = view.pending?.player ?? view.turn.player;
  const lastRoll = [...lastEvents].reverse().find((e) => e.type === "rolled")?.value as number | undefined;

  const figures: { player: PlayerPublic; x: number; y: number }[] = [];
  for (const [place, room] of Object.entries(layout.rooms)) {
    view.players
      .filter((p) => p.place === place)
      .sort((a, b) => a.seat - b.seat)
      .forEach((player, i) => {
        const [x, y] = room.slots[i % room.slots.length];
        figures.push({ player, x, y });
      });
  }
  figures.sort((a, b) => a.y - b.y); // back to front

  const toggleZoom = () => {
    const next = zoom === 1 ? 2 : 1;
    setZoom(next);
    const room = myPlace ? layout.rooms[myPlace] : null;
    requestAnimationFrame(() => {
      const el = scroller.current;
      if (el && room && next > 1) {
        el.scrollTo({
          left: room.label[0] * el.scrollWidth - el.clientWidth / 2,
          top: (room.label[1] - 0.15) * el.scrollHeight - el.clientHeight / 2,
        });
      }
    });
  };

  return (
    <div className="relative h-full">
      <div ref={scroller} className="h-full overflow-auto">
        <div
          className="relative mx-auto"
          style={{ width: `${zoom * 100}%`, maxWidth: zoom === 1 ? `${(W / H) * 62}vh` : undefined, aspectRatio: `${W} / ${H}` }}
        >
          <Picture img={assets.board} alt="Spielplan" className="absolute inset-0 h-full w-full" />

          <svg viewBox={`0 0 ${W} ${H}`} className="absolute inset-0 h-full w-full" aria-label="Räume">
            {Object.entries(layout.rooms).map(([place, room]) => {
              const [l, b, r, t] = room.outline;
              const up = (p: [number, number]): [number, number] => [p[0], p[1] - raise];
              const points = [l, b, r, up(r), up(t), up(l)].map(([x, y]) => `${x * W},${y * H}`).join(" ");
              const isTarget = targets.has(place);
              return (
                <polygon
                  key={place}
                  points={points}
                  role="button"
                  aria-label={data.board.places.find((p) => p.id === place)?.name}
                  onClick={() => onRoom(place)}
                  className={`cursor-pointer transition ${isTarget ? "animate-pulse" : "fill-transparent hover:fill-white/10"}`}
                  style={{
                    fill: isTarget ? "rgba(255,207,138,0.28)" : undefined,
                    stroke: isTarget ? "#ffcf8a" : place === myPlace ? "rgba(255,255,255,0.35)" : "transparent",
                    strokeWidth: W * 0.0025,
                  }}
                />
              );
            })}
          </svg>

          {figures.map(({ player, x, y }) => (
            <Picture
              key={player.id}
              img={assets.standee(characterOf(player.id))}
              alt={player.name}
              className="pointer-events-none absolute max-w-none"
              style={{
                left: `${x * 100}%`,
                top: `${y * 100}%`,
                height: `${figureHeight * 100}%`,
                transform: "translate(-50%, -95%)",
                filter:
                  player.id === decider
                    ? `drop-shadow(0 0 5px ${colorOf(player.id)}) drop-shadow(0 0 2px ${colorOf(player.id)})`
                    : "drop-shadow(0 4px 3px rgba(0,0,0,.6))",
              }}
            />
          ))}
          {figures.map(({ player, x, y }) => (
            <span
              key={`tag-${player.id}`}
              className="pointer-events-none absolute -translate-x-1/2 translate-y-0.5 rounded px-1 text-[10px] leading-tight whitespace-nowrap text-white shadow sm:text-xs"
              style={{ left: `${x * 100}%`, top: `${y * 100}%`, background: colorOf(player.id) }}
            >
              {player.id === me?.id ? "Du" : player.name}
              {player.beatings > 0 && ` ${"🩹".repeat(player.beatings)}`}
            </span>
          ))}

          {Object.entries(layout.rooms).map(([place, room]) => {
            const def = data.board.places.find((p) => p.id === place)!;
            return (
              <button
                key={place}
                onClick={() => onRoom(place)}
                className={`absolute flex -translate-x-1/2 translate-y-1 items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] whitespace-nowrap shadow-lg sm:text-xs ${
                  targets.has(place) ? "border-lamp bg-lamp text-night" : "border-line bg-panel/90 text-ink"
                }`}
                style={{ left: `${room.label[0] * 100}%`, top: `${room.label[1] * 100}%` }}
              >
                {diceFor(data, place).map((f) => (
                  <Picture key={f} img={assets.dice(f)} alt={`Würfel ${f}`} className="size-3.5 sm:size-4" />
                ))}
                <span className="font-semibold">{def.name}</span>
                <span title={`Suchen: ${def.search} Karten`}>🔍{def.search}</span>
                {def.craft_allowed && <span title="Herstellen möglich">🔨</span>}
                {def.actions.map((a) => (
                  <span key={a} title={ROOM_ACTIONS[a]?.label}>
                    {ROOM_ACTIONS[a]?.icon}
                  </span>
                ))}
              </button>
            );
          })}
        </div>
      </div>

      <div className="pointer-events-none absolute inset-x-2 top-2 flex justify-between text-[11px] text-muted">
        <div className="pointer-events-auto flex items-center gap-2 rounded-xl bg-night/80 px-2 py-1">
          <button className="min-h-8 min-w-8 rounded-lg bg-panel-2 text-base" onClick={toggleZoom} aria-label="Zoom">
            {zoom === 1 ? "🔍" : "↩"}
          </button>
          <span>Stapel {view.search_deck}</span>
          {(["spoon", "pickaxe", "shovel", "knife"] as const).map((pile) => (
            <span key={pile} className="inline-flex items-center">
              <Picture img={assets.card(pile)} alt="" className="size-5" />
              {view.piles[pile]}
            </span>
          ))}
        </div>
        {lastRoll && (
          <div className="flex items-center gap-1 rounded-xl bg-night/80 px-2 py-1">
            <Picture img={assets.dice(lastRoll)} alt={`Würfel ${lastRoll}`} className="size-8" />
          </div>
        )}
      </div>
    </div>
  );
}
