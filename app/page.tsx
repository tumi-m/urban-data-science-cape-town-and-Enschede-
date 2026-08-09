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
    label: "The constraint taxonomy",
    blurb: "Which of Enschede's limits are fields, which are boundaries, and what each responds to.",
  },
  {
    href: "/nitrogen",
    label: "Nitrogen",
    blurb: "A threshold of zero, and where a dwelling's nitrogen actually comes from.",
  },
  {
    href: "/mobility",
    label: "Mobility",
    blurb: "Passenger-kilometres per kilowatt-hour, and what the ridge costs a rider.",
  },
  {
    href: "/access",
    label: "Access",
    blurb:
      "Why the station buffer radius is a policy variable, and why land is the wrong denominator.",
  },
  {
    href: "/border",
    label: "The border",
    blurb: "A catchment cut by a chord, and the return on institutional work.",
  },
  {
    href: "/energy",
    label: "Energy",
    blurb: "Land per terawatt-hour, and why the search process selects the land-hungry option.",
  },
  {
    href: "/methods",
    label: "Method and provenance",
    blurb: "Where every figure comes from and what would change it.",
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
          The binding constraints are fields, not boundaries
        </h1>
        <Lede>
          Enschede is normally described through its edges: a settlement boundary, a nature
          network, a national frontier four kilometres from the centre. Those edges are real
          and they are not what stops the city building. What stops it is a set of continuous
          quantities with thresholds — deposited nitrogen, sound level, fatality probability,
          groundwater travel time — that a map can only show as a contour. The distinction
          decides what can be done about them: a boundary can be moved or fought, and a field
          can be lowered.
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
        title="What a constraint looks like when you plot it against distance"
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
          Why Enschede
        </h2>
        <Prose>
          <p>
            A constraint analysis is only interesting where the constraints bind, and Enschede
            binds in an unusual combination. It has {sig(CITY.landArea.value, 3)} km² of
            municipal land and roughly {(CITY.population.value / 1000).toFixed(0)} thousand
            people, which is not a land shortage. It also has a raised bog on its own edge, a
            national frontier inside its commuting radius, its drinking water directly beneath
            its built-up area, and thirty metres of relief in a country that has almost none.
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
