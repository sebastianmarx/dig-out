import type { ButtonHTMLAttributes, CSSProperties, ReactNode } from "react";

import type { Img } from "../lib/assets";

type Variant = "primary" | "secondary" | "danger" | "ghost";

const VARIANTS: Record<Variant, string> = {
  primary: "bg-orange text-white hover:brightness-110",
  secondary: "bg-panel-2 text-ink hover:bg-line",
  danger: "bg-danger text-white hover:brightness-110",
  ghost: "bg-transparent text-muted hover:text-ink",
};

export function Button({
  variant = "secondary",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      className={`min-h-11 rounded-xl px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-40 ${VARIANTS[variant]} ${className}`}
      {...props}
    />
  );
}

export function Picture({ img, alt, className = "", style }: { img: Img; alt: string; className?: string; style?: CSSProperties }) {
  return <img src={img.src} srcSet={img.srcSet} alt={alt} className={className} style={style} draggable={false} />;
}

export function Sheet({ title, onClose, children }: { title: string; onClose?: () => void; children: ReactNode }) {
  return (
    <div className="fixed inset-0 z-40 flex items-end justify-center bg-black/60 sm:items-center" onClick={onClose}>
      <div
        role="dialog"
        aria-label={title}
        className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-t-2xl bg-panel p-4 pb-[max(1rem,env(safe-area-inset-bottom))] shadow-2xl sm:rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-bold">{title}</h2>
          {onClose && (
            <button className="min-h-11 min-w-11 text-2xl text-muted" aria-label="Schließen" onClick={onClose}>
              ×
            </button>
          )}
        </div>
        {children}
      </div>
    </div>
  );
}
