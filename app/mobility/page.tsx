import type { Metadata } from "next";
import { Figure, Prose, Stat } from "@/components/Figure";
import { PageHeader, Section } from "@/components/PageHeader";
import { EnergyLadder, EnergyLadderTable } from "@/components/charts/EnergyLadder";
import { EnergyVersusSpace } from "@/components/charts/EnergyVersusSpace";
import { RidgeProfile } from "@/components/d3/RidgeProfile";
import {
  CLIMB,
  MODES,
  RIDGE_TRANSECT,
  UPSTREAM,
  climbBatteryWh,
  climbMetabolicWh,
  pkmPerKWh,
  totalAscent,
} from "@/data/mobility";

export const metadata: Metadata = { title: "Mobility" };

const byId = (id: string) => MODES.find((m) => m.id === id)!;
const ebike = byId("ebike");
const ice = byId("ice");
const bev = byId("bev");
const ratio = pkmPerKWh(ebike) / pkmPerKWh(ice);
const bevRatio = pkmPerKWh(ebike) / pkmPerKWh(bev);
const ascent = totalAscent(RIDGE_TRANSECT);

export default function Page() {
  return (
    <div>
      <PageHeader index="03 · Mobility" title="How much energy each way of travelling uses">
        Traffic is normally counted in vehicles per hour. That measures what is being managed,
        not what is being used up. Measure instead the energy each way of travelling spends
        moving one person one kilometre, and the options stop being a matter of taste: the
        best is about fifty times better than the worst. In a city where building permission
        depends on nitrogen from driving, that is the fastest thing to fix.
      </PageHeader>

      <section className="mb-4 grid gap-x-10 gap-y-8 sm:grid-cols-2 lg:grid-cols-4">
        <Stat
          label="Electric bicycle"
          value={pkmPerKWh(ebike).toFixed(0)}
          unit="p-km per kWh"
          note="At 11 Wh per kilometre from the battery, carrying one person."
          accent
        />
        <Stat
          label="Petrol car"
          value={pkmPerKWh(ice).toFixed(1)}
          unit="p-km per kWh"
          note="At 7 litres per 100 km and the Dutch average occupancy of 1.35."
        />
        <Stat
          label="Ratio between them"
          value={`${ratio.toFixed(0)}×`}
          note="Not a marginal improvement. A different order of magnitude, available today, at a fraction of the capital cost."
        />
        <Stat
          label="Electric bicycle against battery car"
          value={`${bevRatio.toFixed(0)}×`}
          note="Electrifying the car closes part of the gap. It does not close the part that comes from moving a tonne and a half to carry eighty kilograms."
        />
      </section>

      <Figure
        n="01"
        title="Energy used per person per kilometre"
        deck="Passenger-kilometres delivered per kilowatt-hour, on a logarithmic axis. Energy is counted where it enters the vehicle — fuel in the tank, electricity at the battery, food at the mouth — and occupancy is the observed average rather than the design capacity."
        klass="engineering"
        sources={["physics", "cbs"]}
        table={<EnergyLadderTable />}
        note="Every dot is labelled, which is normally a fault. Here the axis is logarithmic and a reader cannot recover a value from it, so the labels are carrying information the axis cannot."
      >
        <EnergyLadder />
      </Figure>

      <Section title="What this leaves out">
        <Prose>
          <p>
            Upstream chains are held apart from the ladder rather than folded into it. Folding
            them in is the commonest way to make an energy comparison unfalsifiable: once two
            multipliers are inside one number, a reader can no longer tell which of them moved.
            They are given here so they can be applied on purpose.
          </p>
        </Prose>
        <dl className="mt-8 grid gap-x-10 gap-y-6 sm:grid-cols-3">
          {UPSTREAM.map((u) => (
            <div key={u.id} className="border-t border-rule pt-3">
              <dt className="flex items-baseline justify-between text-[0.6875rem] uppercase tracking-widest text-ink-3">
                {u.label}
                <span className="tabular-nums text-ink">×{u.factor}</span>
              </dt>
              <dd className="mt-2 text-[0.8125rem] leading-relaxed text-ink-2">{u.note}</dd>
            </div>
          ))}
        </dl>
        <Prose>
          <p className="mt-8">
            Applying the food multiplier is the honest stress test of the whole argument, and
            it costs the unassisted bicycle its position: at a factor of six, cycling falls
            below the electric bicycle rather than sitting above it. That is not a defect in
            the comparison, it is the finding — the assisted bicycle wins on primary energy as
            well as at the vehicle, which is a stronger claim than the one usually made for it.
          </p>
          <p>
            Two caveats belong with that result rather than in a footnote. The multiplier
            assumes food intake rises in proportion to effort, which for most riders it does
            not, so six is an upper bound on a term whose true value is somewhere between one
            and six. And the assisted rider is still pedalling, so a like-for-like accounting
            would add part of a metabolic term back to the electric bicycle. Both corrections
            narrow the gap; neither reverses it.
          </p>
        </Prose>
      </Section>

      <Figure
        n="02"
        title="The modes that waste energy also waste space"
        deck="Energy per passenger-kilometre against plan area occupied per passenger at operating speed, both logarithmic. Private modes are picked out."
        klass="engineering"
        sources={["physics"]}
        note="The modes fall along a diagonal. In a city with a settlement boundary on one side, a nature network on another and a national border on a third, the mode that wastes energy is the same mode that wastes the land there is none of. These are not two constraints to be traded against one another; they are one constraint measured twice."
      >
        <EnergyVersusSpace />
      </Figure>

      <Section title="The ridge">
        <Prose>
          <p>
            Enschede sits on a Saalian ice-pushed ridge, which makes it one of the few Dutch
            cities where a bicycle trip contains real climb. A west-to-east traverse of the
            built-up area accumulates about {ascent} metres of ascent. In a country whose
            cycling policy is written for flat ground, this is the local variable that policy
            does not account for — and it is the specific thing electrical assistance removes.
          </p>
        </Prose>
        <Figure
          n="03"
          title="The hill across Enschede, west to east"
          deck="Elevation above datum along a coarse transect from the low ground west of the city, over the ridge through the centre, and down toward the Glanerbeek and the border. Hover to read a point."
          klass="official"
          sources={["ahn"]}
          note={`A thirty-metre climb costs a rider about ${climbMetabolicWh(CLIMB.typicalClimbM).toFixed(0)} watt-hours of food energy at ${(CLIMB.humanEfficiency * 100).toFixed(0)} per cent muscular efficiency — roughly a fifth of a five-kilometre trip's whole metabolic budget, and quite enough to arrive somewhere needing a change of shirt. The same climb costs a motor ${climbBatteryWh(CLIMB.typicalClimbM).toFixed(1)} watt-hours, which is under a kilometre of range. The gradient a person experiences as a reason to take the car is, to the motor, a rounding error.`}
        >
          <RidgeProfile />
        </Figure>
        <Prose>
          <p>
            This is why the assisted bicycle is a different proposition in Enschede than in the
            west of the country. Elsewhere in the Netherlands it buys speed and range on ground
            that was already ridable. Here it removes a barrier that exists — and it removes it
            for exactly the trips that currently default to a car, which are the trips carrying
            the dwelling nitrogen term on the previous page.
          </p>
          <p>
            The regional cycle route running the length of Twente is the corresponding piece of
            infrastructure, and its unit economics are the argument for it. It is built at a
            small fraction of the cost per kilometre of the road capacity it substitutes for,
            occupies a corridor narrow enough to thread through land that heavier infrastructure
            cannot enter, and imposes loads low enough that the constraint layers which stop a
            road do not stop it.
          </p>
        </Prose>
      </Section>
    </div>
  );
}
