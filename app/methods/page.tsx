import type { Metadata } from "next";
import { Prose } from "@/components/Figure";
import { PageHeader, Section } from "@/components/PageHeader";
import { CLASS_LABEL, SOURCES, type Class } from "@/lib/provenance";

export const metadata: Metadata = { title: "Method" };

const CLASS_NOTES: Record<Class, string> = {
  official:
    "Published by a named authority and reproducible by opening their document. Rounding is applied where the analysis is insensitive below a digit, and the rounding is stated rather than implied.",
  derived:
    "Computed here from stated inputs, with the arithmetic given alongside the figure. If you disagree with a derived number, the disagreement is with an input, and the input is on the page.",
  engineering:
    "A standard physics or engineering parameter quoted with its typical range. These carry real spread; where a conclusion depends on where in the range the value sits, that dependence is stated.",
  estimate:
    "An order-of-magnitude figure held in place until the authoritative layer is wired in. Every conclusion resting on one is written to survive its replacement, or it is not drawn.",
};

const LIMITS: { title: string; body: string }[] = [
  {
    title: "No dispersion model",
    body: "The nitrogen section works entirely on the emission side. Converting emissions to deposition at a named receptor is what the official calculator exists for, and a plausible-looking imitation of it would be more dangerous than an obvious gap. What is claimed here is a ratio between two emission terms, which survives almost any dispersion assumption because both terms disperse from broadly the same place.",
  },
  {
    title: "The constraint-shape figure is a schematic",
    body: "Its curves are characteristic forms, not calibrated site models, and nothing anywhere reads a value off them. They exist to make one comparison visible: that four of the five respond to a reduction at source and the fifth has no source to reduce.",
  },
  {
    title: "The border is a straight chord",
    body: "The real frontier is not straight, the population beyond it is not uniform, and permeability is not a scalar — retail crosses far more easily than employment, which crosses more easily than healthcare. All three simplifications understate the finding rather than manufacture it.",
  },
  {
    title: "Occupancy dominates the energy ladder",
    body: "Collective modes are only as efficient as they are filled, and the all-day averages used here are lower than the peak-hour figures usually quoted. A bus at capacity beats a battery car comfortably; a bus at four passengers does not. The ladder uses observed averages because that is what a network actually delivers.",
  },
  {
    title: "Nothing here is a permit assessment",
    body: "This platform is a way of seeing which constraints are reducible. It is not an environmental impact assessment, a nitrogen calculation, an acoustic report or a siting study, and no figure on it should be carried into one.",
  },
];

const PIPELINE: { stage: string; detail: string }[] = [
  {
    stage: "Ingestion",
    detail:
      "National geodata services for building footprints, elevation and topography; the statistics office for population, dwellings and commuting; provincial and municipal portals for designations and policy. All are open services, so the ingestion layer needs credentials for none of them.",
  },
  {
    stage: "Storage and spatial operations",
    detail:
      "A relational store with spatial types, which is what makes the intersections this analysis depends on — habitat against distance band, dwelling against corridor, roof against elevation model — expressible as queries rather than as scripts.",
  },
  {
    stage: "Derivation",
    detail:
      "The typed data modules in this repository. Every figure is a value with a unit, a class and a source, and every computed figure is a function whose inputs are those values. There is no number in the interface that cannot be traced to one of them.",
  },
  {
    stage: "Presentation",
    detail:
      "Server-rendered pages, with the interactive figures as the only client components. The chart engines are split by task: a declarative grammar for anything with a standard form, and low-level drawing for the three figures that are geometry rather than charts.",
  },
];

export default function Page() {
  return (
    <div>
      <PageHeader index="06 · Method" title="Where every figure comes from">
        An analytical claim is only as strong as the weakest number feeding it, so the class of
        each figure travels with the figure rather than sitting in a footnote at the end. The
        four classes below are deliberately coarse. A finer taxonomy would invite the author to
        hide behind it.
      </PageHeader>

      <Section title="Classes">
        <dl className="grid gap-x-10 gap-y-6 sm:grid-cols-2">
          {(Object.keys(CLASS_NOTES) as Class[]).map((k) => (
            <div key={k} className="border-t border-rule pt-3">
              <dt className="text-[0.6875rem] uppercase tracking-widest text-ink-3">
                {CLASS_LABEL[k]}
              </dt>
              <dd className="mt-2 text-[0.875rem] leading-relaxed text-ink-2">
                {CLASS_NOTES[k]}
              </dd>
            </div>
          ))}
        </dl>
      </Section>

      <Section title="Sources">
        <div className="scroll-x">
          <table className="data-table">
            <thead>
              <tr>
                <th>Holder</th>
                <th style={{ textAlign: "left" }}>Dataset or document</th>
                <th style={{ textAlign: "left" }}>What is taken from it</th>
              </tr>
            </thead>
            <tbody>
              {Object.values(SOURCES).map((s) => (
                <tr key={s.key}>
                  <td style={{ whiteSpace: "normal", minWidth: "12rem" }}>
                    {s.url ? (
                      <a
                        href={s.url}
                        className="underline decoration-rule underline-offset-2 hover:decoration-current"
                        rel="noreferrer noopener"
                        target="_blank"
                      >
                        {s.holder}
                      </a>
                    ) : (
                      s.holder
                    )}
                  </td>
                  <td style={{ textAlign: "left", whiteSpace: "normal", minWidth: "16rem" }}>
                    {s.title}
                  </td>
                  <td style={{ textAlign: "left", whiteSpace: "normal", minWidth: "22rem" }}>
                    {s.takes}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section title="Pipeline">
        <ol className="mt-2">
          {PIPELINE.map((p, i) => (
            <li
              key={p.stage}
              className="grid gap-x-8 gap-y-2 border-t border-rule py-5 md:grid-cols-[10rem_1fr]"
            >
              <div>
                <span className="text-[0.6875rem] tabular-nums tracking-widest text-ink-3">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span className="ml-3 text-[0.9375rem] font-medium text-ink">{p.stage}</span>
              </div>
              <p className="max-w-[62ch] text-[0.875rem] leading-relaxed text-ink-2">
                {p.detail}
              </p>
            </li>
          ))}
        </ol>
      </Section>

      <Section title="Design rules the figures follow">
        <Prose>
          <p>
            Chrome is subtracted once, in a shared configuration, so no chart restates it:
            no domain lines, no tick marks, no frames, no legend boxes, and a single hairline
            grid on the measured axis only. Marks are thin. Touching fills are separated by a
            gap in the surface colour rather than by a stroke, because a stroke adds ink that
            is not data.
          </p>
          <p>
            Quantities that span orders of magnitude are plotted logarithmically, and where a
            logarithmic axis makes values unreadable the values are labelled directly — that
            is the one circumstance in which labelling every point is right rather than
            careless. There are no dual-axis charts anywhere on this site. Where a zero cannot
            be drawn on a logarithmic scale, it is stated in the caption instead of being
            nudged onto the scale.
          </p>
          <p>
            The categorical palette is three slots from a validated eight-slot order — the
            three that clear the colour-vision separation floor on the all-pairs test in both
            light and dark. Colour is never the only channel carrying identity: every
            multi-series chart has a legend, and the charts whose series colour sits below
            three-to-one against the surface carry a values table underneath. Dark mode is a
            second set of steps chosen against the dark surface, not an inversion of the light
            one.
          </p>
        </Prose>
      </Section>

      <Section title="Limits">
        <div className="mt-2">
          {LIMITS.map((l) => (
            <article key={l.title} className="border-t border-rule py-5">
              <h3 className="text-[0.9375rem] font-medium leading-snug text-ink">{l.title}</h3>
              <p className="mt-2 max-w-[68ch] text-[0.875rem] leading-relaxed text-ink-2">
                {l.body}
              </p>
            </article>
          ))}
        </div>
      </Section>
    </div>
  );
}
