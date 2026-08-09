import type { Metadata } from "next";
import { Prose, Stat } from "@/components/Figure";
import { PageHeader, Section } from "@/components/PageHeader";
import { COMPARISON, CT, CT_STATION_SHARE } from "@/data/capetown";
import { CITY } from "@/data/city";

export const metadata: Metadata = { title: "Both cities" };

const ctPeoplePerKm2 = CT.population.value / CT.urbanEdgeArea.value;
const enPeoplePerKm2 = CITY.population.value / CITY.builtUpArea.value;

const SIDE_BY_SIDE: { label: string; ct: string; en: string; note: string }[] = [
  {
    label: "People",
    ct: "4.8 million",
    en: "161,000",
    note: "Cape Town is about thirty times bigger.",
  },
  {
    label: "Land you can build on",
    ct: `${CT.urbanEdgeArea.value} km²`,
    en: `${CITY.builtUpArea.value} km² built, ${CITY.landArea.value} km² total`,
    note: "Cape Town has twenty times the buildable land for thirty times the people.",
  },
  {
    label: "People per km² of that land",
    ct: ctPeoplePerKm2.toLocaleString("en-GB", { maximumFractionDigits: 0 }),
    en: enPeoplePerKm2.toLocaleString("en-GB", { maximumFractionDigits: 0 }),
    note: "Cape Town is already denser on the land it uses.",
  },
  {
    label: "Land protected for nature",
    ct: `${CT.protectedShare.value}% formally, roughly a third once biodiversity areas are added`,
    en: "A few per cent, but one bog sets a limit for the whole city",
    note: "Cape Town loses land to protection. Enschede loses permission.",
  },
  {
    label: "What blocks building",
    ct: "A line on a map, and land already spoken for",
    en: "Nitrogen in the air, and noise at the façade",
    note: "One is drawn, the other is measured.",
  },
  {
    label: "Land within a walk of a station",
    ct: `${(CT_STATION_SHARE * 100).toFixed(0)}% of land inside the edge`,
    en: "8% of built-up land, 82% of residents by bicycle",
    note: "Same arithmetic behind both: the walking radius, not the rail network.",
  },
];

export default function Page() {
  return (
    <div>
      <PageHeader index="Both cities" title="Cape Town and Enschede, side by side">
        These two cities are in one project because they are hard to build in for
        opposite reasons. Cape Town has run out of land. Enschede has plenty and still
        cannot build. Comparing them shows something neither shows alone: what kind of
        limit you are dealing with decides what you can do about it.
      </PageHeader>

      <section className="mb-16 grid gap-x-10 gap-y-8 sm:grid-cols-2 lg:grid-cols-4">
        <Stat
          label="Cape Town, people per built km²"
          value={ctPeoplePerKm2.toLocaleString("en-GB", { maximumFractionDigits: 0 })}
          note="On 895 km² inside the urban edge."
        />
        <Stat
          label="Enschede, people per built km²"
          value={enPeoplePerKm2.toLocaleString("en-GB", { maximumFractionDigits: 0 })}
          note="On about 43 km² of built-up land."
        />
        <Stat
          label="Cape Town's limit"
          value="A line"
          note="The urban edge and the protected areas. You can argue about where it goes; you cannot make it smaller."
        />
        <Stat
          label="Enschede's limit"
          value="A number"
          note="Nitrogen per hectare per year. You can bring it down, and bringing it down helps everywhere at once."
          accent
        />
      </section>

      <Section title="The same questions, both cities">
        <div className="mt-2">
          {COMPARISON.map((row, i) => (
            <article key={row.question} className="border-t border-rule py-7">
              <div className="flex items-baseline gap-3">
                <span className="text-[0.6875rem] tabular-nums tracking-widest text-ink-3">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <h3 className="text-[1.125rem] font-medium tracking-tight text-ink">
                  {row.question}
                </h3>
              </div>
              <div className="mt-4 grid gap-x-10 gap-y-5 md:grid-cols-2">
                <div className="border-l-2 pl-4" style={{ borderColor: "var(--series-2)" }}>
                  <div className="text-[0.6875rem] uppercase tracking-widest text-ink-3">
                    Cape Town
                  </div>
                  <p className="mt-1.5 text-[0.875rem] leading-relaxed text-ink-2">
                    {row.capeTown}
                  </p>
                </div>
                <div className="border-l-2 pl-4" style={{ borderColor: "var(--series-1)" }}>
                  <div className="text-[0.6875rem] uppercase tracking-widest text-ink-3">
                    Enschede
                  </div>
                  <p className="mt-1.5 text-[0.875rem] leading-relaxed text-ink-2">
                    {row.enschede}
                  </p>
                </div>
              </div>
              <p className="mt-4 max-w-[68ch] text-[0.9375rem] leading-relaxed text-ink">
                {row.soWhat}
              </p>
            </article>
          ))}
        </div>
      </Section>

      <Section title="The numbers next to each other">
        <div className="scroll-x">
          <table className="data-table">
            <thead>
              <tr>
                <th></th>
                <th style={{ textAlign: "left" }}>Cape Town</th>
                <th style={{ textAlign: "left" }}>Enschede</th>
                <th style={{ textAlign: "left" }}>What it means</th>
              </tr>
            </thead>
            <tbody>
              {SIDE_BY_SIDE.map((row) => (
                <tr key={row.label}>
                  <td style={{ whiteSpace: "normal", minWidth: "11rem" }}>{row.label}</td>
                  <td style={{ textAlign: "left", whiteSpace: "normal", minWidth: "13rem" }}>
                    {row.ct}
                  </td>
                  <td style={{ textAlign: "left", whiteSpace: "normal", minWidth: "13rem" }}>
                    {row.en}
                  </td>
                  <td style={{ textAlign: "left", whiteSpace: "normal", minWidth: "16rem" }}>
                    {row.note}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section title="What both cities have in common">
        <Prose>
          <p>
            Three things show up in both, and they are the parts worth taking somewhere
            else.
          </p>
          <p>
            <strong className="font-medium text-ink">
              The limit pushes building to the worst place.
            </strong>{" "}
            Cape Town&apos;s edge pushes housing onto sand that is expensive to build on and
            sits over the water supply. Enschede&apos;s land prices push housing to the edge
            of town, where people drive most — and driving is what produces the nitrogen that
            blocks the next permit. Neither was anyone&apos;s plan. Both follow from the
            limit.
          </p>
          <p>
            <strong className="font-medium text-ink">
              The tool draws maps, so the answer comes back as a map.
            </strong>{" "}
            Planning software holds shapes, so limits get stored as shapes, and the fix
            always looks like moving a line. But Cape Town&apos;s real problem is that the
            trains stopped running, and Enschede&apos;s is a chemical measurement. Neither is
            a shape, and neither is fixed by moving one.
          </p>
          <p>
            <strong className="font-medium text-ink">
              The cheapest fix is not construction.
            </strong>{" "}
            In Cape Town it is making the existing trains run and helping people reach the
            stations that already exist. In Enschede it is building near the stations with
            less parking, and opening the German border to commuting. In both cases the thing
            that would help most costs a fraction of what new infrastructure costs.
          </p>
        </Prose>
      </Section>

      <Section title="What is not equal here">
        <Prose>
          <p>
            The Enschede sections do their own arithmetic and show it. The Cape Town figures
            are taken from published city documents and one third-party calculation, and
            repeated as given. So this is a fair comparison of what the two cities look like,
            and not yet a fair comparison of two analyses. Redoing the Cape Town side from
            source data is the obvious next step.
          </p>
        </Prose>
      </Section>
    </div>
  );
}
