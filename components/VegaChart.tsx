"use client";

import { useEffect, useRef, useState } from "react";
import embed, { type VisualizationSpec, type Result } from "vega-embed";
import { readTokens, vegaConfig, type Tokens } from "@/lib/vegaTheme";

/**
 * Declarative charts.
 *
 * Vega-Lite carries every chart whose form is a standard one — the grammar
 * expresses those faster than hand-written SVG and, more usefully, expresses
 * them the same way every time. The bespoke figures are elsewhere, in D3,
 * where low-level control is worth the cost of writing it.
 *
 * The spec arrives as a function of the resolved tokens rather than as a
 * literal, so a chart that needs to name a colour names the same one the rest
 * of the page is using in whichever mode is live.
 */
export function VegaChart({
  spec,
  ariaLabel,
  minHeight = 260,
}: {
  spec: (t: Tokens) => VisualizationSpec;
  ariaLabel: string;
  minHeight?: number;
}) {
  const host = useRef<HTMLDivElement>(null);
  const [themeTick, setThemeTick] = useState(0);

  // Re-embed when the effective colour scheme changes, in either of the two
  // ways it can change: the OS preference, or the document's own stamp.
  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const bump = () => setThemeTick((n) => n + 1);
    mq.addEventListener("change", bump);
    const obs = new MutationObserver(bump);
    obs.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });
    return () => {
      mq.removeEventListener("change", bump);
      obs.disconnect();
    };
  }, []);

  useEffect(() => {
    const el = host.current;
    if (!el) return;
    let view: Result | undefined;
    let cancelled = false;

    const tokens = readTokens();
    embed(el, spec(tokens), {
      actions: false,
      renderer: "svg",
      config: vegaConfig(tokens),
      tooltip: { theme: "custom" },
    })
      .then((r) => {
        if (cancelled) r.finalize();
        else view = r;
      })
      .catch(() => {
        /* A chart that fails to render must not take the page with it. */
      });

    return () => {
      cancelled = true;
      view?.finalize();
    };
  }, [spec, themeTick]);

  // Two divs rather than one: the embed overwrites the aria-label on whatever
  // container it is handed, replacing a sentence that describes the finding
  // with the string "Vega visualization". The outer element keeps the label
  // and, being role="img", hides the generated tree from assistive technology.
  return (
    <div role="img" aria-label={ariaLabel} className="w-full">
      <div ref={host} className="w-full" style={{ minHeight }} />
    </div>
  );
}
