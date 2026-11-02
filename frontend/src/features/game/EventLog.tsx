import { Sheet } from "../../components/ui";
import { useStore } from "../../lib/store";
import { useGame } from "./useGame";

export function EventLog({ onClose }: { onClose: () => void }) {
  const log = useStore((s) => s.log);
  const { labels } = useGame();
  if (!labels) return null;
  const lines = [...log]
    .reverse()
    .map(({ id, event }) => [id, labels.event(event)] as const)
    .filter(([, text]) => text);

  return (
    <Sheet title="Verlauf" onClose={onClose}>
      <ol className="flex flex-col gap-1 text-sm">
        {lines.length === 0 && <li className="text-muted">Noch nichts passiert.</li>}
        {lines.map(([id, text]) => (
          <li key={id} className={text!.startsWith("—") ? "pt-2 font-semibold text-lamp" : ""}>
            {text}
          </li>
        ))}
      </ol>
    </Sheet>
  );
}
