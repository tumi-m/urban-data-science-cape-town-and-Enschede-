import type { Metadata } from "next";
import { Figure, Prose, Stat } from "@/components/Figure";
import { PageHeader, Section } from "@/components/PageHeader";
import { CapeTownLand, CapeTownLandTable } from "@/components/charts/CapeTownLand";
import { CT, CT_LIMITS, CT_STATION_SHARE } from "@/data/capetown";

export const metadata: Metadata = { title: "Cape Town" };

const protectedKm2 = CT.protectedArea.value / 100;
const edgeShare = CT.urbanEdgeArea.value / CT.municipalArea.value;
const peoplePerKm2 = CT.population.value / CT.urbanEdgeArea.value;

export default function Page() {
  return (
    <div>
      <PageHeader index="Cape Town" title="Cape Town: running out of room">
        Cape Town has the opposite problem to Enschede. Enschede has land it cannot build
        on. Cape Town has almost no land left at all. Mountain on one side, ocean on two,
        and about a third of what remains is protected nature. What is left is a flat sandy
        plain that is both the worst ground to build on and the roof of the city&apos;s
        emergency water supply.
      </PageHeader>

      <section className="mb-4 grid gap-x-10 gap-y-8 sm:grid-cols-2 lg:grid-cols-4">
        <Stat
          label="Land you can build on"
          value={`${(edgeShare * 100).toFixed(0)}%`}
          note={`${CT.urbanEdgeArea.value} km² inside the urban edge, out of ${CT.municipalArea.value.toLocaleString("en-GB")} km² of city.`}
        />
        <Stat
          label="People per km² of that land"
          value={peoplePerKm2.toLocaleString("en-GB", { maximumFractionDigits: 0 })}
          note="Roughly five times Enschede's figure, on land that is much harder to build on."
          accent
        />
        <Stat
          label="Protected nature"
          value={`${CT.protectedShare.value}%`}
          note={`${CT.protectedArea.value.toLocaleString("en-GB")} hectares with formal protection, before biodiversity areas are counted on top.`}
        />
        <Stat
          label="Original plant life already gone"
          value={`${CT.vegetationLost.value}%`}
          note="Mostly on the flat lowlands, which is exactly where building is easiest."
        />
      </section>

      <Figure
        n="01"
        title="Where Cape Town's land goes"
        deck="The whole municipality, split three ways. The blue block is everything the city is allowed to build on."
        klass="derived"
        sources={["cctMsdf", "cctBionet"]}
        table={<CapeTownLandTable />}
        note={`The municipal total here is worked out from the city's own numbers rather than looked up: ${CT.protectedArea.value.toLocaleString("en-GB")} hectares is stated as ${CT.protectedShare.value}% of the city, which makes the whole ${CT.municipalArea.value.toLocaleString("en-GB")} km². That matches the published area, which is a useful sign the two figures agree.`}
      >
        <CapeTownLand />
      </Figure>

      <Section title="The four limits">
        <Prose>
          <p>
            Two of these are lines on a map and two are quantities. That split matters,
            because you can only argue about a line, whereas a quantity can be brought down.
          </p>
        </Prose>
        <div className="mt-8">
          {CT_LIMITS.map((limit, i) => (
            <article key={limit.id} className="border-t border-rule py-6">
              <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                <span className="text-[0.6875rem] tabular-nums tracking-widest text-ink-3">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <h3 className="text-[1.0625rem] font-medium tracking-tight text-ink">
                  {limit.label}
                </h3>
                <span
                  className="rounded-full border px-2 py-0.5 text-[0.625rem] uppercase tracking-widest"
                  style={{
                    borderColor:
                      limit.shape === "field" ? "var(--series-1)" : "var(--rule)",
                    color:
                      limit.shape === "field" ? "var(--series-1)" : "var(--text-muted)",
                  }}
                >
                  {limit.shape}
                </span>
              </div>
              <dl className="mt-4 grid gap-x-10 gap-y-5 md:grid-cols-3">
                <div>
                  <dt className="text-[0.6875rem] uppercase tracking-widest text-ink-3">
                    What it is
                  </dt>
                  <dd className="mt-1.5 text-[0.875rem] leading-relaxed text-ink-2">
                    {limit.what}
                  </dd>
                </div>
                <div>
                  <dt className="text-[0.6875rem] uppercase tracking-widest text-ink-3">
                    What it does
                  </dt>
                  <dd className="mt-1.5 text-[0.875rem] leading-relaxed text-ink-2">
                    {limit.effect}
                  </dd>
                </div>
                <div>
                  <dt className="text-[0.6875rem] uppercase tracking-widest text-ink-3">
                    Can it be brought down?
                  </dt>
                  <dd className="mt-1.5 text-[0.875rem] leading-relaxed text-ink-2">
                    {limit.canItBeLowered}
                  </dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      </Section>

      <Section title="The trap">
        <Prose>
          <p>
            Put the four together and you get a loop the city cannot easily get out of.
            The urban edge stops outward growth. Protected nature takes a third of the land.
            That leaves the Cape Flats — flat, available, and cheap to buy.
          </p>
          <p>
            But the Cape Flats is loose sand that can lose its strength in an earthquake
            between about {CT.liquefiableFrom.value} and {CT.liquefiableTo.value} metres
            down. That is exactly the depth range foundations for tall buildings sit in, so
            building upward there costs far more than it should. So the city builds outward
            and low instead, on the cheapest land at the edge — which is furthest from the
            jobs.
          </p>
          <p>
            And underneath that same sand is the aquifer: about{" "}
            {CT.aquiferYield.value} million cubic metres of water a year, which the city
            turned to when the dams nearly ran dry. The sand that makes the water reachable
            is the same sand that lets anything spilled on the surface reach it. Housing
            without working sewerage, built over the recharge area, puts the emergency water
            supply at risk.
          </p>
          <p className="text-ink">
            So: the limit pushes housing onto the one piece of land where building up is
            most expensive and where building at all threatens the water. Every part of that
            is a reasonable decision on its own. Together they trap the city.
          </p>
        </Prose>
      </Section>

      <Section title="Trains">
        <Prose>
          <p>
            About {(CT_STATION_SHARE * 100).toFixed(0)}% of the land inside the urban edge
            is within an 800 metre walk of a train station —{" "}
            {CT.stationBuffers.value} km² out of {CT.urbanEdgeArea.value} km². That figure
            is usually read as proof that the city needs decades of new rail.
          </p>
          <p>
            It is worth being careful with it. Cape Town has a big rail network already. The
            20% is mostly a statement about how far people are assumed to walk, not about how
            much track exists — the access section works through why. And in the years since
            the network was largely stripped by theft and vandalism, coverage has been beside
            the point: a station you can walk to is worth nothing if no train comes.
          </p>
        </Prose>
      </Section>

      <Section title="Where these numbers come from">
        <Prose>
          <p>
            The land, nature and geology figures are the City of Cape Town&apos;s own
            published numbers and research on the Cape Flats. The station figure is a
            third-party calculation, repeated here as given and not checked independently.
            Nothing on this page has been recomputed from source data — unlike the Enschede
            sections, where the arithmetic is done here and shown.
          </p>
        </Prose>
      </Section>
    </div>
  );
}
