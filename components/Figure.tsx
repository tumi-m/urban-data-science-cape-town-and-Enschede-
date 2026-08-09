import type { ReactNode } from "react";
import { SOURCES, type Class, type SourceKey, CLASS_LABEL } from "@/lib/provenance";

/**
 * The figure frame.
 *
 * A number is not an argument until the reader can see where it came from, so
 * the provenance line is part of the figure rather than a footnote at the end
 * of the page. It is set small and quiet — it should be available without
 * competing with the marks.
 *
 * `table` exists for two reasons. It is the accessible reading of any chart,
 * and it is the required relief wherever a series colour sits below three to
 * one against the surface. Both are satisfied by the same element.
 */
export function Figure({
  n,
  title,
  deck,
  klass,
  sources,
  children,
  table,
  note,
}: {
  n?: string;
  title: string;
  deck?: string;
  klass?: Class;
  sources?: SourceKey[];
  children: ReactNode;
  table?: ReactNode;
  note?: string;
}) {
  return (
    <figure className="my-12">
      <figcaption className="mb-5 border-t border-rule pt-3">
        <div className="flex items-baseline gap-3">
          {n && (
            <span className="shrink-0 text-[0.6875rem] font-medium tracking-widest text-ink-3">
              {n}
            </span>
          )}
          <h3 className="text-[0.9375rem] font-semibold leading-snug text-ink">{title}</h3>
        </div>
        {deck && (
          <p className="mt-1.5 max-w-[62ch] text-[0.8125rem] leading-relaxed text-ink-2">
            {deck}
          </p>
        )}
      </figcaption>

      <div className="scroll-x">{children}</div>

      {note && (
        <p className="mt-4 max-w-[62ch] text-[0.8125rem] leading-relaxed text-ink-2">{note}</p>
      )}

      {table && (
        <details className="mt-4 group">
          <summary className="cursor-pointer list-none text-[0.6875rem] uppercase tracking-widest text-ink-3 hover:text-ink-2">
            <span className="group-open:hidden">Values ▸</span>
            <span className="hidden group-open:inline">Values ▾</span>
          </summary>
          <div className="scroll-x mt-3">{table}</div>
        </details>
      )}

      {(klass || sources?.length) && (
        <p className="mt-4 flex flex-wrap items-baseline gap-x-2 gap-y-1 text-[0.6875rem] leading-relaxed text-ink-3">
          {klass && <span className="uppercase tracking-widest">{CLASS_LABEL[klass]}</span>}
          {klass && sources?.length ? <span aria-hidden>·</span> : null}
          {sources?.map((k, i) => (
            <span key={k}>
              {SOURCES[k].holder}
              {i < sources.length - 1 ? "," : ""}
            </span>
          ))}
        </p>
      )}
    </figure>
  );
}

/** A number that is the chart. Used instead of a one-bar bar chart, never beside one. */
export function Stat({
  label,
  value,
  unit,
  note,
  accent = false,
}: {
  label: string;
  value: string;
  unit?: string;
  note?: string;
  accent?: boolean;
}) {
  return (
    <div className="border-t border-rule pt-3">
      <div className="text-[0.6875rem] uppercase tracking-widest text-ink-3">{label}</div>
      <div className="mt-2 flex items-baseline gap-1.5">
        <span
          className="text-[2rem] font-semibold leading-none tracking-tight tabular-nums"
          style={accent ? { color: "var(--series-2)" } : undefined}
        >
          {value}
        </span>
        {unit && <span className="text-[0.8125rem] text-ink-2">{unit}</span>}
      </div>
      {note && <p className="mt-2 text-[0.75rem] leading-relaxed text-ink-3">{note}</p>}
    </div>
  );
}

/** Reading column. Set once so no page invents its own measure. */
export function Prose({ children }: { children: ReactNode }) {
  return (
    <div className="max-w-[68ch] space-y-4 text-[0.9375rem] leading-[1.7] text-ink-2">
      {children}
    </div>
  );
}

export function Lede({ children }: { children: ReactNode }) {
  return (
    <p className="max-w-[62ch] text-[1.0625rem] leading-[1.65] text-ink">{children}</p>
  );
}
