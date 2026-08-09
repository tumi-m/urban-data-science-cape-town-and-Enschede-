import type { Metadata } from "next";
import { Figure, Prose } from "@/components/Figure";
import { PageHeader, Section } from "@/components/PageHeader";
import { ConstraintShapes } from "@/components/d3/ConstraintShapes";
import { CONSTRAINTS, THESIS } from "@/data/constraints";
import { SOURCES } from "@/lib/provenance";

export const metadata: Metadata = { title: "Constraints" };

const fields = CONSTRAINTS.filter((c) => c.shape === "field");
const polygons = CONSTRAINTS.filter((c) => c.shape === "polygon");

export default function Page() {
  return (
    <div>
      <PageHeader index="01 · Constraints" title="Seven limits, two shapes">
        A geographic information system stores what its formats can hold, and the dominant
        format holds polygons. So constraints arrive as polygons, and the habit of thought
        that follows is that a constraint is a place. Most of the limits that actually bind
        in Enschede are not places. They are quantities defined everywhere, drawn as polygons
        only because someone traced the contour where the quantity crosses a number.
      </PageHeader>

      <Figure
        n="01"
        title="Fields decay; boundaries step"
        deck="Intensity as a multiple of each constraint's own threshold, against distance from source, with the same constraint after a thirty per cent reduction at source shown pale. Schematic — the forms are the finding, not the values."
        klass="derived"
        sources={["aerius", "provOverijssel"]}
      >
        <ConstraintShapes />
      </Figure>

      <Section title="The five that are fields">
        <Prose>
          <p>
            Each of these is a quantity with a source, a decay, and a threshold. Each has a
            lever that moves the whole surface rather than one location on it. And each is
            routinely handled as though it were the polygon that represents it, which converts
            a problem with an engineering answer into a problem with only a political one.
          </p>
        </Prose>
        <div className="mt-8 space-y-0">
          {fields.map((c, i) => (
            <ConstraintEntry key={c.id} c={c} n={i + 1} />
          ))}
        </div>
      </Section>

      <Section title="The two that really are boundaries">
        <Prose>
          <p>
            These two are genuine polygons: inside or outside, with nothing underneath to
            reduce. They are also the two that dominate public argument about growth in the
            city, which is the mismatch this platform exists to point at. The designated areas
            explain where Enschede may not build. They do not explain why it cannot.
          </p>
        </Prose>
        <div className="mt-8">
          {polygons.map((c, i) => (
            <ConstraintEntry key={c.id} c={c} n={fields.length + i + 1} />
          ))}
        </div>
      </Section>

      <Section title="The consequence">
        <ol className="grid gap-x-10 gap-y-7 sm:grid-cols-2">
          {THESIS.corollaries.map((c, i) => (
            <li key={i} className="border-t border-rule pt-3">
              <span className="text-[0.6875rem] tabular-nums tracking-widest text-ink-3">
                {String(i + 1).padStart(2, "0")}
              </span>
              <p className="mt-2 text-[0.9375rem] leading-relaxed text-ink-2">{c}</p>
            </li>
          ))}
        </ol>
      </Section>
    </div>
  );
}

function ConstraintEntry({
  c,
  n,
}: {
  c: (typeof CONSTRAINTS)[number];
  n: number;
}) {
  return (
    <article className="border-t border-rule py-6">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className="text-[0.6875rem] tabular-nums tracking-widest text-ink-3">
          {String(n).padStart(2, "0")}
        </span>
        <h3 className="text-[1.0625rem] font-medium tracking-tight text-ink">{c.label}</h3>
        <span
          className="rounded-full border px-2 py-0.5 text-[0.625rem] uppercase tracking-widest"
          style={{
            borderColor: c.shape === "field" ? "var(--series-1)" : "var(--rule)",
            color: c.shape === "field" ? "var(--series-1)" : "var(--text-muted)",
          }}
        >
          {c.shape}
        </span>
      </div>

      <dl className="mt-4 grid gap-x-10 gap-y-5 md:grid-cols-2">
        <Row term="Quantity">
          {c.quantity} <span className="text-ink-3">({c.unit})</span>
        </Row>
        <Row term="Threshold">{c.threshold}</Row>
        <Row term="Effect on development">{c.effect}</Row>
        <Row term={c.shape === "field" ? "Reduced by" : "Reducible?"}>{c.reducedBy}</Row>
      </dl>

      <p className="mt-4 text-[0.6875rem] text-ink-3">{SOURCES[c.source].holder}</p>
    </article>
  );
}

function Row({ term, children }: { term: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-[0.6875rem] uppercase tracking-widest text-ink-3">{term}</dt>
      <dd className="mt-1.5 text-[0.875rem] leading-relaxed text-ink-2">{children}</dd>
    </div>
  );
}
