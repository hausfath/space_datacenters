# Methodology

This document records the parameters, formulas, and citations behind the lifecycle
GHG comparison of a space-based versus ground-based AI datacenter. Every value
described here is implemented in `space_dc_lca.py`, which is the single source of
truth; the figures are produced by `make_figures.py`. References are listed at the
end.

This is a **screening-level** assessment. Each scenario intensity is built up from
explicit, individually sourced parameters rather than taken from a single bottom-up
inventory, so the assumptions are visible and adjustable and the dominant terms are
easy to identify. Absolute numbers should be read as accurate to roughly ±50%; the
*comparison* between options is more robust than any single value.

## Contents

1. [Functional unit and system boundary](#1-functional-unit-and-system-boundary)
2. [Scenarios](#2-scenarios)
3. [Launch emissions](#3-launch-emissions)
4. [Thermal management from radiative physics](#4-thermal-management-from-radiative-physics)
5. [Power and orbit choice](#5-power-and-orbit-choice)
6. [Station-keeping and data downlink](#6-station-keeping-and-data-downlink)
7. [Ground baselines](#7-ground-baselines)
8. [Shared IT hardware](#8-shared-it-hardware)
9. [Methane leakage (shared parameter)](#9-methane-leakage-shared-parameter)
10. [Non-greenhouse-gas co-benefits](#10-non-greenhouse-gas-co-benefits)
11. [Uncertainty: Monte Carlo](#11-uncertainty-monte-carlo)
12. [Reconciliation with prior estimates](#12-reconciliation-with-prior-estimates)
13. [Parameter table](#13-parameter-table)
14. [References](#14-references)

---

## 1. Functional unit and system boundary

The functional unit is a **1 GW IT load operated for 10 years at a 95% capacity
factor**, which delivers

```
1 GW × 8760 h/yr × 0.95 × 10 yr = 83.2 TWh
```

to the load. All results are grams of CO₂-equivalent per kWh delivered. The boundary
covers electricity generation (or, in orbit, the embodied emissions of solar arrays
and batteries plus the launch to put the system in orbit), the embodied emissions of
the IT hardware including mid-life refresh, thermal management, and — for the ground
cases — the facility cooling overhead. It excludes end-of-life beyond the reentry
discussion in the main text, and treats the data-transmission term as negligible
(Section 6).

**A 1 GW orbital facility is a constellation, not a single satellite.** Both detailed
proposals envisage many co-orbiting satellites flying in close formation, linked by
free-space optical interconnects: Google's Project Suncatcher uses an ~81-satellite,
~1 km-radius cluster as its scaling unit, and Starcloud describes a modular 5 GW system
with kilometre-scale arrays assembled from many such units. Because every quantity here
is expressed per watt of IT load and per kWh delivered, the result does not depend on
the exact satellite count — only on the per-watt bus, array, radiator, and battery
masses a modular constellation must build and launch.

## 2. Scenarios

| Scenario | Power source |
|---|---|
| Ground — 100% gas | Combined-cycle gas turbine (CCGT) |
| Ground — 90/10 hybrid | 90% solar + storage, 10% gas backup |
| Ground — solar overbuild + storage | Fully decarbonised, near-term |
| Ground — nuclear | Firm baseload, fully decarbonised, longer-term |
| Space — high / mid / low mass | Orbital solar, three system-mass tiers |

The two fully-decarbonised ground cases are treated as the **near-term** and
**longer-term ends of a single decarbonised-ground range**: solar overbuild plus
storage is buildable now; firm nuclear at scale is the longer-term option. The
orbital tiers are then compared against that range rather than against a single
"clean grid" number.

## 3. Launch emissions

The launch term is

```
effective launch factor (kg CO₂e/kg to LEO)
    = combustion CO₂ per kg × non-CO₂ forcing multiplier
      + leaked-propellant methane (CO₂e per kg)
```

- **Combustion CO₂**: 25 kg CO₂e per kg to LEO centrally (range 20–35), consistent
  with FAA environmental assessments for Starship-class vehicles and the launch
  inventory of Kukreja et al. (2025).
- **Non-CO₂ forcing multiplier**: 1.5 centrally, varied 1.2–3.0. Rocket exhaust
  injects black carbon, water vapour, and nitrogen oxides directly into the
  stratosphere, where black carbon has a radiative-forcing efficiency roughly 500×
  that of surface soot because it is not rained out (Ryan et al. 2022). The soot
  emission index of methane–oxygen engines has never been directly measured;
  modelling studies have had to assume it is about a quarter of the kerosene value
  (Tsigaridis et al. 2024; Maloney et al. 2022). This multiplier is the single
  largest source of uncertainty in the orbital estimate, and the 3.0 upper bound
  reflects the possibility that methalox soot is closer to the kerosene value.
- **Propellant methane leakage**: producing the methane burned by a methalox vehicle
  leaks methane upstream, exactly as producing pipeline gas does. At ~9.6 kg of
  methane burned per kg of payload (about 1,200 t CH₄ per Starship launch over a
  ~125 t payload), the central 2.3% leakage rate and a 100-year GWP add about
  6.6 kg CO₂e per kg of payload — roughly a quarter of the combustion term.

Mass is converted to an intensity by multiplying total launched mass (system mass +
mid-life refresh mass) by the effective launch factor and amortising over 83.2 TWh.

## 4. Thermal management from radiative physics

In vacuum, waste heat can leave the spacecraft only by radiation. A flat panel of
emissivity ε at temperature *T*ᵣ radiating to an effective sink at *T*ₛ from both
faces rejects

```
P/A = n_sides · ε · σ · (Tᵣ⁴ − Tₛ⁴)
```

with σ = 5.67×10⁻⁸ W m⁻² K⁻⁴. Taking ε = 0.9 and *T*ₛ = 250 K (El-Genk & Schriener
2025), the flux is about 370 W m⁻² per face at 320 K and about 1,100 W m⁻² at 350 K.
For an areal density ρ (kg m⁻²), the specific mass is ρ / (n_sides · P/A), applied to
the waste heat, which is 75% of the IT load (≈25% GPU efficiency).

**The point that decides the orbital result — and the most common error in
orbital-datacenter proposals — is that the very light radiators quoted in the
literature operate at 500–1000 K**, a regime appropriate to nuclear-electric
propulsion, not to GPUs. Because flux scales as *T*⁴, dropping from 700 K to a
GPU-compatible 350 K cuts the flux per unit area roughly sixteen-fold and inflates
specific mass proportionally. The radiator mass here is therefore derived at the
relevant temperature rather than imported from high-temperature designs.

The bare panel is not the whole subsystem. Cold plates, pumped fluid loops, pumps,
headers, and micrometeoroid armour add mass: the International Space Station's
external thermal-control system has component masses summing to roughly 1.3–1.5× its
radiator panels alone (NASA ISS ATCS), and El-Genk & Schriener (2025) report a further
30–50% for debris armour. A **1.4× system overhead** is applied to the panel-derived
mass. The three tiers, all passive and operating at or below the ~375 K GPU junction
(so none requires a heat pump), come out at about **1.9, 3.7, and 12.5 kg per kW of
IT load** after overhead.

A radiator could be made lighter by running it hotter and using a heat pump to lift
waste heat above the chip temperature, but this is not free: the ideal work to move
heat *Q* from *T*ᵪ to *T*ₕ is *Q*(*T*ₕ−*T*ᵪ)/*T*ᵪ, so at half the Carnot limit
lifting 750 MW from 330 K to 500 K demands of order 77% of the IT load in additional
electrical power — which must itself be generated, stored, and launched. Exotic
liquid-droplet radiators (Mattick & Hertzberg 1982; Taussig & Mattick 1986; Alotaibi
et al. 2026) could also be lighter but sit at low technology readiness. Both are
excluded from the modelled tiers and treated only as an optimistic bound.

## 5. Power and orbit choice

The baseline is a **dawn–dusk sun-synchronous orbit (SSO)**, which keeps the
spacecraft in sunlight for all but brief solstice eclipses and so needs only a small
ride-through battery (0.5 GWh usable, ~30 min). This is the orbit selected by both
Starcloud (2024) and Google's Project Suncatcher (2025), and the near-continuous
illumination does real work in the favourable comparison.

A **generic LEO** is included as a sensitivity: eclipsed for roughly 35 minutes of
each 90-minute orbit, it pays two penalties — a battery sized to ride through every
eclipse, and a PV array oversized by about 1 + *t*eclipse/*t*sunlit ≈ 1.6 so it can
serve the load and recharge during the sunlit fraction. In generic LEO the orbital
intensity rises to 42 / 57 / 90 g CO₂e/kWh across the three mass tiers.

Battery embodied emissions use 60 kg CO₂/kWh of capacity for the space pack and 55
kg CO₂/kWh for ground storage, near the lithium-iron-phosphate distribution of
Peiseler et al. (2024). Space solar arrays use 500 kg CO₂/kWp (Frischknecht et al.
2020), scaled by a parasitic factor for avionics and attitude control.

## 6. Station-keeping and data downlink

**Station-keeping.** A large, low-areal-density array in low orbit must offset
aerodynamic drag, *F* = ½ ρ *C*_d *A* *v*². Using NRLMSISE-00 densities (Picone et al.
2002) at 600–800 km, *C*_d = 2.2, *v* ≈ 7.6 km/s, and electric propulsion at *I*_sp ≈
2000 s, the make-up propellant is of order 0.8 g per m² of ram area per year at solar
minimum, up to ~20 g m⁻² yr⁻¹ at solar maximum. For a GW-class platform this is only
~0.02–0.4 kg per kW of IT load over ten years; a 1 kg/kW allowance (range 0.3–3) is
carried to include thruster and tankage dry mass — under a few percent of system
mass.

**Data downlink.** State-of-the-art space optical terminals have demonstrated
200-Gbps downlinks (NASA TBIRD; Schieler et al. 2023). Scaling from such terminals,
link power is of order 0.5 W per Gbps, so even a continuous terabit-per-second
downlink draws ~0.5 kW — under 10⁻⁴% of a 1 GW IT load. Terrestrial network energy is
likewise a few percent of datacenter electricity and declining (Aslan et al. 2018).
For a batch AI-training workload the transmission term is therefore negligible and is
excluded.

## 7. Ground baselines

- **Gas (CCGT)**: 486 g CO₂e/kWh generated, including upstream methane (NREL 2021),
  multiplied by the facility PUE. The gas intensity is decomposed into a
  combustion-and-plant floor plus a leakage term that scales with the methane-leakage
  rate, calibrated so the central 2.3% rate reproduces 486.
- **Solar overbuild + storage (near-term decarbonised)**: a modern utility PV
  intensity of 40 g CO₂e/kWh *generated* (NREL 2021; Hsu et al. 2012), scaled by a
  1.5 generation-to-delivered ratio for the overbuild and curtailment needed to serve
  a flat round-the-clock load (Frazier et al. 2021; Davis et al. 2018), plus a storage
  term using LFP batteries at 55 kg CO₂/kWh. This gives ~70 g/kWh of generation-and-
  storage intensity, ~91 g/kWh delivered after PUE and shared IT.
- **Nuclear (longer-term decarbonised)**: 12 g CO₂e/kWh, the harmonised median of
  Warner & Heath (2012), multiplied by PUE. Nuclear matches a constant load directly
  and needs no overbuild or storage, giving ~22 g/kWh delivered.
- **90/10 hybrid**: 10% gas backup plus 90% solar-plus-storage; ~130 g/kWh delivered.

A **facility PUE of 1.2** (range 1.1–1.5; Uptime Institute 2024) is applied to every
ground generation term to capture cooling and electrical overhead. The orbital cases
carry a smaller **1.1 parasitic factor** for avionics, attitude control, and pumped
loops — orbit rejects heat passively and needs no chillers — so the cooling overhead
is genuinely asymmetric and that asymmetry favours space.

## 8. Shared IT hardware

The embodied carbon of the servers and GPUs is carried **identically on the ground
and in orbit**. Both refresh GPUs on the same 3–5-year obsolescence cadence (one
mid-life refresh centrally), so the IT term — about 7 g/kWh delivered at base plus one
refresh, anchored to the NVIDIA HGX H100 product carbon footprint of 1,312 kg CO₂e per
8-GPU baseboard (NVIDIA 2025) — **cancels in the comparison**. It is included so the
absolute intensities are complete, not because it shifts the space-versus-ground
result. (In orbit, the *launch* of the refresh hardware does not cancel and is counted
separately.)

## 9. Methane leakage (shared parameter)

Both the gas-fired ground datacenter and the methalox-launched orbital one carry an
upstream methane penalty, and a single leakage-rate parameter moves them on a common
basis — 2.3% centrally (Alvarez et al. 2018), varied 1.0–3.5%, at a 100-year GWP of
29.8 for fossil methane (IPCC AR6 2021). A **100-year GWP is used throughout; no
20-year horizon is reported.**

The gas plant burns methane for a decade, so its intensity moves by tens of grams per
kWh as the leakage rate varies; the rocket burns it once, so the orbital intensity
moves by only a few. A leaky gas supply therefore worsens the terrestrial option much
faster than the orbital one, widening the orbital advantage over gas.

## 10. Non-greenhouse-gas co-benefits

Serving a flat 1 GW load from a mostly-solar terrestrial system needs substantial
nameplate capacity. At a 25% AC capacity factor and a 1.5 generation-to-delivered
ratio, a 90%-solar datacenter needs roughly five to six gigawatts of panels. At the
utility-scale land-use intensity of Ong et al. (2013) — about 7.6 acres per MW_AC of
total area for fixed-tilt PV — this occupies on the order of **160 km², more than 2.5×
the area of Manhattan**. The same facility, evaporatively cooled at 0.5 L/kWh, would
consume about **4 Mt of water a year** (Siddik et al. 2021). An orbital datacenter
requires neither land nor cooling water. As land-use conflict and water scarcity
become binding constraints on terrestrial datacenter siting (IEA 2025), these
advantages are more robust than the GHG comparison itself and do not depend on any of
the contested launch or thermal assumptions.

## 11. Uncertainty: Monte Carlo

All ranges are 5th–95th percentiles from a Monte Carlo of 40,000 draws in which every
parameter in the table below is sampled jointly from a triangular distribution over
its (low, central, high) values. **System mass and radiator specific mass are drawn
independently**, so the favourable low-mass case is not implicitly paired with the
lightest radiator. Sampling all parameters gives a composite orbital intensity with
median 59 and 5th–95th range 44–84 g CO₂e/kWh; the decarbonised-ground options give
81–124 (solar plus storage) and 16–30 (nuclear), and gas 548–707.

Because the non-CO₂ launch multiplier (1.2–1.5–3.0) and several embodied terms are
right-skewed, the propagated medians sit slightly above the central-parameter point
estimates (for example the mid-mass orbital median is ~49 against a 41 central value).
Each figure reports the central estimate as the point value and the Monte Carlo
interval as the range.

## 12. Reconciliation with prior estimates

The orbital estimate here (central range 31–63) sits **broadly in line with Ohs and
well below Aili** once both are placed on this functional unit.

**Ohs et al. (2025)**, "Dirty Bits in Low-Earth Orbit" — 52 (Starship) to 66
(Falcon-9) g/kWh for a ~30 W eclipsed CubeSat with a ~4 kWh battery over 5 years,
counting combustion CO₂ only. This is already close to the basis used here. The
residual gap is one of inputs, not physics: starting from the mid-mass case (41 g/kWh;
dawn–dusk orbit, 10-year life, central launch), stripping the non-CO₂ and methane terms
to a combustion-only launch lowers it to ~28; switching to a heavily eclipsed generic
LEO with its larger battery and oversized array raises it to ~41; and amortising over a
5-year rather than 10-year life (doubling all one-time terms) brings it to ~81, into the
upper part of the Ohs range.

**Aili et al. (2025)**, *Nature Electronics* — report a life-cycle *carbon usage
effectiveness* (CUE: total emissions per unit of IT energy), headlined at ~0.72
kgCO₂e/kWh at a 4-year server life. Reproducing it from their Supplementary Table 11,
~65% (about 465 g/kWh) is a corporate scope-3 *recurrent* term (business travel,
purchased goods and services) that lies outside this study's physical boundary and is
common to their ground baseline — which is why their orbital case "approaches" an
all-renewable terrestrial data centre. Their Supplementary Table 10 nonetheless gives a
full per-satellite component inventory (each computational satellite carries 3 Dell R740
servers drawing 8,112 kWh/yr of IT energy), which `aili_harmonised()` re-expresses on
this functional unit. The result is ~**250 gCO₂e/kWh** — the *highest* of the three
orbital estimates, not the lowest — decomposed as:

| Component (Aili's inputs, 4-yr life) | gCO₂e/kWh |
|---|---:|
| IT hardware — Dell R740 server manufacturing (970 kg/server) | ~90 |
| Power + structure — Starlink-v1.0 bus + arrays (2,940 kg/sat) | ~90 |
| Thermal — aluminium active cooler (490 kg/server) | ~45 |
| Launch (Falcon-9 share, 790 kg/sat) | ~24 |
| **Physical total** | **~250** |

The launch term (~24) agrees closely with the value here; the excess is almost entirely
hardware. Aili cost a constellation of existing Starlink-class satellites each carrying
a few general-purpose servers — ~13× the embodied carbon per watt of a modern AI
accelerator, a 260 kg bus carrying only ~1 kW of compute, and thick aluminium radiators
in place of thin deployable panels. The purpose-built, compute-dense platforms actually
proposed (Starcloud, Project Suncatcher) are far closer to the inputs used here, so the
present estimate is the more representative of a real GW-scale orbital datacentre.
Amortising Aili's own inventory over 10 rather than 4 years would itself roughly halve
their figure to ~100 g/kWh.

**Cross-check of the ground baseline.** The solar-plus-storage baseline can be checked
against the open-source datacenter calculator at `offgridai.us`, which models a
20-year life, a four-hour battery, single-axis-tracking solar, and gas at 500 g/kWh,
and quotes ~70 g/kWh for a mostly-solar configuration — matching the 70 g/kWh
generation-and-storage intensity adopted here (before facility overhead and shared IT,
which raise the delivered figure to ~91). The gas figure (486 g/kWh including upstream
methane) likewise sits within a few percent of that calculator's 500 g/kWh.

## 13. Parameter table

Type: **L** literature/official dataset, **D** derived from other parameters,
**A** modelling assumption.

| Parameter | Low | Central | High | Type | Source |
|---|---:|---:|---:|:--:|---|
| *Functional unit* | | | | | |
| IT load (GW) | — | 1.0 | — | A | Hyperscale AI cluster scale |
| Operating life (yr) | — | 10 | — | A | Comparison window |
| Capacity factor | — | 0.95 | — | A | Availability / SSO illumination |
| Energy delivered (TWh) | — | 83.2 | — | D | 1 GW × 8760 × 0.95 × 10 |
| *Launch* | | | | | |
| Combustion CO₂ (kg/kg LEO) | 20 | 25 | 35 | L | FAA EA; Kukreja et al. (2025) |
| Non-CO₂ multiplier (×) | 1.2 | 1.5 | 3.0 | A | Ryan et al. (2022); Maloney et al. (2022); Tsigaridis et al. (2024) |
| Propellant CH₄ (kg/kg payload) | — | 9.6 | — | D | ~1200 t CH₄ / 125 t payload |
| Effective factor (kg CO₂e/kg) | 27 | 44 | 115 | D | combustion × mult + leakage |
| *Methane leakage (shared)* | | | | | |
| Leakage rate (%) | 1.0 | 2.3 | 3.5 | L | Alvarez et al. (2018) |
| GWP100 (CH₄, fossil) | — | 29.8 | — | L | IPCC AR6 (2021) |
| *Photovoltaics (space)* | | | | | |
| Si array (kg CO₂/kWp) | 400 | 500 | 700 | L | Frischknecht et al. (2020) |
| III–V array (kg CO₂/kWp) | — | 1500 | — | A | Stress test |
| *Thermal management* | | | | | |
| Waste-heat fraction | — | 0.75 | — | A | ~25% GPU efficiency |
| Panel areal density (kg/m²) | 5.2 | 8.0 | 12.8 | L | El-Genk & Schriener (2025) |
| Radiator *T*ᵣ (K) | 300 | 320–350 | 350 | A | ≤ GPU junction (passive) |
| System overhead (× panel) | 1.3 | 1.4 | 1.6 | L | NASA ISS ATCS; El-Genk & Schriener (2025) |
| Radiator (kg/kW_IT, w/ overhead) | 1.9 | 3.7 | 12.5 | D | Stefan–Boltzmann (Section 4) |
| *Battery (space, dawn–dusk SSO)* | | | | | |
| Usable capacity (GWh) | — | 0.5 | — | A | ~30 min ride-through |
| Depth of discharge | 0.30 | 0.40 | 0.50 | A | Few-thousand solstice cycles |
| Specific energy (Wh/kg) | 150 | 200 | 250 | L | Forward-looking space pack |
| Embodied (kg CO₂/kWh) | 50 | 60 | 100 | L | Peiseler et al. (2024) |
| *System mass, station-keeping, refresh* | | | | | |
| Bus+PV+structure (kg/kW) | 15 | 30 | 60 | A | Starcloud (2024); + server/redundancy |
| Station-keeping (kg/kW) | 0.3 | 1.0 | 3.0 | D | Drag make-up (Picone et al. 2002) |
| GPU refresh count | 0 | 1 | 2 | A | 3–5 yr obsolescence |
| Refresh compute (kg/kW) | — | 5.0 | — | A | Boards + servers, bus reused |
| Space parasitic (× IT) | 1.05 | 1.10 | 1.20 | A | Avionics/ADCS/pumps (no chiller) |
| *Ground* | | | | | |
| Gas CCGT (g CO₂e/kWh) | — | 486 | — | L | NREL (2021) |
| Nuclear (g CO₂e/kWh) | 5 | 12 | 20 | L | Warner & Heath (2012) |
| PV base (g/kWh generated) | 30 | 40 | 50 | L | NREL (2021); Hsu et al. (2012) |
| Generation/delivered | 1.3 | 1.5 | 2.0 | A | Frazier et al. (2021); Davis et al. (2018) |
| Ground battery (kg CO₂/kWh) | 40 | 55 | 75 | L | Peiseler et al. (2024) |
| Facility PUE (×) | 1.1 | 1.2 | 1.5 | L | Uptime Institute (2024) |
| Cooling water (L/kWh) | 0.2 | 0.5 | 1.8 | L | Siddik et al. (2021) |
| *Shared IT hardware* | | | | | |
| Embodied (Mt CO₂/GW, per build) | 0.2 | 0.3 | 0.4 | L | NVIDIA (2025) |

## 14. References

- Aili, A., Choi, J., Ong, Y. S., & Wen, Y. (2025). The development of carbon-neutral data centres in space. *Nature Electronics*, 8(11), 1016–1026. https://doi.org/10.1038/s41928-025-01476-1
- Alotaibi, R., Martín García, P., & Romero-Calvo, Á. (2026). Magnetic droplet radiator for CubeSat heat rejection. *Journal of Spacecraft and Rockets*. https://doi.org/10.2514/1.A36624
- Alvarez, R. A., Zavala-Araiza, D., Lyon, D. R., et al. (2018). Assessment of methane emissions from the U.S. oil and gas supply chain. *Science*, 361(6398), 186–188. https://doi.org/10.1126/science.aar7204
- Aslan, J., Mayers, K., Koomey, J. G., & France, C. (2018). Electricity intensity of internet data transmission: untangling the estimates. *Journal of Industrial Ecology*, 22(4), 785–798. https://doi.org/10.1111/jiec.12630
- Davis, S. J., Lewis, N. S., Shaner, M., et al. (2018). Net-zero emissions energy systems. *Science*, 360(6396), eaas9793. https://doi.org/10.1126/science.aas9793
- El-Genk, M. S., & Schriener, T. M. (2025). *Advanced lightweight heat rejection radiators for space nuclear power systems*. Institute for Space and Nuclear Power Studies, University of New Mexico (NASA Early-Stage Innovations Grant 80NSSC22K0263, Final Report).
- Federal Aviation Administration (2022). *Final programmatic environmental assessment for the SpaceX Starship/Super Heavy launch vehicle program at the Boca Chica launch site.*
- Frazier, A. W., Cole, W., Denholm, P., et al. (2021). *Storage Futures Study: economic potential of diurnal storage in the U.S. power sector*. NREL/TP-6A20-77449.
- Frischknecht, R., Stolz, P., Heath, G., et al. (2020). *Methodology guidelines on life cycle assessment of photovoltaic, 2020*. IEA PVPS Task 12, T12-18:2020.
- Hsu, D. D., O'Donoughue, P., Fthenakis, V., et al. (2012). Life cycle greenhouse gas emissions of crystalline silicon photovoltaic electricity generation. *Journal of Industrial Ecology*, 16, S122–S135. https://doi.org/10.1111/j.1530-9290.2011.00439.x
- International Energy Agency (2025). *Energy and AI*. World Energy Outlook Special Report. https://www.iea.org/reports/energy-and-ai
- IPCC (2021). *Climate Change 2021: The Physical Science Basis.* Contribution of Working Group I to the Sixth Assessment Report. Cambridge University Press. (GWP100 fossil CH₄ = 29.8, Table 7.15.)
- Kukreja, R., Oughton, E. J., & Linares, R. (2025). Greenhouse gas (GHG) emissions poised to rocket: modeling the environmental impact of LEO satellite constellations. arXiv:2504.15291.
- Maloney, C. M., Portmann, R. W., Ross, M. N., & Rosenlof, K. H. (2022). The climate and ozone impacts of black carbon emissions from global rocket launches. *Journal of Geophysical Research: Atmospheres*, 127(12), e2021JD036373. https://doi.org/10.1029/2021JD036373
- Mattick, A. T., & Hertzberg, A. (1982). The liquid droplet radiator — an ultralightweight heat rejection system for efficient energy conversion in space. *Acta Astronautica*, 9(3), 165–172.
- NASA. *International Space Station: Active Thermal Control System (ATCS) overview.* (Doc. 473486.) https://www.nasa.gov/pdf/473486main_iss_atcs_overview.pdf
- National Renewable Energy Laboratory (2021). *Life cycle greenhouse gas emissions from electricity generation: update*. NREL/FS-6A50-80580.
- NVIDIA Corporation (2025). *HGX H100 product carbon footprint.* (Cradle-to-gate: 1,312 kg CO₂e per 8-GPU baseboard.)
- Ohs, R., Stock, G. F., Schmidt, A., Fraire, J. A., & Hermanns, H. (2025). Dirty bits in low-Earth orbit: the carbon footprint of launching computers. *ACM SIGEnergy Energy Informatics Review*, 5(2), 26–33. https://doi.org/10.1145/3757892.3757896
- Ong, S., Campbell, C., Denholm, P., Margolis, R., & Heath, G. (2013). *Land-use requirements for solar power plants in the United States*. NREL/TP-6A20-56290.
- Peiseler, L., Schenker, V., Schatzmann, K., et al. (2024). Carbon footprint distributions of lithium-ion batteries and their materials. *Nature Communications*, 15, 10301. https://doi.org/10.1038/s41467-024-54634-y
- Picone, J. M., Hedin, A. E., Drob, D. P., & Aikin, A. C. (2002). NRLMSISE-00 empirical model of the atmosphere. *Journal of Geophysical Research: Space Physics*, 107(A12), 1468. https://doi.org/10.1029/2002JA009430
- Ryan, R. G., Marais, E. A., Balhatchet, C. J., & Eastham, S. D. (2022). Impact of rocket launch and space debris air pollutant emissions on stratospheric ozone and global climate. *Earth's Future*, 10(6), e2021EF002612. https://doi.org/10.1029/2021EF002612
- Schieler, C. M., Riesing, K. M., Bilyeu, B. C., et al. (2023). On-orbit demonstration of 200-Gbps laser communication downlink from the TBIRD CubeSat. *Free-Space Laser Communications XXXV*, Proc. SPIE 12413. https://doi.org/10.1117/12.2651297
- Siddik, M. A. B., Shehabi, A., & Marston, L. (2021). The environmental footprint of data centers in the United States. *Environmental Research Letters*, 16(6), 064017. https://doi.org/10.1088/1748-9326/abfba1
- Starcloud / Lumen Orbit (2024). *Why we should train AI in space.* White Paper v1.03. https://starcloudinc.github.io/wp.pdf
- Agüera y Arcas, B., Beals, T., Biggs, M., et al. (2025). Towards a future space-based, highly scalable AI infrastructure system design (Project Suncatcher). arXiv:2511.19468.
- Taussig, R. T., & Mattick, A. T. (1986). Droplet radiator systems for spacecraft thermal control. *Journal of Spacecraft and Rockets*, 23(1), 10–17. https://doi.org/10.2514/3.25077
- Tsigaridis, K., Field, R., Bauer, S. E., et al. (2024). Composition and climate impacts of increasing launches to low Earth orbit. *AIAA SciTech 2024 Forum*. https://doi.org/10.2514/6.2024-2168
- Uptime Institute (2024). *2024 Global Data Center Survey.*
- Warner, E. S., & Heath, G. A. (2012). Life cycle greenhouse gas emissions of nuclear electricity generation. *Journal of Industrial Ecology*, 16, S73–S92. https://doi.org/10.1111/j.1530-9290.2012.00472.x
