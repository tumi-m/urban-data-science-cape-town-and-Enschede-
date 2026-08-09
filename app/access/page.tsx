import type { Metadata } from "next";
import { Figure, Prose, Stat } from "@/components/Figure";
import { PageHeader, Section } from "@/components/PageHeader";
import { AccessSheds } from "@/components/d3/AccessSheds";
import { CoverageCurve, CoverageCurveTable } from "@/components/charts/CoverageCurve";
import { CapeTownSheds, CapeTownShedsTable } from "@/components/charts/CapeTownSheds";
import {
  ACCESS_MODES,
  CAPE_TOWN,
  CITY_DISC,
  CURVE_RADII,
  STATIONS,
  coverage,
  effectiveRadiusKm,
  shedAreaKm2,
} from "@/data/access";

export const metadata: Metadata = { title: "Access" };

const walk = ACCESS_MODES[0];
const bike = ACCESS_MODES[1];
const ebike = ACCESS_MODES[2];

const walkShed = shedAreaKm2(walk.radiusKm);
const bikeShed = shedAreaKm2(bike.radiusKm);
const ebikeShed = shedAreaKm2(ebike.radiusKm);

const walkCov = coverage(effectiveRadiusKm(walk));
const bikeCov = coverage(effectiveRadiusKm(bike));

/** Where the two ways of counting diverge most, in percentage points. */
const peakGap = CURVE_RADII.map((radius) => ({ radius, ...coverage(radius) })).reduce(
  (best, c) => (c.population - c.land > best.population - best.land ? c : best),
);

/** The radius at which the three stations first cover the whole built-up area. */
const saturation = CURVE_RADII.find((r) => coverage(r).land >= 0.999);

export default function Page() {
  return (
    <div>
      <PageHeader index="04 · Access" title="How many people can reach a station">
        The usual measure is the share of an area within an 800 metre walk of a station. It is
        easy to work out, which is most of why it gets used, and it hides two assumptions.
        First, that 800 metres is a fact about the place rather than a choice about how people
        get there. Second, that land is the right thing to count. Both are wrong, and fixing
        them changes what the number tells you.
      </PageHeader>

      <section className="mb-4 grid gap-x-10 gap-y-8 sm:grid-cols-2 lg:grid-cols-4">
        <Stat
          label="Shed at the walking radius"
          value={walkShed.toFixed(1)}
          unit="km² per station"
          note={`π r² at ${walk.radiusKm * 1000} m, the conventional planning buffer.`}
        />
        <Stat
          label="Shed at the cycling radius"
          value={bikeShed.toFixed(1)}
          unit="km² per station"
          note={`The same ten minutes at cycling speed. ${(bikeShed / walkShed).toFixed(0)}× the area, because the shed goes as the square of the radius.`}
          accent
        />
        <Stat
          label="Shed at the assisted radius"
          value={ebikeShed.toFixed(0)}
          unit="km² per station"
          note={`${(ebikeShed / walkShed).toFixed(0)}× the walking shed, from twelve minutes of pedalling with a motor.`}
        />
        <Stat
          label="Enschede stations"
          value={String(STATIONS.length)}
          note="Which is derisory walking coverage, and turns out not to be the constraint it appears to be."
        />
      </section>

      <Section title="Why the radius matters so much">
        <Prose>
          <p>
            An access shed is a disc, and the area of a disc goes as the square of its radius.
            Tripling the reach does not triple the catchment, it multiplies it by nine. This
            is arithmetic rather than a finding, but it is arithmetic that a coverage
            percentage hides completely: the percentage is reported as though it described the
            rail network, when most of what it describes is the decision to measure at{" "}
            {walk.radiusKm * 1000} metres.
          </p>
          <p>
            The corollary is uncomfortable for the usual reading. A low coverage figure is
            evidence about the last mile at least as much as it is evidence about the track,
            and the last mile is orders of magnitude cheaper to change. A station whose
            catchment is set by walking has a fixed and small shed. The same station, with
            secure cycle parking and a direct route, has fourteen times the shed and needed no
            new rail to get it.
          </p>
        </Prose>
      </Section>

      <Figure
        n="01"
        title="How much of Enschede each station reaches"
        deck="Three stations, one adjustable access radius. The grey wash is the density gradient; the blue is the union of the sheds, composited once so overlaps do not read as darker. Adjust the radius, or take the network's indirectness out of it."
        klass="derived"
        sources={["ns", "cbs", "clark"]}
        note={`The built-up area is stylised as a disc of equal area — ${CITY_DISC.areaKm2} km², radius ${CITY_DISC.radiusKm.toFixed(2)} km — centred on the city centre. Enschede's real footprint reaches further south-west than north, so a true boundary would move the coverage fractions by a few points. It would not move the ratio between the walking and cycling cases, which is set by r² and not by the shape of the edge.`}
      >
        <AccessSheds />
      </Figure>

      <Section title="Why a circle on a map overstates it">
        <Prose>
          <p>
            A circle drawn around a station assumes streets run straight at it. They do not.
            The ratio of network distance to straight-line distance is typically between 1.2
            and 1.4, and because the shed goes as r², the real catchment is the circle divided
            by the square of that factor — somewhere between 51 and 69 per cent of what the
            buffer claims.
          </p>
          <p>
            The factor is not a constant of nature either. It is set by how permeable the
            street fabric is, which is a design decision. Superblock layouts, severance by
            motorways and rail reserves, and cul-de-sac estates all push it up; a fine-grained
            connected grid pushes it down. Enschede's pre-war fabric and its cycle network sit
            at the good end, which is why the cycling figures here lose little to circuity.
          </p>
        </Prose>
        <dl className="mt-8 grid gap-x-10 gap-y-6 sm:grid-cols-3">
          {ACCESS_MODES.map((m) => (
            <div key={m.id} className="border-t border-rule pt-3">
              <dt className="flex items-baseline justify-between text-[0.6875rem] uppercase tracking-widest text-ink-3">
                {m.label}
                <span className="tabular-nums text-ink">×{m.circuity.toFixed(2)}</span>
              </dt>
              <dd className="mt-2 text-[0.8125rem] leading-relaxed text-ink-2">
                {m.radiusKm.toFixed(1)} km nominal becomes {effectiveRadiusKm(m).toFixed(2)} km
                of real reach, so the shed is{" "}
                {((1 / (m.circuity * m.circuity)) * 100).toFixed(0)} per cent of the circle.
              </dd>
              <dd className="mt-1.5 text-[0.75rem] leading-relaxed text-ink-3">{m.note}</dd>
            </div>
          ))}
        </dl>
      </Section>

      <Figure
        n="02"
        title="Counting land instead of people"
        deck="Coverage against access radius, counted as a share of residents and as a share of built-up land. Vertical rules mark the three access modes."
        klass="derived"
        sources={["clark", "cbs", "ns"]}
        table={<CoverageCurveTable />}
        note={`The gap is the finding, and it behaves in two ways worth separating. In percentage points it is widest in the middle of the range — around ${(peakGap.radius).toFixed(1)} km, where the land metric reads ${(peakGap.land * 100).toFixed(0)} per cent against ${(peakGap.population * 100).toFixed(0)} per cent of residents. In proportional terms it is worst at the short end: at a real walk the land metric reports ${(walkCov.land * 100).toFixed(1)} per cent where ${(walkCov.population * 100).toFixed(1)} per cent of people are covered, understating access by a fifth. Either way it runs in the same direction, because the central station stands on the density peak while hectares out at the edge are nearly empty — and a station in an industrial estate books the same hectares as one on a dense corridor.`}
      >
        <CoverageCurve />
      </Figure>

      <Section title="What three stations actually reach">
        <Prose>
          <p>
            Measured the conventional way, Enschede's rail access is poor:{" "}
            {(walkCov.land * 100).toFixed(0)} per cent of built-up land within a real walk of
            a station. Measured in residents it is {(walkCov.population * 100).toFixed(0)} per
            cent — better, and still not a network anyone would call adequate.
          </p>
          <p>
            Shift the access mode to the bicycle and the same three stations reach{" "}
            {(bikeCov.population * 100).toFixed(0)} per cent of residents. Nothing was built.
            The trains did not change, the timetable did not change, and the stations stayed
            where they were. What changed was the assumed radius, and the radius was never a
            property of the rail network.
          </p>
          <p>
            Push the radius further and it saturates: by about {saturation?.toFixed(1)} km the
            three stations reach the whole built-up area, and the assisted radius adds no
            coverage at all. That is worth stating plainly, because it marks where this
            metric stops being informative. Past saturation the returns are in journey time
            and in reliability, not in reach — and a coverage percentage cannot see either.
          </p>
          <p>
            This is the specific reason the mobility page matters to this one. The bicycle
            only delivers that radius if the ridge is not in the way, and thirty metres of
            climb is precisely the thing that turns a three-kilometre feeder trip into a car
            trip. Assistance removes it for about nine watt-hours. The rail network's
            effective catchment in Enschede is, to a first approximation, a function of
            e-bike adoption.
          </p>
        </Prose>
        <div className="mt-8">
          {STATIONS.map((s) => (
            <article key={s.id} className="border-t border-rule py-4">
              <h3 className="text-[0.9375rem] font-medium text-ink">{s.label}</h3>
              <p className="mt-1.5 max-w-[68ch] text-[0.875rem] leading-relaxed text-ink-2">
                {s.note}
              </p>
            </article>
          ))}
        </div>
      </Section>

      <Section title="The same sum for Cape Town">
        <Prose>
          <p>
            The published figure for Cape Town is that {CAPE_TOWN.bufferKm2.value} km² of
            800 metre station buffers cover{" "}
            {(CAPE_TOWN.coverageShare() * 100).toFixed(0)} per cent of the{" "}
            {CAPE_TOWN.developmentEdgeKm2.value} km² inside its urban development edge, and
            the conclusion usually drawn is that decades of rail investment stand between the
            city and adequate coverage. The figures are restated here as given and have not
            been independently reproduced; the point being made survives a wide margin of
            error in either of them.
          </p>
          <p>
            Divide the buffer area by the area of one 800 metre disc and the network is worth
            about {CAPE_TOWN.stationEquivalents.toFixed(0)} non-overlapping station-equivalents.
            Give those same station-equivalents a cycling radius and their sheds sum to{" "}
            {CAPE_TOWN.summedShedKm2(bike.radiusKm).toLocaleString("en-GB", {
              maximumFractionDigits: 0,
            })}{" "}
            km² — {(CAPE_TOWN.summedShedKm2(bike.radiusKm) / CAPE_TOWN.developmentEdgeKm2.value).toFixed(1)}{" "}
            times the entire development edge.
          </p>
        </Prose>
      </Section>

      <Figure
        n="03"
        title="Cape Town's stations, if people cycled instead of walked"
        deck="Summed sheds for the published station set against the area of the development edge, logarithmic. Labels give the multiple of the edge."
        klass="derived"
        sources={["ctAccess"]}
        table={<CapeTownShedsTable />}
        note="Summed, not unioned, and the distinction is load-bearing: overlap means the real union is a good deal smaller than the sum, so the cycling and assisted bars overstate coverage. What the comparison establishes is narrower and still worth having — a network whose sheds sum to nearly three times the area to be covered is not short of stations. It is short of a way to reach them."
      >
        <CapeTownSheds />
      </Figure>

      <Section title="What this does not tell you">
        <Prose>
          <p>
            Three limits, stated so they are not discovered as a rebuttal. Summed sheds are
            not a union, so the metropolitan figures above are an upper bound and the true
            union at a cycling radius would need the real station geometry to compute. The
            density gradient is a modelled exponential rather than a measured surface, chosen
            because it is the standard form and solved so it integrates to the actual
            population — it will misplace people at the neighbourhood scale even where the
            aggregate is right. And a shed is not a service: coverage says nothing about
            whether trains run, and a network can have excellent geometric access and no
            usable service at all.
          </p>
          <p>
            That last one deserves more than a caveat, because it is where the Cape Town
            argument really turns. Metrorail ridership on the worst corridors fell by roughly
            an order of magnitude over the past decade through vandalism, cable theft and
            service withdrawal. Twenty per cent coverage is moot when the trains do not come.
            A reliability constraint was measured as a spatial one, and the instrument
            returned a spatial answer — which is the same failure this platform documents in
            nitrogen, in noise and in renewable siting. The tool draws polygons, so the
            problem arrives shaped like a polygon.
          </p>
        </Prose>
      </Section>
    </div>
  );
}
