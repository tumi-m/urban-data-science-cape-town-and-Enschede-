import type { Metadata } from "next";
import { Figure, Prose, Stat } from "@/components/Figure";
import { PageHeader, Section } from "@/components/PageHeader";
import { CriticalValues, CriticalValuesTable } from "@/components/charts/CriticalValues";
import {
  DwellingNitrogen,
  DwellingNitrogenTable,
} from "@/components/charts/DwellingNitrogen";
import {
  BACKGROUND_DEPOSITION,
  CHRONOLOGY,
  DWELLING,
  HABITATS,
  LEVERS,
  annualUseNOxKg,
  kgNOxToMolN,
  lifetimeNOxKg,
} from "@/data/nitrogen";

export const metadata: Metadata = { title: "Nitrogen" };

const bog = HABITATS[0];
const baseline = lifetimeNOxKg(1, false);
const constructionShare = DWELLING.constructionNOxKg.value / baseline;
const locationOnly = 1 - lifetimeNOxKg(0.5, false) / baseline;
const leverRatio = locationOnly / constructionShare;
const bestCase = lifetimeNOxKg(0.2, true);

export default function Page() {
  return (
    <div>
      <PageHeader index="02 · Nitrogen" title="Nitrogen: why the allowance is zero">
        Since a 2019 court ruling, a project that adds nitrogen to a nature area already over
        its limit gets no allowance at all. Not a small one — none. So what limits building in
        Enschede is not hectares of land, it is a chemical measurement. And most of that
        measurement comes from something nobody files under environmental policy: how much
        driving each new home causes.
      </PageHeader>

      <section className="mb-4 grid gap-x-10 gap-y-8 sm:grid-cols-2 lg:grid-cols-4">
        <Stat
          label="Raised-bog critical value"
          value={bog.kdw.toLocaleString("en-GB")}
          unit="mol N/ha/yr"
          note="The lowest in the national set, at a habitat on the municipality's own south-eastern edge."
        />
        <Stat
          label="Regional background load"
          value={BACKGROUND_DEPOSITION.value.toLocaleString("en-GB")}
          unit="mol N/ha/yr"
          note="Eastern Overijssel sits well above the national mean. The habitat is over its limit before any project is proposed."
          accent
        />
        <Stat
          label="Headroom for a new project"
          value="0.00"
          unit="mol N/ha/yr"
          note="There is no de minimis. What the model reports to two decimals is what functions as the limit."
        />
        <Stat
          label="Construction's share of a dwelling's lifetime NOx"
          value={`${(constructionShare * 100).toFixed(0)}%`}
          note="The remainder is the traffic the dwelling attracts over fifty years."
        />
      </section>

      <Figure
        n="01"
        title="Five of six habitats get more nitrogen than they can take"
        deck="Critical deposition values by habitat against the regional background. The bar is what the habitat tolerates; the vertical rule is what the region delivers. Raised bog, picked out, is under by a factor of four; only alluvial forest clears the rule."
        klass="official"
        sources={["aerius", "natura2000"]}
        table={<CriticalValuesTable />}
        note="Once a habitat is over its critical value, the legal question stops being how much a project adds and becomes whether it adds anything at all. That is a categorical test, and categorical tests do not respond to being slightly better."
      >
        <CriticalValues />
      </Figure>

      <Section title="How the rule came about">
        <ol className="mt-2">
          {CHRONOLOGY.map((c) => (
            <li key={c.date} className="grid gap-x-8 gap-y-2 border-t border-rule py-5 md:grid-cols-[8rem_1fr]">
              <span className="text-[0.8125rem] tabular-nums text-ink-3">{c.date}</span>
              <div>
                <p className="text-[0.9375rem] font-medium leading-snug text-ink">{c.event}</p>
                <p className="mt-1.5 max-w-[62ch] text-[0.875rem] leading-relaxed text-ink-2">
                  {c.consequence}
                </p>
              </div>
            </li>
          ))}
        </ol>
        <Prose>
          <p className="mt-8">
            The 2018 change matters more than it looks. A new Dutch dwelling has no combustion
            in use, so its heating contributes nothing. That leaves two terms in the account —
            the plant that builds it and the traffic it attracts — and it makes the second one
            almost the whole of the answer.
          </p>
        </Prose>
      </Section>

      <Figure
        n="02"
        title="Most of a home's nitrogen comes from driving, not building"
        deck="Nitrogen oxides per dwelling over a fifty-year life, split between construction plant and attracted traffic, under five combinations of location, parking provision and plant."
        klass="derived"
        sources={["cbs", "aerius"]}
        table={<DwellingNitrogenTable />}
        note={`Emission side only: no dispersion is modelled here and none should be read into it. Turning emissions into deposition at a named receptor is what the official calculator does, and an imitation of it would be worse than nothing. What survives any dispersion assumption is the ratio between the two segments, because both disperse from broadly the same place.`}
      >
        <DwellingNitrogen />
      </Figure>

      <Section title="The options, biggest effect first">
        <div className="mt-2">
          {LEVERS.map((l) => {
            const total = lifetimeNOxKg(l.carKmScale, l.electricPlant);
            const cut = 1 - total / baseline;
            return (
              <article key={l.id} className="grid gap-x-8 gap-y-3 border-t border-rule py-5 md:grid-cols-[1fr_9rem]">
                <div>
                  <h3 className="text-[0.9375rem] font-medium leading-snug text-ink">{l.label}</h3>
                  <p className="mt-1.5 max-w-[62ch] text-[0.875rem] leading-relaxed text-ink-2">
                    {l.detail}
                  </p>
                </div>
                <div className="md:text-right">
                  <div className="text-[1.375rem] font-semibold leading-none tabular-nums text-ink">
                    {total.toFixed(0)}
                    <span className="ml-1 text-[0.75rem] font-normal text-ink-2">kg NOx</span>
                  </div>
                  <div className="mt-1.5 text-[0.6875rem] text-ink-3">
                    {Math.round(kgNOxToMolN(total)).toLocaleString("en-GB")} mol N
                    {cut > 0 && ` · −${(cut * 100).toFixed(0)}%`}
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      </Section>

      <Section title="What this means">
        <Prose>
          <p>
            Electrifying the construction plant is the intervention with the clearest public
            profile and it removes {(constructionShare * 100).toFixed(0)} per cent of the
            lifetime total. Putting the same dwelling where its residents drive half as much
            removes {(locationOnly * 100).toFixed(0)} per cent — nearly{" "}
            {leverRatio.toFixed(0)} times as much — and the two together take a dwelling from{" "}
            {baseline.toFixed(0)} kg to {bestCase.toFixed(0)} kg — a reduction of{" "}
            {(100 * (1 - bestCase / baseline)).toFixed(0)} per cent, with no change to the
            building itself.
          </p>
          <p>
            The conclusion is not that nitrogen policy should be relaxed. It is that in
            Enschede the nitrogen decision and the parking decision are the same decision, and
            only one of them is currently made by people who think they are working on
            nitrogen. A parking norm is an emissions instrument. So is the choice between an
            edge site and a site on the regional cycle route.
          </p>
          <p>
            There is a second-order effect worth naming. Where a threshold has no lower bound,
            compliance cost is dominated by modelling and by legal exposure rather than by
            abatement, because the marginal kilogram avoided does not change the answer to a
            categorical question. That structure favours applicants large enough to carry a
            specialist and a litigation reserve. A rule written to protect a bog also, quietly,
            selects for developer size — and the housing that most needs to be built is
            precisely the housing whose promoters can least carry that overhead.
          </p>
        </Prose>
      </Section>

      <Section title="Assumptions used">
        <dl className="grid gap-x-10 gap-y-5 sm:grid-cols-2">
          <Assumption term="Car use per dwelling">
            {DWELLING.carKmPerYear.value.toLocaleString("en-GB")} vehicle-km per year.{" "}
            {DWELLING.carKmPerYear.basis}
          </Assumption>
          <Assumption term="Fleet emission factor">
            {DWELLING.fleetNOxPerKm.value} g NOx per vehicle-km. {DWELLING.fleetNOxPerKm.note}
          </Assumption>
          <Assumption term="Construction plant">
            {DWELLING.constructionNOxKg.value} kg NOx per dwelling, one-off.{" "}
            {DWELLING.constructionNOxKg.basis}
          </Assumption>
          <Assumption term="Annual use-phase total">
            {annualUseNOxKg().toFixed(1)} kg NOx per dwelling per year, over a{" "}
            {DWELLING.lifetimeYears}-year life.
          </Assumption>
        </dl>
      </Section>
    </div>
  );
}

function Assumption({ term, children }: { term: string; children: React.ReactNode }) {
  return (
    <div className="border-t border-rule pt-3">
      <dt className="text-[0.6875rem] uppercase tracking-widest text-ink-3">{term}</dt>
      <dd className="mt-1.5 text-[0.875rem] leading-relaxed text-ink-2">{children}</dd>
    </div>
  );
}
