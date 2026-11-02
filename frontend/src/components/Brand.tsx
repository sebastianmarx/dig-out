import { assets } from "../lib/assets";
import { Picture } from "./ui";

export function Brand() {
  return (
    <div className="flex w-full items-center gap-3 sm:gap-4">
      <img src="/icon.svg" width={64} height={64} alt="" className="h-16 w-16 shrink-0" draggable={false} />
      <Picture img={assets.logo} alt="Dig Out" className="min-w-0 flex-1" />
    </div>
  );
}
