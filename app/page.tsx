import Link from "next/link";
import type { Route } from "next";
import { Figure, Lede, Prose, Stat } from "@/components/Figure";
import { ConstraintShapes } from "@/components/d3/ConstraintShapes";
import { CITY, FRAME } from "@/data/city";
import { THESIS } from "@/data/constraints";
import { BACKGROUND_DEPOSITION, HABITATS } from "@/data/nitrogen";
import { MODES, pkmPerKWh } from "@/data/mobility";
import { catchmentRatio } from "@/data/border";
import { sig } from "@/lib/provenance";

const bog = HABITATS[0];
const exceedance = BACKGROUND_DEPOSITION.value / bog.kdw;
const best = MODES.reduce((a, b) => (pkmPerKWh(b) > pkmPerKWh(a) ? b : a));
const worst = MODES.reduce((a, b) => (pkmPerKWh(b) < pkmPerKWh(a) ? b : a));
const ladderSpan = pkmPerKWh(best) / pkmPerKWh(worst);
const borderLoss = 1 - catchmentRatio(20, 0);

const NEXT: { href: Route; label: string; blurb: string }[] = [
  {
    href: "/constraints",
    label: "The seven limits",
    blurb: "Which limits are lines on a map, which are measurements, and what can be done about each.",
  },
  {
    href: "/nitrogen",
    label: "Nitrogen",
    blurb: "Why the allowance is zero, and where a home's nitrogen really comes from.",
  },
  {
    href: "/mobility",
    label: "Mobility",
    blurb: "How much energy each way of getting around uses, and what the hill costs a cyclist.",
  },
  {
    href: "/access",
    label: "Access",
    blurb: "Why how far people will travel to a station matters more than how many stations there are.",
  },
  {
    href: "/border",
    label: "The border",
    blurb: "How much of the city's market the German border removes, and what opening it is worth.",
  },
  {
    href: "/energy",
    label: "Energy",
    blurb: "How much land wind and solar need, and why the process keeps picking the hungrier one.",
  },
  {
    href: "/cape-town",
    label: "Cape Town",
    blurb: "The other city in this project, and why it has the opposite problem.",
  },
  {
    href: "/compare",
    label: "Both cities",
    blurb: "Cape Town and Enschede next to each other, and the three things they share.",
  },
  {
    href: "/methods",
    label: "Sources",
    blurb: "Where every number comes from, and what this analysis gets wrong.",
  },
];

export default function Page() {
  return (
    <div>
      <header className="mb-16 max-w-[62ch]">
        <p className="mb-4 text-[0.6875rem] uppercase tracking-widest text-ink-3">
          Enschede · {CITY.region}
        </p>
        <h1 className="mb-6 text-[2.25rem] font-semibold leading-[1.15] tracking-tight text-ink sm:text-[2.75rem]">
          What actually stops Enschede building
        </h1>
        <Lede>
          Enschede has plenty of land and still cannot build much on it. People usually blame
          the lines on the planning map — the settlement boundary, the nature areas, the
          German border four kilometres away. Those lines are real, but they are not the
          problem. The problem is a set of measurements: nitrogen in the air, noise at the
          window, risk near a pipeline, how long water takes to reach a well. That difference
          matters, because you can argue about a line but you can actually bring a
          measurement down — and bringing it down helps everywhere at once.
        </Lede>
      </header>

      <section className="mb-16 grid gap-x-10 gap-y-8 sm:grid-cols-2 lg:grid-cols-4">
        <Stat
          label="Regional load ÷ raised-bog tolerance"
          value={`${exceedance.toFixed(1)}×`}
          note={`${BACKGROUND_DEPOSITION.value.toLocaleString("en-GB")} against a critical value of ${bog.kdw} mol N per hectare per year, at a habitat inside the municipal boundary.`}
          accent
        />
        <Stat
          label="Permitted increase once exceeded"
          value="0.00"
          unit="mol N/ha/yr"
          note="No de minimis allowance. The test is whether a project rounds to zero, which is a detection limit rather than a budget."
        />
        <Stat
          label="Span of the mobility energy ladder"
          value={`${ladderSpan.toFixed(0)}×`}
          note={`From ${worst.label.toLowerCase()} to ${best.label.toLowerCase()}, measured in passenger-kilometres delivered per kilowatt-hour.`}
        />
        <Stat
          label="Twenty-kilometre catchment lost to the border"
          value={`${(borderLoss * 100).toFixed(0)}%`}
          note="Pure geometry, before any question of whether the frontier is open. Every fixed cost in the city amortises over the remainder."
        />
      </section>

      <Figure
        n="01"
        title="What each limit looks like as you move away from its source"
        deck="Intensity as a multiple of each constraint's own threshold, against distance from its source. The pale curve is the same constraint after a thirty per cent reduction at source. Schematic: these are characteristic forms, not calibrated site models, and nothing downstream reads a value from them."
        klass="derived"
        sources={["aerius", "provOverijssel"]}
        note="Four of the five respond to a reduction at source. The fifth has no source term at all — it is a line on a map, and the only thing that can be done with a line is to argue about where it goes. Planning practice spends most of its attention on the fifth kind."
      >
        <ConstraintShapes />
      </Figure>

      <section className="mb-16 mt-20">
        <h2 className="mb-6 border-t border-rule pt-3 text-[1.25rem] font-semibold tracking-tight text-ink">
          What follows
        </h2>
        <Prose>
          <p className="text-ink">{THESIS.claim}</p>
        </Prose>
        <ol className="mt-8 grid gap-x-10 gap-y-7 sm:grid-cols-2">
          {THESIS.corollaries.map((c, i) => (
            <li key={i} className="border-t border-rule pt-3">
              <span className="text-[0.6875rem] tabular-nums tracking-widest text-ink-3">
                {String(i + 1).padStart(2, "0")}
              </span>
              <p className="mt-2 text-[0.9375rem] leading-relaxed text-ink-2">{c}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="mb-16 mt-20">
        <h2 className="mb-6 border-t border-rule pt-3 text-[1.25rem] font-semibold tracking-tight text-ink">
          Why this city
        </h2>
        <Prose>
          <p>
            Enschede has {sig(CITY.landArea.value, 3)} km² of land and about{" "}
            {(CITY.population.value / 1000).toFixed(0)} thousand people. That is not a land
            shortage. But it also has a protected bog on its own edge, the German border
            inside commuting distance, its drinking water directly under the built-up area,
            and thirty metres of hill in a country that has almost none. Each of those turns
            into a limit, and only one of them is a line on a map.
          </p>
        </Prose>
        <dl className="mt-8 grid gap-x-10 gap-y-8 sm:grid-cols-2">
          {FRAME.map((f) => (
            <div key={f.title} className="border-t border-rule pt-3">
              <dt className="text-[0.9375rem] font-medium leading-snug text-ink">{f.title}</dt>
              <dd className="mt-2 text-[0.875rem] leading-relaxed text-ink-2">{f.body}</dd>
            </div>
          ))}
        </dl>
      </section>

      <nav className="mt-20">
        <h2 className="mb-6 border-t border-rule pt-3 text-[1.25rem] font-semibold tracking-tight text-ink">
          Sections
        </h2>
        <ul className="grid gap-x-10 gap-y-6 sm:grid-cols-2 lg:grid-cols-3">
          {NEXT.map((s) => (
            <li key={s.href} className="border-t border-rule pt-3">
              <Link href={s.href} className="group block">
                <span className="text-[0.9375rem] font-medium text-ink group-hover:underline">
                  {s.label}
                </span>
                <span className="mt-1.5 block text-[0.8125rem] leading-relaxed text-ink-2">
                  {s.blurb}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}
