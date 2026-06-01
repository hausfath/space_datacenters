"""
space_dc_lca.py - Lifecycle GHG model for a space-based vs. ground-based AI datacenter.

Single source of truth for every number in the analysis. All scenario intensities
(g CO2e per kWh delivered) are derived here from explicit parameters so they can be
varied in one place. See METHODOLOGY.md for citations and justification of each value.

Functional unit: 1 GW IT load, 10-year operating life, 95% capacity factor.

This version (May 2026) includes:
  * radiator mass derived from Stefan-Boltzmann physics at realistic rejection
    temperatures, with NASA state-of-the-art areal densities, plus a heat-pump trade;
  * a methane-leakage term applied consistently to grid gas AND methalox propellant
    (GWP100 only);
  * a generic-LEO orbit scenario (vs. the dawn-dusk SSO baseline);
  * a launch-emission-intensity break-even sweep;
  * non-GHG co-benefit calculations (land area, cooling water).

Run:    python space_dc_lca.py            # prints the scenario tables
Import: from space_dc_lca import scenarios_with_ranges, total, ENERGY_TWH
"""

import numpy as np

# ----------------------------------------------------------------------------
# Functional unit
# ----------------------------------------------------------------------------
P_GW          = 1.0        # IT load (GW)
LIFE_YR       = 10
HOURS_PER_YR  = 8760
CF            = 0.95       # capacity factor (datacenter availability / orbital illumination)
ENERGY_TWH    = P_GW * HOURS_PER_YR * CF * LIFE_YR / 1000.0   # 83.2 TWh delivered


def mt_to_g_per_kwh(mt: float) -> float:
    """Convert one-time embodied emissions (Mt CO2e) to g CO2e / kWh delivered."""
    return mt * 1e12 / (ENERGY_TWH * 1e9)


# ----------------------------------------------------------------------------
# Shared: IT hardware (servers/GPUs) embodied - common to ground AND space
# Anchored on NVIDIA's published HGX H100 cradle-to-gate PCF (1,312 kg CO2e per
# 8-GPU board, ~164 kg/GPU) scaled to GW density with a system allowance for CPUs,
# memory, networking, racks and storage ~= 0.3 Mt/GW. Order-of-magnitude.
# Accelerators obsolesce on the same 3-5 yr cadence on the ground as in orbit, so
# BOTH cases carry one refresh of IT embodied (it_total below); the embodied term
# then CANCELS in the comparison and only the refresh LAUNCH mass is space-only.
# ----------------------------------------------------------------------------
IT_EMBODIED_MT_PER_GW = 0.30                                   # ~300 kt CO2/GW
IT_G_PER_KWH = mt_to_g_per_kwh(IT_EMBODIED_MT_PER_GW * P_GW)   # ~3.6 g/kWh (one build)

# ----------------------------------------------------------------------------
# Methane leakage (shared between grid gas and methalox propellant; GWP100 only)
# ----------------------------------------------------------------------------
CH4_GWP100        = 29.8     # IPCC AR6 (fossil methane), 100-yr
CH4_LEAK_CENTRAL  = 0.023    # Alvarez et al. (2018), Science: 2.3% of gross production
CH4_LEAK_LOW      = 0.010
CH4_LEAK_HIGH     = 0.035

# ----------------------------------------------------------------------------
# SPACE - launch
# ----------------------------------------------------------------------------
LAUNCH_KGCO2_PER_KG = 25.0   # Starship-class combustion CO2 per kg to LEO
UPPER_ATM_MULT      = 1.5    # lump-sum non-CO2 ascent forcing factor (BC, H2O, NOx)
UPPER_ATM_MULT_LOW  = 1.2    # optimistic (very clean methalox burn)
UPPER_ATM_MULT_HIGH = 3.0    # pessimistic (if BC closer to kerolox)

# Methalox propellant -> methane mass per kg of payload to LEO.
# Starship/Super Heavy stack carries ~1,200 t CH4; ~125 t payload to LEO.
PROP_CH4_T_PER_LAUNCH = 1200.0
PAYLOAD_T_PER_LAUNCH  = 125.0
CH4_KG_PER_KG_PAYLOAD = PROP_CH4_T_PER_LAUNCH / PAYLOAD_T_PER_LAUNCH   # ~9.6 kg CH4/kg


def propellant_leak_kgco2e_per_kg(leak=CH4_LEAK_CENTRAL):
    """Upstream methane-leakage CO2e per kg of payload launched (methalox)."""
    return CH4_KG_PER_KG_PAYLOAD * leak * CH4_GWP100


def launch_factor(launch_mult=UPPER_ATM_MULT, leak=CH4_LEAK_CENTRAL):
    """Effective launch GHG intensity (kg CO2e per kg to LEO).

    = combustion CO2 * non-CO2 multiplier + upstream methane leakage.
    """
    return LAUNCH_KGCO2_PER_KG * launch_mult + propellant_leak_kgco2e_per_kg(leak)


# ----------------------------------------------------------------------------
# SPACE - PV manufacturing (space-grade)
# ----------------------------------------------------------------------------
PV_SI_KGCO2_PER_KWP   = 500.0    # silicon-on-glass space array (central)
PV_IIIV_KGCO2_PER_KWP = 1500.0   # III-V (GaAs/multijunction) upper-bound stress test

# Space facility overhead ("PUE-equivalent"): avionics, ADCS, comms and thermal-loop
# pumps draw a parasitic load beyond IT. Cooling itself is passive (radiative), so
# space avoids the chiller energy that dominates a ground PUE; the overhead is small.
SPACE_PARASITIC      = 1.10   # facility/IT power ratio (PV + battery sized up by this)
SPACE_PARASITIC_LOW  = 1.05
SPACE_PARASITIC_HIGH = 1.20

# ----------------------------------------------------------------------------
# SPACE - eclipse-firming battery (dawn-dusk sun-synchronous orbit)
# ----------------------------------------------------------------------------
BATT_GWH               = 0.5     # ~30 min ride-through for 1 GW (worst-case solstice)
BATT_WH_PER_KG         = 200.0   # space-grade pack, forward-looking (current ~150-180)
BATT_EMB_KGCO2_PER_KWH = 60.0    # manufacturing embodied (Peiseler et al. 2024, LFP median ~62)
BATT_DOD_SPACE         = 0.40    # shallow DoD for cycle life (~5000+ eclipses/yr * 10 yr)


def battery_terms(usable_gwh=BATT_GWH, dod=BATT_DOD_SPACE):
    """Return (mass_t, kg_per_kw, embodied_Mt) for a space battery."""
    nameplate_gwh = usable_gwh / dod
    mass_t   = nameplate_gwh * 1e9 / BATT_WH_PER_KG / 1000.0
    kg_per_kw = mass_t * 1000.0 / (P_GW * 1e6)
    emb_mt   = nameplate_gwh * 1e6 * BATT_EMB_KGCO2_PER_KWH / 1e9
    return mass_t, kg_per_kw, emb_mt


_batt_mass_t, _batt_kg_per_kw, _batt_emb_mt = battery_terms()

# ----------------------------------------------------------------------------
# SPACE - thermal management (radiators), derived from physics
# Waste heat ~75% of IT load rejected radiatively in vacuum:
#   P/A = eps * sigma * (T_rad^4 - T_sink^4),  rejected from both faces of a panel.
# Specific mass = areal_density / (sides * flux).  See METHODOLOGY.md 4a.
# ----------------------------------------------------------------------------
WASTE_HEAT_FRACTION = 0.75
SIGMA   = 5.670374419e-8     # Stefan-Boltzmann (W/m2/K4)
EMISS   = 0.9               # radiator emissivity
T_SINK  = 250.0            # effective radiative sink temperature (K), El-Genk (2025)
# The bare radiating panel is only part of the thermal-control subsystem. Heat
# transport (cold plates, pumped loops, pumps, headers) and MMOD armour add mass.
# ISS EATCS flight hardware implies a transport/integration multiplier of ~1.3-1.5x
# the panel mass (NASA ISS ATCS Overview); El-Genk (2025) adds +30-50% for MMOD
# armour. Applied as a system-overhead multiplier on the panel-derived mass.
RAD_SYS_OVERHEAD       = 1.4    # central thermal-bus/transport + integration overhead
RAD_SYS_OVERHEAD_LOW   = 1.3
RAD_SYS_OVERHEAD_HIGH  = 1.6


def radiator_flux_wpm2(t_rad_k, sides=2):
    """Net radiative heat flux per m2 of (double-sided) panel."""
    return sides * EMISS * SIGMA * (t_rad_k**4 - T_SINK**4)


def radiator_kg_per_kw_th(t_rad_k, areal_density_kg_m2, sides=2):
    """Radiator specific mass (kg per kW_thermal) at a given rejection temperature."""
    flux_kw_m2 = radiator_flux_wpm2(t_rad_k, sides) / 1000.0
    return areal_density_kg_m2 / flux_kw_m2


def radiator_kg_per_kw_it(t_rad_k, areal_density_kg_m2, sides=2):
    """Radiator specific mass per kW of IT load (waste-heat fraction applied)."""
    return radiator_kg_per_kw_th(t_rad_k, areal_density_kg_m2, sides) * WASTE_HEAT_FRACTION


# Three physics-anchored radiator tiers (T_rad, areal density, sides), all PASSIVE
# at or below the ~375 K GPU junction so no heat pump is required:
#   conventional: ISS-heritage areal density at GPU-compatible temperature
#   near-term:    lower areal density deployable panels
#   advanced:     advanced lightweight (e.g. carbon-fibre) panels, still passive
# Each is multiplied by RAD_SYS_OVERHEAD for transport/integration hardware.
# (A heat-pumped high-T radiator could be lighter still but costs a large fraction
#  of IT power; treated separately as an optimistic bound, not a modelled tier.)
RAD_HIGH = dict(t_rad_k=320.0, areal_density_kg_m2=8.0, sides=2)   # conventional
RAD_MID  = dict(t_rad_k=350.0, areal_density_kg_m2=4.0, sides=2)   # near-term
RAD_LOW  = dict(t_rad_k=350.0, areal_density_kg_m2=2.0, sides=2)   # advanced lightweight

RADIATOR_KG_PER_KW_IT_HIGH = radiator_kg_per_kw_it(**RAD_HIGH) * RAD_SYS_OVERHEAD
RADIATOR_KG_PER_KW_IT_MID  = radiator_kg_per_kw_it(**RAD_MID) * RAD_SYS_OVERHEAD
RADIATOR_KG_PER_KW_IT_LOW  = radiator_kg_per_kw_it(**RAD_LOW) * RAD_SYS_OVERHEAD


def heat_pump_power_fraction(t_cold_k, t_hot_k, second_law_eff=0.5):
    """Fraction of IT power a heat pump needs to lift waste heat from t_cold to t_hot.

    Carnot work to move Q from T_cold to T_hot: W = Q*(T_hot - T_cold)/T_cold,
    divided by a second-law efficiency. Q = waste-heat fraction of IT power.
    """
    if t_hot_k <= t_cold_k:
        return 0.0
    carnot = (t_hot_k - t_cold_k) / t_cold_k
    return WASTE_HEAT_FRACTION * carnot / second_law_eff


# ----------------------------------------------------------------------------
# SPACE - GPU refresh (obsolescence every 3-5 years)
# Radiation at dawn-dusk SSO is modest (Suncatcher: ~750 rad over 5 yr shielded),
# so refresh is obsolescence-driven, not radiation-driven.
# ----------------------------------------------------------------------------
GPU_REFRESH_COUNT  = 1       # number of full IT hardware refreshes over 10 yr
GPU_MASS_KG_PER_KW = 5.0    # mass of compute hardware replaced per refresh

# ----------------------------------------------------------------------------
# SPACE - station-keeping / drag make-up (recurring, launched as propellant+hardware)
# Aerodynamic drag on a large LEO/SSO array must be offset over 10 yr. From NRLMSIS
# densities at 600-800 km (Picone et al. 2002; Emmert et al. 2021), Cd~2.2, and
# electric-propulsion Isp~2000 s, the make-up propellant is only ~0.02-0.4 kg/kW
# over 10 yr; adding thruster/tank dry mass gives a small total. See SI.
STATIONKEEPING_KG_PER_KW      = 1.0    # propellant + thrusters + tanks over 10 yr
STATIONKEEPING_KG_PER_KW_LOW  = 0.3
STATIONKEEPING_KG_PER_KW_HIGH = 3.0

# ----------------------------------------------------------------------------
# SPACE - system mass intensity scenarios (kg per kW; bus + PV + structure + ADCS,
# excluding battery, radiator and station-keeping, which are added explicitly).
# ----------------------------------------------------------------------------
MASS_LOW, MASS_MID, MASS_HIGH = 15.0, 30.0, 60.0   # Starcloud target -> conservative


def space_scenario(mass_kg_per_kw, pv_kgco2_per_kwp=PV_SI_KGCO2_PER_KWP,
                   launch_mult=UPPER_ATM_MULT, radiator_kg_per_kw_it_=RADIATOR_KG_PER_KW_IT_MID,
                   gpu_refresh=GPU_REFRESH_COUNT, leak=CH4_LEAK_CENTRAL,
                   pv_mass_factor=1.0, batt_mass_t=None, batt_emb_mt=None,
                   parasitic=SPACE_PARASITIC, stationkeeping=STATIONKEEPING_KG_PER_KW):
    """Return component intensities (g/kWh) for a space datacenter scenario.

    Components: 'solar_storage' (PV + battery), 'launch', 'launch_ch4', 'it',
    'refresh_launch'. pv_mass_factor scales PV array size/embodied (e.g. generic-LEO
    oversizing); parasitic scales PV + battery for non-IT facility loads.
    """
    if batt_mass_t is None:
        batt_mass_t, _, batt_emb_mt = _batt_mass_t, _batt_kg_per_kw, _batt_emb_mt
    # Parasitic (facility/IT) load scales PV array and battery up.
    pv_scale  = pv_mass_factor * parasitic
    batt_mass_t = batt_mass_t * parasitic
    batt_emb_mt = batt_emb_mt * parasitic
    # Split the launch factor into a combustion + non-CO2 part and an upstream
    # propellant-methane part, so the methane term can be shown separately.
    factor_comb = LAUNCH_KGCO2_PER_KG * launch_mult
    factor_leak = propellant_leak_kgco2e_per_kg(leak)

    # Launched mass: bus/PV/structure + battery + radiators + station-keeping.
    batt_kg_per_kw = batt_mass_t * 1000.0 / (P_GW * 1e6)
    total_mass_kg_per_kw = (mass_kg_per_kw * pv_scale
                            + batt_kg_per_kw + radiator_kg_per_kw_it_ + stationkeeping)
    mass_t    = total_mass_kg_per_kw * P_GW * 1e6 / 1000.0
    pv_mt     = pv_kgco2_per_kwp * pv_scale * P_GW * 1e6 / 1e9

    # GPU refresh: extra launch mass + extra IT embodied
    refresh_mass_t    = gpu_refresh * GPU_MASS_KG_PER_KW * P_GW * 1e6 / 1000.0
    refresh_it_mt     = gpu_refresh * IT_EMBODIED_MT_PER_GW * P_GW

    launch_comb_mt  = mass_t * factor_comb / 1e6
    refresh_comb_mt = refresh_mass_t * factor_comb / 1e6
    leak_mt         = (mass_t + refresh_mass_t) * factor_leak / 1e6

    return {
        "solar_storage":  mt_to_g_per_kwh(pv_mt + batt_emb_mt),
        "launch":         mt_to_g_per_kwh(launch_comb_mt),
        "launch_ch4":     mt_to_g_per_kwh(leak_mt),
        "refresh_launch": mt_to_g_per_kwh(refresh_comb_mt),
        "it":             IT_G_PER_KWH + mt_to_g_per_kwh(refresh_it_mt),
    }


def space_scenario_range(mass_kg_per_kw, pv_kgco2_per_kwp=PV_SI_KGCO2_PER_KWP,
                         radiator_kg_per_kw_it_=RADIATOR_KG_PER_KW_IT_MID,
                         gpu_refresh=GPU_REFRESH_COUNT):
    """(low, central, high) totals varying the non-CO2 multiplier (1.2-3.0x)."""
    low = space_scenario(mass_kg_per_kw, pv_kgco2_per_kwp, UPPER_ATM_MULT_LOW,
                         radiator_kg_per_kw_it_, gpu_refresh)
    cen = space_scenario(mass_kg_per_kw, pv_kgco2_per_kwp, UPPER_ATM_MULT,
                         radiator_kg_per_kw_it_, gpu_refresh)
    high = space_scenario(mass_kg_per_kw, pv_kgco2_per_kwp, UPPER_ATM_MULT_HIGH,
                          radiator_kg_per_kw_it_, gpu_refresh)
    return total(low), total(cen), total(high)


# ----------------------------------------------------------------------------
# SPACE - generic LEO (vs. dawn-dusk SSO): ~35 min eclipse per ~90 min orbit.
# Battery must ride through every orbit, and the PV array must be oversized to
# both serve load and recharge the battery during the sunlit fraction.
# ----------------------------------------------------------------------------
LEO_ECLIPSE_MIN = 35.0
LEO_ORBIT_MIN   = 90.0


def generic_leo_scenario(mass_kg_per_kw, radiator_kg_per_kw_it_=RADIATOR_KG_PER_KW_IT_MID,
                         launch_mult=UPPER_ATM_MULT, leak=CH4_LEAK_CENTRAL):
    """Space scenario in a generic (non-SSO) LEO with a large eclipse fraction."""
    sunlit_min   = LEO_ORBIT_MIN - LEO_ECLIPSE_MIN
    usable_gwh   = P_GW * (LEO_ECLIPSE_MIN / 60.0)          # ride-through per orbit
    pv_oversize  = 1.0 + LEO_ECLIPSE_MIN / sunlit_min        # serve load + recharge
    bmass_t, _, bemb_mt = battery_terms(usable_gwh=usable_gwh)
    return space_scenario(mass_kg_per_kw, launch_mult=launch_mult,
                          radiator_kg_per_kw_it_=radiator_kg_per_kw_it_, leak=leak,
                          pv_mass_factor=pv_oversize, batt_mass_t=bmass_t, batt_emb_mt=bemb_mt)


# ----------------------------------------------------------------------------
# GROUND - facility overhead (PUE) applied to all ground generation
# A ground datacenter must generate PUE x IT to deliver the IT load (cooling, fans,
# power conditioning). Uptime Institute 2024 global avg ~1.56; Google 1.09, Meta
# 1.08 hyperscale. Central 1.2 for a modern AI build; the (PUE-1) overhead is the
# active-cooling energy that the orbital case avoids (passive radiative rejection).
# T&D losses (~5-6%, EIA/IEA) apply if grid-supplied; co-located dedicated plants
# (modelled here) avoid them, so T&D is treated as a noted sensitivity, not applied.
# ----------------------------------------------------------------------------
GROUND_PUE      = 1.20
GROUND_PUE_LOW  = 1.10
GROUND_PUE_HIGH = 1.50

# ----------------------------------------------------------------------------
# GROUND - gas
# ----------------------------------------------------------------------------
GAS_CCGT_GCO2_PER_KWH = 486.0     # NREL harmonized lifecycle, GWP100 (incl. upstream CH4)
# Decompose into a combustion+midstream floor and a leakage-scaled CH4 term so the
# methane-leakage sensitivity can be applied consistently with the rocket side. The
# floor is calibrated so the central leakage rate reproduces the NREL 486 g/kWh.
GAS_CH4_KG_PER_KWH   = 0.135          # CH4 burned per kWh_e (~55% efficient CCGT)


def _gas_leak_gco2e(leak):
    return GAS_CH4_KG_PER_KWH * leak * CH4_GWP100 * 1000.0


GAS_COMBUSTION_FLOOR = GAS_CCGT_GCO2_PER_KWH - _gas_leak_gco2e(CH4_LEAK_CENTRAL)  # ~393


def gas_intensity(leak=CH4_LEAK_CENTRAL):
    """Gas CCGT lifecycle intensity with leakage-scaled upstream methane (GWP100).

    Calibrated so gas_intensity(CH4_LEAK_CENTRAL) == GAS_CCGT_GCO2_PER_KWH (486).
    """
    return GAS_COMBUSTION_FLOOR + _gas_leak_gco2e(leak)

# ----------------------------------------------------------------------------
# GROUND - nuclear (firm low-carbon baseload; no overbuild or storage needed)
# ----------------------------------------------------------------------------
NUCLEAR_GCO2_PER_KWH = 12.0     # lifecycle harmonized median (Warner & Heath 2012)
NUCLEAR_LOW, NUCLEAR_HIGH = 5.0, 20.0   # centrifuge/UNECE low end -> enrichment-heavy high

# ----------------------------------------------------------------------------
# GROUND - hybrid (90% solar+storage / 10% gas backup)
# ----------------------------------------------------------------------------
HYBRID_SOLAR_STORAGE_GCO2_PER_KWH = 60.0
HYBRID_GAS_FRACTION               = 0.10

# ----------------------------------------------------------------------------
# GROUND - no-gas (solar overbuild + storage)
# ----------------------------------------------------------------------------
PV_BASE_GCO2_PER_KWH = 40.0     # modern utility PV, per kWh GENERATED (NREL harmonized)
GEN_PER_DELIVERED    = 1.5      # generation/delivered with overbuild + curtailment
GROUND_BATT_EMB_KGCO2_PER_KWH = 55.0  # utility LFP (Peiseler et al. 2024: LFP median ~62)
GROUND_BATT_CYCLES = 5000; GROUND_BATT_DOD = 0.9; GROUND_BATT_RT = 0.9
FRAC_STORED = 0.55
MULTIDAY_FACTOR = 1.3


def _ground_storage_adder(frac_stored=FRAC_STORED):
    per_throughput = (GROUND_BATT_EMB_KGCO2_PER_KWH * 1000.0
                      / (GROUND_BATT_CYCLES * GROUND_BATT_DOD * GROUND_BATT_RT))
    return frac_stored * per_throughput * MULTIDAY_FACTOR


def nogas_solar_storage(pv_base=PV_BASE_GCO2_PER_KWH, gpd=GEN_PER_DELIVERED,
                        frac_stored=FRAC_STORED):
    return pv_base * gpd + _ground_storage_adder(frac_stored)


NOGAS_CENTRAL = nogas_solar_storage()
NOGAS_LOW     = nogas_solar_storage(30.0, 1.3, 0.45)   # excellent site, lean storage
NOGAS_HIGH    = nogas_solar_storage(45.0, 2.0, 0.65)   # poor site, reliability-heavy

# Shared IT (base + one refresh) and decarbonised-ground totals incl. PUE, used as
# reference lines/targets throughout (so figures and break-even stay consistent).
IT_TOTAL_G_PER_KWH    = IT_G_PER_KWH * (1 + GPU_REFRESH_COUNT)
GROUND_NOGAS_TOTAL    = GROUND_PUE * NOGAS_CENTRAL + IT_TOTAL_G_PER_KWH
GROUND_NUCLEAR_TOTAL  = GROUND_PUE * NUCLEAR_GCO2_PER_KWH + IT_TOTAL_G_PER_KWH


# ----------------------------------------------------------------------------
# Non-GHG co-benefits: land footprint and cooling water (ground vs space)
# ----------------------------------------------------------------------------
SOLAR_CF_AC          = 0.25     # AC capacity factor, good US site (single-axis tracking)
LAND_ACRES_PER_MW_AC = 7.6      # Ong et al. (2013), NREL/TP-6A20-56290 (fixed-tilt total)
ACRES_PER_KM2        = 247.105
MANHATTAN_KM2        = 59.1
WATER_L_PER_KWH      = 0.5      # direct evaporative cooling water (Siddik et al. 2021, ERL; ~0.2-1.8)


def ground_solar_land_km2(gas_fraction=0.10, gpd=GEN_PER_DELIVERED):
    """Approx. land for the solar fleet of a 1 GW datacenter (mostly-solar ground)."""
    avg_solar_load_gw = P_GW * (1.0 - gas_fraction)
    gen_gw            = avg_solar_load_gw * gpd            # incl. overbuild/curtailment
    nameplate_mw_ac   = gen_gw * 1000.0 / SOLAR_CF_AC
    acres             = nameplate_mw_ac * LAND_ACRES_PER_MW_AC
    return acres / ACRES_PER_KM2


def datacenter_cooling_water_megatons():
    """Lifetime evaporative cooling water for a ground datacenter (Mt; 1 t = 1 m3)."""
    litres = ENERGY_TWH * 1e9 * WATER_L_PER_KWH   # TWh -> kWh -> L
    return litres / 1e3 / 1e6                      # L -> tonnes -> Mt


# ----------------------------------------------------------------------------
# Assemble scenarios
# ----------------------------------------------------------------------------
def scenarios(leak=CH4_LEAK_CENTRAL):
    sl = space_scenario(MASS_LOW, radiator_kg_per_kw_it_=RADIATOR_KG_PER_KW_IT_LOW, leak=leak)
    sm = space_scenario(MASS_MID, radiator_kg_per_kw_it_=RADIATOR_KG_PER_KW_IT_MID, leak=leak)
    sh = space_scenario(MASS_HIGH, radiator_kg_per_kw_it_=RADIATOR_KG_PER_KW_IT_HIGH, leak=leak)

    # IT embodied carried by BOTH ground and space at base + one refresh, so it
    # cancels in the comparison (ground hardware obsolesces on the same cadence).
    it_total = IT_G_PER_KWH * (1 + GPU_REFRESH_COUNT)
    pue = GROUND_PUE
    return {
        "Ground - 100% gas CCGT":
            {"gas": pue * gas_intensity(leak), "it": it_total},
        "Ground - 90% solar+storage / 10% gas":
            {"gas": pue * HYBRID_GAS_FRACTION * gas_intensity(leak),
             "solar_storage": pue * (1 - HYBRID_GAS_FRACTION) * HYBRID_SOLAR_STORAGE_GCO2_PER_KWH,
             "it": it_total},
        "Ground - no gas: solar overbuild + storage":
            {"solar_storage": pue * NOGAS_CENTRAL, "it": it_total,
             "_range": (pue * NOGAS_LOW + it_total, pue * NOGAS_HIGH + it_total)},
        "Ground - nuclear (firm baseload)":
            {"nuclear": pue * NUCLEAR_GCO2_PER_KWH, "it": it_total,
             "_range": (pue * NUCLEAR_LOW + it_total, pue * NUCLEAR_HIGH + it_total)},
        "Space - high (conv. radiators)": sh,
        "Space - mid":                    sm,
        "Space - low (Starcloud-target)": sl,
    }


def scenarios_with_ranges(leak=CH4_LEAK_CENTRAL, mc=None):
    """scenarios() with _range tuples set from the Monte Carlo 5th-95th percentiles
    (full multi-parameter propagation), replacing the old single-parameter whiskers."""
    sc = scenarios(leak)
    if mc is None:
        mc = monte_carlo()
    for name, (p5, p50, p95) in mc.items():
        if name in sc:
            sc[name]["_range"] = (p5, p95)
    return sc


def total(components):
    return sum(v for k, v in components.items() if not k.startswith("_"))


# ----------------------------------------------------------------------------
# Launch-emission-intensity break-even sweep
# ----------------------------------------------------------------------------
def space_total_at_launch_factor(mass_kg_per_kw, radiator_kg_per_kw_it_, eff_launch_factor):
    """Space lifecycle total (g/kWh) as a function of the effective launch factor.

    Solves the scenario at the central non-CO2 multiplier, then rescales the launch
    components linearly to the requested effective launch factor.
    """
    base = space_scenario(mass_kg_per_kw, radiator_kg_per_kw_it_=radiator_kg_per_kw_it_)
    base_factor = launch_factor(UPPER_ATM_MULT, CH4_LEAK_CENTRAL)
    scale = eff_launch_factor / base_factor
    launchy = base["launch"] + base["launch_ch4"] + base["refresh_launch"]
    return base["solar_storage"] + base["it"] + scale * launchy


def breakeven_launch_factor(mass_kg_per_kw, radiator_kg_per_kw_it_, ground_target):
    """Effective launch factor at which space total equals a ground target (g/kWh)."""
    base = space_scenario(mass_kg_per_kw, radiator_kg_per_kw_it_=radiator_kg_per_kw_it_)
    base_factor = launch_factor(UPPER_ATM_MULT, CH4_LEAK_CENTRAL)
    fixed   = base["solar_storage"] + base["it"]
    launchy = base["launch"] + base["launch_ch4"] + base["refresh_launch"]
    if launchy <= 0:
        return float('inf')
    scale = (ground_target - fixed) / launchy
    return scale * base_factor


# ----------------------------------------------------------------------------
# Sensitivity table (space-mid vs ground no-gas)
# ----------------------------------------------------------------------------
def sensitivity_table():
    base_space  = total(space_scenario(MASS_MID, radiator_kg_per_kw_it_=RADIATOR_KG_PER_KW_IT_MID))
    base_ground = GROUND_NOGAS_TOTAL

    return [
        ("Upper-atm non-CO2 mult", "1.2x", "1.5x", "3.0x",
         total(space_scenario(MASS_MID, launch_mult=1.2, radiator_kg_per_kw_it_=RADIATOR_KG_PER_KW_IT_MID)),
         base_space,
         total(space_scenario(MASS_MID, launch_mult=3.0, radiator_kg_per_kw_it_=RADIATOR_KG_PER_KW_IT_MID))),
        ("System mass (kg/kW)", "15", "30", "60",
         total(space_scenario(MASS_LOW, radiator_kg_per_kw_it_=RADIATOR_KG_PER_KW_IT_LOW)),
         base_space,
         total(space_scenario(MASS_HIGH, radiator_kg_per_kw_it_=RADIATOR_KG_PER_KW_IT_HIGH))),
        ("Radiator tier", "advanced", "near-term", "conventional",
         total(space_scenario(MASS_MID, radiator_kg_per_kw_it_=RADIATOR_KG_PER_KW_IT_LOW)),
         base_space,
         total(space_scenario(MASS_MID, radiator_kg_per_kw_it_=RADIATOR_KG_PER_KW_IT_HIGH))),
        ("Propellant CH4 leakage", "1.0%", "2.3%", "3.5%",
         total(space_scenario(MASS_MID, radiator_kg_per_kw_it_=RADIATOR_KG_PER_KW_IT_MID, leak=CH4_LEAK_LOW)),
         base_space,
         total(space_scenario(MASS_MID, radiator_kg_per_kw_it_=RADIATOR_KG_PER_KW_IT_MID, leak=CH4_LEAK_HIGH))),
        ("GPU refresh count", "0", "1", "2",
         total(space_scenario(MASS_MID, radiator_kg_per_kw_it_=RADIATOR_KG_PER_KW_IT_MID, gpu_refresh=0)),
         base_space,
         total(space_scenario(MASS_MID, radiator_kg_per_kw_it_=RADIATOR_KG_PER_KW_IT_MID, gpu_refresh=2))),
        ("Ground PV base (g/kWh gen)", "30", "40", "50",
         GROUND_PUE * nogas_solar_storage(30.0) + IT_TOTAL_G_PER_KWH,
         base_ground,
         GROUND_PUE * nogas_solar_storage(50.0) + IT_TOTAL_G_PER_KWH),
    ]


# ----------------------------------------------------------------------------
# Monte Carlo uncertainty propagation (all parameters varied jointly)
# Triangular distributions over (low, central, high) from the parameter table.
# Decouples system mass and radiator (sampled independently) and propagates every
# parameter, rather than varying one at a time. Returns (p5, p50, p95) per scenario.
# ----------------------------------------------------------------------------
def monte_carlo(n=40000, seed=0):
    rng = np.random.default_rng(seed)
    def tri(lo, mode, hi):
        return rng.triangular(lo, mode, hi, n)

    leak_g = tri(0.010, 0.023, 0.035)
    pue    = tri(GROUND_PUE_LOW, GROUND_PUE, GROUND_PUE_HIGH)
    it_t   = IT_TOTAL_G_PER_KWH                         # embodied; cancels, treated fixed

    # --- ground ---
    pv_base = tri(30.0, 40.0, 50.0); gpd = tri(1.3, 1.5, 2.0); frac = tri(0.45, 0.55, 0.65)
    g_batt  = tri(40.0, 55.0, 75.0)
    storage = frac * (g_batt * 1000.0 / (GROUND_BATT_CYCLES * GROUND_BATT_DOD * GROUND_BATT_RT)) * MULTIDAY_FACTOR
    nogas_ss = pv_base * gpd + storage                  # solar+storage, per kWh delivered (pre-PUE)
    nogas   = pue * nogas_ss + it_t
    nuclear = pue * tri(NUCLEAR_LOW, NUCLEAR_GCO2_PER_KWH, NUCLEAR_HIGH) + it_t
    gas_int = GAS_COMBUSTION_FLOOR + GAS_CH4_KG_PER_KWH * leak_g * CH4_GWP100 * 1000.0
    gas     = pue * gas_int + it_t
    # hybrid: 10% gas backup firms the load, so the 90% solar+storage needs less
    # overbuild/storage than the full no-gas case. Scale the (correlated) no-gas
    # solar+storage draw to the hybrid central intensity rather than inventing new
    # bounds, so the hybrid band tracks the same PV/storage/leakage uncertainty.
    hybrid_ss = nogas_ss * (HYBRID_SOLAR_STORAGE_GCO2_PER_KWH / NOGAS_CENTRAL)
    hybrid  = pue * (HYBRID_GAS_FRACTION * gas_int
                     + (1.0 - HYBRID_GAS_FRACTION) * hybrid_ss) + it_t

    # --- space (vectorised replica of space_scenario) ---
    def space_mc(mass, rad):
        mult = tri(UPPER_ATM_MULT_LOW, UPPER_ATM_MULT, UPPER_ATM_MULT_HIGH)
        comb = tri(20.0, 25.0, 35.0)
        pv   = tri(400.0, 500.0, 700.0)
        wh   = tri(150.0, 200.0, 250.0); bemb = tri(50.0, 60.0, 100.0)
        par  = tri(SPACE_PARASITIC_LOW, SPACE_PARASITIC, SPACE_PARASITIC_HIGH)
        sk   = tri(STATIONKEEPING_KG_PER_KW_LOW, STATIONKEEPING_KG_PER_KW, STATIONKEEPING_KG_PER_KW_HIGH)
        leak_s = tri(0.010, 0.023, 0.035)
        nameplate = BATT_GWH / BATT_DOD_SPACE
        batt_mass_t = nameplate * 1e9 / wh / 1000.0 * par
        batt_emb_mt = nameplate * 1e6 * bemb / 1e9 * par
        batt_kg_per_kw = batt_mass_t * 1000.0 / (P_GW * 1e6)
        total_mass = mass * par + batt_kg_per_kw + rad + sk
        mass_t = total_mass * P_GW * 1e6 / 1000.0
        refresh_mass_t = GPU_REFRESH_COUNT * GPU_MASS_KG_PER_KW * P_GW * 1e6 / 1000.0
        launch = mt_to_g_per_kwh((mass_t + refresh_mass_t) * comb * mult / 1e6)
        ch4    = mt_to_g_per_kwh((mass_t + refresh_mass_t) * CH4_KG_PER_KG_PAYLOAD * leak_s * CH4_GWP100 / 1e6)
        ss     = mt_to_g_per_kwh(pv * par * P_GW * 1e6 / 1e9 + batt_emb_mt)
        return ss + launch + ch4 + it_t

    # radiator sampled over full range (areal density, temperature, overhead)
    areal = tri(5.0, 8.0, 13.0); t_rad = rng.uniform(300.0, 350.0, n)
    ov    = tri(RAD_SYS_OVERHEAD_LOW, RAD_SYS_OVERHEAD, RAD_SYS_OVERHEAD_HIGH)
    flux_kw = 2 * EMISS * SIGMA * (t_rad**4 - T_SINK**4) / 1000.0
    rad_full = (areal / flux_kw) * WASTE_HEAT_FRACTION * ov

    space_low  = space_mc(MASS_LOW,  RADIATOR_KG_PER_KW_IT_LOW)
    space_mid  = space_mc(MASS_MID,  RADIATOR_KG_PER_KW_IT_MID)
    space_high = space_mc(MASS_HIGH, RADIATOR_KG_PER_KW_IT_HIGH)
    space_all  = space_mc(tri(MASS_LOW, MASS_MID, MASS_HIGH), rad_full)

    def pct(a):
        return tuple(float(x) for x in np.percentile(a, [5, 50, 95]))

    return {
        "Ground - 100% gas CCGT": pct(gas),
        "Ground - 90% solar+storage / 10% gas": pct(hybrid),
        "Ground - no gas: solar overbuild + storage": pct(nogas),
        "Ground - nuclear (firm baseload)": pct(nuclear),
        "Space - high (conv. radiators)": pct(space_high),
        "Space - mid": pct(space_mid),
        "Space - low (Starcloud-target)": pct(space_low),
        "Space - composite (mass & radiator sampled)": pct(space_all),
    }


# ----------------------------------------------------------------------------
# Harmonisation of Aili et al. (2025), Nature Electronics, onto this metric
# ----------------------------------------------------------------------------
# Their headline is a life-cycle "carbon usage effectiveness" (CUE: total emissions
# per unit IT energy) of ~0.7 kgCO2e/kWh at a 4-yr server life, which is NOT directly
# comparable to the physical, delivered-energy intensity used here. Their Supplementary
# Tables 4-11, however, give a full per-satellite component breakdown that we can
# re-express on this study's basis. Each computational satellite carries 3 Dell R740
# servers. One-time emissions (kgCO2e per satellite):
AILI_SERVERS_PER_SAT        = 3
AILI_C_SERVER_KG            = 970.0    # Dell R740 manufacturing, per server (SI Table 6)
AILI_C_COOLER_KG            = 490.0    # Al active radiative cooler, per server (SI eq 24)
AILI_C_CARRIER_KG           = 2940.0   # Starlink-v1.0 bus + solar arrays, per sat (SI eq 30)
AILI_C_LAUNCH_KG            = 790.0    # Falcon-9 launch share, per sat (SI eq 35)
AILI_E_IT_PER_SERVER_KWH_YR = 2704.0   # IT energy, light-medium workload (SI Table 5)
AILI_SERVER_LIFE_YR         = 4        # their stated mean server lifespan
# Coefficients to reproduce their full life-cycle CUE (SI Table 11):
AILI_PUE         = 1.1
AILI_I1, AILI_E1_E2 = 214.0, 0.02      # scope 1 (backup gen): intensity, energy ratio
AILI_I3, AILI_E3RC_E2 = 271.0, 1.56    # scope 3 RECURRENT: intensity, energy ratio
AILI_E3OT_E2     = 3.35                 # scope 3 one-time energy ratio (units: years)


def aili_harmonised(server_life_yr=AILI_SERVER_LIFE_YR):
    """Aili et al. (2025) orbital data centre re-expressed on this study's metric:
    physical lifecycle emissions (gCO2e per kWh of IT energy delivered), broken into
    the same kind of components used here. Excludes their corporate scope-3 *recurrent*
    term (business travel, purchased services), which is outside this study's physical
    boundary, is common to their ground baseline, and dominates their CUE (~65%)."""
    e_it_life = AILI_SERVERS_PER_SAT * AILI_E_IT_PER_SERVER_KWH_YR * server_life_yr
    g = lambda c_kg: c_kg * 1000.0 / e_it_life      # kgCO2e/sat -> gCO2e per kWh IT
    return {
        "it":              g(AILI_SERVERS_PER_SAT * AILI_C_SERVER_KG),   # server mfg
        "power_structure": g(AILI_C_CARRIER_KG),                         # bus + arrays
        "thermal":         g(AILI_SERVERS_PER_SAT * AILI_C_COOLER_KG),   # Al cooler
        "launch":          g(AILI_C_LAUNCH_KG),                          # launch share
    }


def aili_full_cue(server_life_yr=AILI_SERVER_LIFE_YR):
    """Reproduce Aili's full life-cycle CUE (gCO2e/kWh) and its split into the physical
    one-time terms (comparable here) and the corporate scope-3 recurrent term (not)."""
    onetime   = AILI_PUE * (AILI_E3OT_E2 / server_life_yr) * AILI_I3
    recurrent = AILI_PUE * AILI_E3RC_E2 * AILI_I3
    scope1    = AILI_PUE * AILI_E1_E2 * AILI_I1
    return {"total": onetime + recurrent + scope1,
            "physical_onetime": onetime + scope1, "recurrent": recurrent}


if __name__ == "__main__":
    print(f"Functional unit: {P_GW} GW IT, {LIFE_YR} yr, CF {CF} -> {ENERGY_TWH:.1f} TWh delivered\n")

    mt, kgkw, emb = battery_terms()
    print(f"Space firming battery (dawn-dusk SSO): {BATT_GWH} GWh usable, "
          f"{BATT_GWH/BATT_DOD_SPACE:.2f} GWh nameplate (DoD {BATT_DOD_SPACE}) "
          f"-> {mt:.0f} t (+{kgkw:.1f} kg/kW, +{emb:.3f} Mt)")

    print(f"\nRadiator specific mass (physics-derived) per kW_IT, x{RAD_SYS_OVERHEAD} system overhead:")
    for label, kw, full in [("conventional (320 K, 8 kg/m2)", RAD_HIGH, RADIATOR_KG_PER_KW_IT_HIGH),
                            ("near-term (350 K, 4 kg/m2)",    RAD_MID,  RADIATOR_KG_PER_KW_IT_MID),
                            ("advanced (350 K, 2 kg/m2)",     RAD_LOW,  RADIATOR_KG_PER_KW_IT_LOW)]:
        print(f"   {label:<32} panel {radiator_kg_per_kw_it(**kw):4.2f} -> system "
              f"{full:5.2f} kg/kW_IT (flux {radiator_flux_wpm2(kw['t_rad_k']):.0f} W/m2)")
    print(f"   heat-pump power to lift 330->500 K: "
          f"{heat_pump_power_fraction(330, 500)*100:.0f}% of IT power (advanced bound only)")

    print(f"\nLaunch factor (central): {launch_factor():.1f} kg CO2e/kg "
          f"(= {LAUNCH_KGCO2_PER_KG}*{UPPER_ATM_MULT} + {propellant_leak_kgco2e_per_kg():.1f} leakage)")
    print(f"Gas CCGT (leak {CH4_LEAK_CENTRAL*100:.1f}%): {gas_intensity():.0f} g/kWh")
    print(f"No-gas ground central {NOGAS_CENTRAL:.0f} g/kWh (range {NOGAS_LOW:.0f}-{NOGAS_HIGH:.0f})\n")

    print(f"Ground PUE {GROUND_PUE}; space parasitic {SPACE_PARASITIC}; "
          f"radiator system overhead {RAD_SYS_OVERHEAD}x; station-keeping "
          f"{STATIONKEEPING_KG_PER_KW} kg/kW; shared IT (base+refresh) "
          f"{IT_TOTAL_G_PER_KWH:.1f} g/kWh")
    print(f"Decarbonised ground spans nuclear {GROUND_NUCLEAR_TOTAL:.0f} -> "
          f"solar+storage {GROUND_NOGAS_TOTAL:.0f} g/kWh\n")

    print(f"{'Scenario':<46}{'gas':>6}{'nuc':>6}{'sol+st':>8}{'launch':>8}{'CH4':>6}{'refr':>6}{'IT':>6}{'TOTAL':>8}")
    print("-" * 100)
    for name, comp in scenarios().items():
        print(f"{name:<46}{comp.get('gas',0):>6.1f}{comp.get('nuclear',0):>6.1f}"
              f"{comp.get('solar_storage',0):>8.1f}"
              f"{comp.get('launch',0):>8.1f}{comp.get('launch_ch4',0):>6.1f}"
              f"{comp.get('refresh_launch',0):>6.1f}"
              f"{comp.get('it',0):>6.1f}{total(comp):>8.1f}")

    print("\n--- UNCERTAINTY RANGES (non-CO2 multiplier 1.2-3.0x) ---")
    sc = scenarios_with_ranges()
    print(f"{'Scenario':<46}{'Low':>8}{'Central':>9}{'High':>8}")
    print("-" * 71)
    for name, comp in sc.items():
        rng = comp.get('_range'); t = total(comp)
        if rng:
            print(f"{name:<46}{rng[0]:>8.1f}{t:>9.1f}{rng[1]:>8.1f}")
        else:
            print(f"{name:<46}{'-':>8}{t:>9.1f}{'-':>8}")

    print("\n--- GENERIC LEO vs DAWN-DUSK SSO (mid mass) ---")
    sso = total(space_scenario(MASS_MID, radiator_kg_per_kw_it_=RADIATOR_KG_PER_KW_IT_MID))
    leo = total(generic_leo_scenario(MASS_MID))
    print(f"   dawn-dusk SSO: {sso:.1f} g/kWh    generic LEO: {leo:.1f} g/kWh")

    print("\n--- BREAK-EVEN: launch factor where space total = ground no-gas central ---")
    gtgt = GROUND_NOGAS_TOTAL
    for label, mass, rad in [("low", MASS_LOW, RADIATOR_KG_PER_KW_IT_LOW),
                             ("mid", MASS_MID, RADIATOR_KG_PER_KW_IT_MID),
                             ("high", MASS_HIGH, RADIATOR_KG_PER_KW_IT_HIGH)]:
        be = breakeven_launch_factor(mass, rad, gtgt)
        print(f"   space-{label:<4} crosses {gtgt:.0f} g/kWh at launch factor "
              f"{be:.0f} kg CO2e/kg (central is {launch_factor():.0f})")

    print("\n--- NON-GHG CO-BENEFITS (ground, 1 GW) ---")
    print(f"   solar land footprint (90% solar): {ground_solar_land_km2():.0f} km2 "
          f"(~{ground_solar_land_km2()/MANHATTAN_KM2:.1f}x Manhattan)")
    print(f"   lifetime cooling water: {datacenter_cooling_water_megatons():.1f} Mt")

    print("\n--- SENSITIVITY (space-mid vs ground no-gas) ---")
    print(f"{'Parameter':<28}{'Low':>22}{'Base':>16}{'High':>22}")
    print("-" * 88)
    for pname, lo_l, base_l, hi_l, lo_v, base_v, hi_v in sensitivity_table():
        print(f"{pname:<28}{lo_l+' -> '+str(round(lo_v)):>22}"
              f"{base_l+' -> '+str(round(base_v)):>16}{hi_l+' -> '+str(round(hi_v)):>22}")

    print("\n--- MONTE CARLO (40k draws; central=deterministic, [p5-p95] propagated) ---")
    mc = monte_carlo()
    sc_det = scenarios()
    for name, (p5, p50, p95) in mc.items():
        det = total(sc_det[name]) if name in sc_det else float('nan')
        print(f"   {name:<46} central {det:6.1f}   MC p50 {p50:5.1f}  [{p5:5.1f} - {p95:5.1f}]")

    print("\n--- AILI et al. (2025) HARMONISED onto this metric (physical, g/kWh) ---")
    ah = aili_harmonised()
    print(f"   IT(server) {ah['it']:.0f} + power/struct {ah['power_structure']:.0f} + "
          f"thermal {ah['thermal']:.0f} + launch {ah['launch']:.0f} = "
          f"{sum(ah.values()):.0f} g/kWh (4-yr server life)")
    cue = aili_full_cue()
    print(f"   reproduces their full life-cycle CUE {cue['total']:.0f} g/kWh "
          f"(physical {cue['physical_onetime']:.0f} + recurrent overhead "
          f"{cue['recurrent']:.0f}, the latter ~{100*cue['recurrent']/cue['total']:.0f}% "
          f"and common to ground)")
