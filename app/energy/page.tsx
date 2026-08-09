import type { Metadata } from "next";
import { Figure, Prose, Stat } from "@/components/Figure";
import { PageHeader, Section } from "@/components/PageHeader";
import { LandPerTWh, LandPerTWhTable } from "@/components/charts/LandPerTWh";
import {
  TARGET,
  TECHNOLOGIES,
  exclusiveKm2ForTarget,
  grossKm2ForTarget,
  rooftopPotentialTWh,
  shareOfMunicipality,
  unitsForTarget,
} from "@/data/energy";

export const metadata: Metadata = { title: "Energy" };

const wind = TECHNOLOGIES.find((t) => t.id === "wind")!;
const solar = TECHNOLOGIES.find((t) => t.id === "solar-field")!;
const roof = TECHNOLOGIES.find((t) => t.id === "solar-roof")!;
const landRatio = exclusiveKm2ForTarget(solar) / exclusiveKm2ForTarget(wind);
const rooftop = rooftopPotentialTWh();

export default function Page() {
  return (
    <div>
      <PageHeader index="06 · Energy" title="Land per terawatt-hour">
        The regional renewable target is argued about almost entirely in the language of
        landscape and consent. Converted into the two quantities that actually constrain it —
        area associated, and area withdrawn from other use — it produces an uncomfortable
        result. The technology that consumes the least land is the one the constraint regime
        excludes, and the technology that survives the regime is the one that consumes the
        most.
      </PageHeader>

      <section className="mb-4 grid gap-x-10 gap-y-8 sm:grid-cols-2 lg:grid-cols-4">
        <Stat
          label="Regional target"
          value={TARGET.value.toFixed(1)}
          unit="TWh per year"
          note="Across the fourteen Twente municipalities, not Enschede alone."
        />
        <Stat
          label="Land withdrawn, wind"
          value={exclusiveKm2ForTarget(wind).toFixed(2)}
          unit="km²"
          note={`${Math.round(unitsForTarget(wind))} machines. The array spans ${grossKm2ForTarget(wind).toFixed(0)} km², nearly all of which stays in agricultural use.`}
        />
        <Stat
          label="Land withdrawn, ground-mounted solar"
          value={exclusiveKm2ForTarget(solar).toFixed(0)}
          unit="km²"
          note={`Every hectare of it, withdrawn. That is ${(shareOfMunicipality(exclusiveKm2ForTarget(solar)) * 100).toFixed(0)} per cent of Enschede's entire municipal land area, for scale rather than as a siting proposal.`}
          accent
        />
        <Stat
          label="Ratio between them"
          value={`${landRatio.toFixed(0)}×`}
          note="Per unit of energy delivered. The gap is not a detail of the comparison; it is the comparison."
        />
      </section>

      <Figure
        n="01"
        title="Associated land against land withdrawn"
        deck={`Square kilometres needed for the ${TARGET.value} TWh per year target, on a logarithmic axis. Each technology is a pair: the land it is associated with, and the land it takes out of other use. The distance between the two ends is the finding.`}
        klass="derived"
        sources={["resTwente", "physics"]}
        table={<LandPerTWhTable />}
        note="Rooftop solar sits at zero on both measures, which a logarithmic axis cannot draw, so it is stated here rather than nudged onto the scale — putting a zero at an arbitrary small value is how a chart starts to lie."
      >
        <LandPerTWh />
      </Figure>

      <Section title="Why the process selects the land-hungry option">
        <div className="mt-2">
          {TECHNOLOGIES.map((t) => (
            <article key={t.id} className="border-t border-rule py-5">
              <div className="flex flex-wrap items-baseline gap-x-3">
                <h3 className="text-[1.0625rem] font-medium tracking-tight text-ink">
                  {t.label}
                </h3>
                <span
                  className="rounded-full border px-2 py-0.5 text-[0.625rem] uppercase tracking-widest"
                  style={{
                    borderColor:
                      t.constraintShape === "field" ? "var(--series-1)" : "var(--rule)",
                    color:
                      t.constraintShape === "field" ? "var(--series-1)" : "var(--text-muted)",
                  }}
                >
                  {t.constraintShape === "none" ? "no spatial constraint" : t.constraintShape}
                </span>
              </div>
              <p className="mt-2 max-w-[68ch] text-[0.875rem] leading-relaxed text-ink-2">
                <span className="text-ink-3">What stops it: </span>
                {t.bindingConstraint}
              </p>
              <p className="mt-1.5 max-w-[68ch] text-[0.8125rem] leading-relaxed text-ink-3">
                {t.basis}
              </p>
            </article>
          ))}
        </div>
        <Prose>
          <p className="mt-8">
            The pattern is the one the rest of this platform keeps producing. Wind is stopped by
            fields — noise, shadow flicker, radar sightlines, habitat disturbance — none of
            which is a land requirement, and several of which are tractable engineering
            problems being handled as spatial ones. Radar interference in particular is a signal
            processing question that has been converted into a map.
          </p>
          <p>
            Ground-mounted solar is stopped by a polygon, and a polygon can be redrawn. So a
            search-area process that is genuinely trying to find consentable capacity will
            reliably converge on solar, not because it is the better answer but because its
            obstacle is the negotiable kind. The scarce resource, land, is being spent to avoid
            the reducible one.
          </p>
        </Prose>
      </Section>

      <Section title="The option with no land cost at all">
        <Prose>
          <p>
            Enschede's roofs are worth roughly {rooftop.toFixed(2)} TWh per year — about{" "}
            {((rooftop / TARGET.value) * 100).toFixed(0)} per cent of the whole regional target,
            from one municipality, on structure that already exists. The estimate is coarse and
            marked as such: it multiplies the dwelling stock by an assumed usable roof area and
            scales for the city's unusually large inherited industrial and institutional roof
            stock.
          </p>
          <p>
            What stops it is not land and not consent. It is transformer capacity at the
            low-voltage end of the network, roof structural capacity on older stock, and the
            split incentive between whoever owns a roof and whoever pays the electricity bill
            underneath it. Two of those three are capital problems and the third is a contract
            problem. None of them is a spatial problem, and none of them is what the regional
            search-area process is set up to solve.
          </p>
          <p>
            That is the same finding as the nitrogen page, arriving from the other direction.
            The instrument in use is spatial; the binding constraint is not. A process that can
            only draw polygons will keep producing polygon-shaped answers to problems that do
            not have them, and will keep spending the one resource that cannot be manufactured
            in order to avoid the ones that can.
          </p>
        </Prose>
        <dl className="mt-8 grid gap-x-10 gap-y-6 sm:grid-cols-3">
          <div className="border-t border-rule pt-3">
            <dt className="text-[0.6875rem] uppercase tracking-widest text-ink-3">
              Rooftop potential
            </dt>
            <dd className="mt-2 text-[1.375rem] font-semibold leading-none tabular-nums text-ink">
              {rooftop.toFixed(2)}
              <span className="ml-1.5 text-[0.75rem] font-normal text-ink-2">TWh/yr</span>
            </dd>
            <dd className="mt-2 text-[0.75rem] leading-relaxed text-ink-3">
              Enschede alone, residential stock scaled for non-residential roof area.
            </dd>
          </div>
          <div className="border-t border-rule pt-3">
            <dt className="text-[0.6875rem] uppercase tracking-widest text-ink-3">
              Share of the regional target
            </dt>
            <dd className="mt-2 text-[1.375rem] font-semibold leading-none tabular-nums text-ink">
              {((rooftop / TARGET.value) * 100).toFixed(0)}%
            </dd>
            <dd className="mt-2 text-[0.75rem] leading-relaxed text-ink-3">
              From one of fourteen municipalities, with no land taken.
            </dd>
          </div>
          <div className="border-t border-rule pt-3">
            <dt className="text-[0.6875rem] uppercase tracking-widest text-ink-3">
              Land required
            </dt>
            <dd className="mt-2 text-[1.375rem] font-semibold leading-none tabular-nums text-ink">
              0
              <span className="ml-1.5 text-[0.75rem] font-normal text-ink-2">km²</span>
            </dd>
            <dd className="mt-2 text-[0.75rem] leading-relaxed text-ink-3">
              {roof.bindingConstraint}
            </dd>
          </div>
        </dl>
      </Section>
    </div>
  );
}
