import type { Metadata } from "next";
import { Figure, Prose, Stat } from "@/components/Figure";
import { PageHeader, Section } from "@/components/PageHeader";
import { CatchmentGeometry } from "@/components/d3/CatchmentGeometry";
import { CatchmentCurve, CatchmentCurveTable } from "@/components/charts/CatchmentCurve";
import {
  BORDER_DISTANCE_KM,
  PERMEABILITY_SCENARIOS,
  accessiblePopulation,
  catchmentRatio,
} from "@/data/border";

export const metadata: Metadata = { title: "The border" };

const observed = PERMEABILITY_SCENARIOS.find((s) => s.id === "current")!;
const integrated = PERMEABILITY_SCENARIOS.find((s) => s.id === "integrated")!;
const loss20 = 1 - catchmentRatio(20, 0);
const loss30 = 1 - catchmentRatio(30, 0);
const gain = accessiblePopulation(30, integrated.value) - accessiblePopulation(30, observed.value);

export default function Page() {
  return (
    <div>
      <PageHeader index="04 · Border" title="A catchment cut by a chord">
        Every piece of fixed infrastructure in a city — a rail terminus, a hospital, a
        university, a heat network — recovers its cost from the population inside some travel
        radius, and that population is normally proportional to the area of a disc. Enschede's
        disc is cut {BORDER_DISTANCE_KM} kilometres from its centre. The land beyond is not
        empty; it is institutionally separate, which is a different problem with a different
        remedy.
      </PageHeader>

      <section className="mb-4 grid gap-x-10 gap-y-8 sm:grid-cols-2 lg:grid-cols-4">
        <Stat
          label="Twenty-kilometre disc beyond the border"
          value={`${(loss20 * 100).toFixed(0)}%`}
          note="Pure geometry, independent of how open the frontier is."
        />
        <Stat
          label="Thirty-kilometre disc beyond the border"
          value={`${(loss30 * 100).toFixed(0)}%`}
          note="The loss grows with radius: a larger disc puts a larger share of itself past a fixed chord."
          accent
        />
        <Stat
          label="Effective catchment today, 30 km"
          value={`${(catchmentRatio(30, observed.value) * 100).toFixed(0)}%`}
          note="Of what an interior city of the same size would have, at the permeability currently observed."
        />
        <Stat
          label="Population unlocked by integration alone"
          value={`${Math.round(gain / 1000).toLocaleString("en-GB")}k`}
          note="Moving from today's permeability to a working cross-border labour market, at a thirty-kilometre radius. No construction involved."
        />
      </section>

      <Figure
        n="01"
        title="The geometry, and the membrane over it"
        deck="The shaded ground is the catchment the city can draw on. Ground east of the line counts only to the extent that the border is permeable. Adjust the radius and the permeability; the scenario buttons set permeability to the values used elsewhere on this page."
        klass="derived"
        sources={["cbs", "pdok"]}
        note="Permeability here is an institutional quantity, not a distance — recognition of qualifications, portability of social insurance, a single tariff and ticket, a rail service that does not change character at the frontier. It is the only term in this figure that policy can move without moving earth."
      >
        <CatchmentGeometry />
      </Figure>

      <Section title="The arithmetic">
        <Prose>
          <p>
            For a circle of radius <em>r</em> whose centre lies a distance <em>d</em> from a
            straight border, the area beyond the border is{" "}
            <code className="rounded bg-surface-2 px-1.5 py-0.5 text-[0.8125rem]">
              r² · arccos(d ⁄ r) − d · √(r² − d²)
            </code>
            . Effective catchment is the near area plus permeability times the far area. That
            is the whole model, and its transparency is the point: every judgement in it is
            visible and adjustable, and the only contestable input is the permeability.
          </p>
          <p>
            The behaviour worth noticing is that the loss <em>grows</em> with radius. At five
            kilometres the border costs Enschede almost nothing. At thirty it costs{" "}
            {(loss30 * 100).toFixed(0)} per cent. So the border does not take away the corner
            shop's market; it takes away the market for exactly those functions whose economics
            require a wide catchment — the specialist hospital department, the concert hall, the
            regional distribution centre, the university's non-residential intake. A city can
            lose its regional tier while its local tier looks perfectly healthy, and that is a
            failure mode that per-capita statistics do not show.
          </p>
        </Prose>
      </Section>

      <Figure
        n="02"
        title="Catchment against radius, by permeability"
        deck="Effective catchment as a percentage of the full disc an interior city would enjoy, at three permeabilities. Values labelled at the right-hand end of each line."
        klass="derived"
        sources={["cbs"]}
        table={<CatchmentCurveTable />}
      >
        <CatchmentCurve />
      </Figure>

      <Section title="What this reframes">
        <Prose>
          <p>
            Read alongside the rest of this platform, the border does something specific to the
            argument. Enschede's development capacity is limited by nitrogen, by noise, by
            safety contours and by groundwater — all of which are supply-side constraints on
            building. The border is a demand-side constraint, and it is the one nobody is
            required to model. It caps the catchment that would justify the density that the
            supply-side constraints make expensive.
          </p>
          <p>
            The two interact in a way that is easy to miss. A city with a full disc can justify
            paying the geotechnical and regulatory premium for dense, well-connected
            development, because the catchment is there to fill it. A city with two-thirds of a
            disc has a thinner case for the same investment, so it builds at the edge instead,
            which raises the traffic term, which raises the nitrogen term, which further
            restricts what can be consented. The border is upstream of the constraint that
            binds.
          </p>
          <p>
            That gives an unusual conclusion for a spatial analysis: Enschede's highest-return
            investment may not be spatial at all. Qualification recognition, cross-border social
            insurance, and a single fare regime cost a fraction of one kilometre of
            infrastructure and, on this geometry, move more accessible population than anything
            that could be built.
          </p>
        </Prose>
      </Section>

      <Section title="Where this model is weak">
        <Prose>
          <p>
            Three places, stated so they are not discovered as a rebuttal. The border is
            treated as a straight chord, which it is not. Population beyond it is treated as
            uniformly distributed at a single density, which flattens the fact that Gronau sits
            immediately across the line while the Münsterland thins out quickly behind it. And
            permeability is applied as a scalar when in reality it differs sharply by
            function — retail crosses far more easily than employment, which crosses more
            easily than healthcare.
          </p>
          <p>
            All three sharpen rather than reverse the conclusion. A real border geometry, a real
            population surface and a per-function permeability would give a more precise number
            for the same finding: the constraint is institutional, and it is not being counted.
          </p>
        </Prose>
      </Section>
    </div>
  );
}
