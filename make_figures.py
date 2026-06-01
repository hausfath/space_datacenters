"""
make_figures.py - Generate every figure in the analysis.

Each value is pulled from space_dc_lca.py (the single source of truth). Figures are
written as both vector PDF and 600-dpi PNG into figures/.

Run: python make_figures.py
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

import space_dc_lca as M

OUT = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 11, 'axes.titlesize': 12,
    'axes.labelsize': 11, 'xtick.labelsize': 10, 'ytick.labelsize': 10,
    'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 150,
})

# Okabe-Ito colourblind-safe palette
C = {
    'gas': '#D55E00', 'nuclear': '#E69F00', 'solar_storage': '#009E73',
    'launch': '#0072B2', 'launch_ch4': '#CC79A7', 'refresh_launch': '#56B4E9',
    'it': '#999999',
    'ground': '#009E73', 'space': '#0072B2', 'space2': '#56B4E9', 'space3': '#785EF0',
}


def save(fig, stem):
    for ext, dpi in (("pdf", None), ("png", 600)):
        path = os.path.join(OUT, f"{stem}.{ext}")
        fig.savefig(path, dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"wrote {stem}.pdf / .png")


# ---------------------------------------------------------------------------
# Scenario comparison (stacked bars + uncertainty whiskers)
# ---------------------------------------------------------------------------
def fig_comparison():
    sc = M.scenarios_with_ranges()
    order_keys = ['gas', 'nuclear', 'solar_storage', 'launch', 'launch_ch4',
                  'refresh_launch', 'it']
    labels = {
        'gas': 'Natural gas (combustion + upstream CH$_4$)',
        'nuclear': 'Nuclear (firm baseload, lifecycle)',
        'solar_storage': 'PV array + batteries (embodied)',
        'launch': 'Launch: combustion $\\times$ non-CO$_2$ forcing',
        'launch_ch4': 'Launch: propellant CH$_4$ leakage',
        'refresh_launch': 'GPU-refresh launch mass',
        'it': 'IT hardware (servers, GPUs; incl. refresh)',
    }
    rows = [
        ('Ground - 100% gas CCGT',                     'Ground: 100% gas (CCGT)'),
        ('Ground - 90% solar+storage / 10% gas',       'Ground: 90% solar + storage,\n10% gas backup'),
        ('Ground - no gas: solar overbuild + storage', 'Ground: solar overbuild + storage\n(near-term decarbonised)'),
        ('Ground - nuclear (firm baseload)',           'Ground: nuclear\n(longer-term decarbonised)'),
        ('Space - high (conv. radiators)',             'Space: high mass\n(conventional radiators)'),
        ('Space - mid',                                'Space: mid mass'),
        ('Space - low (Starcloud-target)',             'Space: low mass\n(Starcloud target)'),
    ]
    fig, ax = plt.subplots(figsize=(9.4, 6.4))

    # decarbonised-ground range: nuclear (longer-term) to solar+storage (near-term)
    g_nuc = M.total(sc['Ground - nuclear (firm baseload)'])
    g_sol = M.total(sc['Ground - no gas: solar overbuild + storage'])
    ax.axvspan(g_nuc, g_sol, color='#888888', alpha=0.10, zorder=0)
    ax.text((g_nuc + g_sol) / 2, len(rows) - 0.4,
            'decarbonised\nground range', ha='center', va='top', fontsize=8, color='#666')

    y = np.arange(len(rows))[::-1]
    for yi, (key, _) in zip(y, rows):
        comp = sc[key]; left = 0
        for k in order_keys:
            if comp.get(k, 0) > 0:
                ax.barh(yi, comp[k], left=left, color=C[k], edgecolor='white',
                        linewidth=0.6, height=0.62)
                left += comp[k]
        t = M.total(comp); rng = comp.get('_range')
        if rng:
            ax.errorbar(t, yi, xerr=[[t - rng[0]], [rng[1] - t]], fmt='none',
                        ecolor='#333', elinewidth=1.3, capsize=4, capthick=1.3, zorder=5)
            ax.text(rng[1] + 7, yi, f'{t:.0f}  ({rng[0]:.0f}–{rng[1]:.0f})',
                    va='center', fontsize=9.5, fontweight='bold')
        else:
            ax.text(t + 7, yi, f'{t:.0f}', va='center', fontsize=10, fontweight='bold')

    ax.set_yticks(y); ax.set_yticklabels([lbl for _, lbl in rows], fontsize=9.5, linespacing=1.25)
    ax.set_xlabel('Lifecycle GHG intensity (g CO$_2$e per kWh delivered)')
    ax.set_xlim(0, 780)
    ax.grid(axis='x', linestyle=':', alpha=0.5)
    handles = [Patch(facecolor=C[k], label=labels[k]) for k in order_keys]
    ax.legend(handles=handles, loc='lower right', frameon=False, fontsize=8.6)
    save(fig, "comparison")


# ---------------------------------------------------------------------------
# Launch-emission-intensity break-even
# ---------------------------------------------------------------------------
def fig_breakeven():
    f = np.linspace(15, 125, 200)
    tiers = [
        ('Space, low mass (Starcloud target)', M.MASS_LOW,  M.RADIATOR_KG_PER_KW_IT_LOW,  C['space3']),
        ('Space, mid mass',                    M.MASS_MID,  M.RADIATOR_KG_PER_KW_IT_MID,  C['space']),
        ('Space, high mass (conv. radiators)', M.MASS_HIGH, M.RADIATOR_KG_PER_KW_IT_HIGH, '#003f5c'),
    ]
    fig, ax = plt.subplots(figsize=(8.2, 5.4))

    # decarbonised-ground range: nuclear (longer-term) <-> solar+storage (near-term)
    g_sol = M.GROUND_NOGAS_TOTAL
    g_nuc = M.GROUND_NUCLEAR_TOTAL
    ax.axhspan(g_nuc, g_sol, color='#888888', alpha=0.12, zorder=0)
    ax.axhline(g_sol, color=C['ground'], lw=1.4, ls='--')
    ax.axhline(g_nuc, color='#9a6a00', lw=1.4, ls='--')
    ax.text(124, g_sol + 1.5, 'solar + storage (near-term ground)', color=C['ground'],
            ha='right', va='bottom', fontsize=8.6)
    ax.text(124, g_nuc + 1.5, 'nuclear (longer-term ground)', color='#9a6a00',
            ha='right', va='bottom', fontsize=8.6)
    ax.text(17.5, (g_nuc + g_sol) / 2, 'decarbonised\nground range', color='#666',
            ha='left', va='center', fontsize=8)

    for label, mass, rad, col in tiers:
        yv = [M.space_total_at_launch_factor(mass, rad, fi) for fi in f]
        ax.plot(f, yv, color=col, lw=2.2, label=label)
        be = M.breakeven_launch_factor(mass, rad, g_sol)
        if 15 <= be <= 125:
            ax.plot([be], [g_sol], 'o', color=col, ms=6, zorder=6)

    # reference launch-intensity markers
    for x, lab in [(M.LAUNCH_KGCO2_PER_KG * M.UPPER_ATM_MULT_LOW, 'optimistic\n($\\times$1.2)'),
                   (M.launch_factor(), 'central\n($\\times$1.5 + leak)'),
                   (M.LAUNCH_KGCO2_PER_KG * M.UPPER_ATM_MULT_HIGH
                    + M.propellant_leak_kgco2e_per_kg(M.CH4_LEAK_HIGH), 'pessimistic\n($\\times$3 + leak)')]:
        ax.axvline(x, color='#555', lw=0.9, ls=':')
        ax.text(x, 4, lab, rotation=0, fontsize=8, color='#555', ha='center', va='bottom')

    ax.set_xlabel('Effective launch GHG intensity (kg CO$_2$e per kg to LEO)')
    ax.set_ylabel('Space lifecycle GHG intensity (g CO$_2$e kWh$^{-1}$)')
    ax.set_xlim(15, 125); ax.set_ylim(0, 140)
    ax.grid(linestyle=':', alpha=0.45)
    ax.legend(loc='upper left', frameon=False, fontsize=9)
    ax.text(0.62, 0.96, 'Gas-fired ground = 590 g kWh$^{-1}$ (off scale)',
            transform=ax.transAxes, ha='center', va='top', fontsize=8.4, color=C['gas'])
    save(fig, "launch_breakeven")


# ---------------------------------------------------------------------------
# Comparison with published estimates
#   Ohs et al. (2025), "Dirty Bits in LEO": orbital 52.1 (Starship) / 66.3
#     (Falcon-9) at 5-yr with eclipse battery + re-entry; solar-array-only
#     (no battery) 6.3-7.5; their terrestrial baseline 34. Comparable basis
#     (g CO2e/kWh delivered).
#   Aili et al. (2025), Nature Electronics: report a life-cycle CUE (kgCO2e per
#     IT-kWh; absolute ~0.6-1.5, NOT directly comparable as it includes the
#     IT-manufacturing term that cancels in our differential comparison). Their
#     conclusion: orbital solar (I2=0) approaches an all-renewable-grid terrestrial
#     DC at 4-yr server life. The 20 marker below is that all-renewable terrestrial
#     GRID intensity (their ref. 88 benchmark), not an orbital absolute. (Their other
#     grid refs: 380 = medium-carbon = Google scope-2; Google life-cycle CUE 1050.)
# ---------------------------------------------------------------------------
def fig_literature():
    sc = M.scenarios_with_ranges()
    def tw(key):
        c = sc[key]
        return M.total(c), c.get('_range')
    tlo, rlo = tw('Space - low (Starcloud-target)')
    tmid, rmid = tw('Space - mid')
    thi, rhi = tw('Space - high (conv. radiators)')

    CW, CA, COH, COHL = C['space'], '#CC79A7', '#D55E00', '#E69F00'
    # (label, value, range or None, colour, filled marker, approx?)
    rows = [
        ('This work · low mass\n(10 yr, dawn–dusk, +non-CO$_2$+CH$_4$)', tlo, rlo, CW, True, False),
        ('This work · mid mass', tmid, rmid, CW, True, False),
        ('This work · high mass', thi, rhi, CW, True, False),
        ('Aili et al. 2025: orbital matches\nall-renewable terrestrial grid (CUE metric)', 20.0, None, CA, False, True),
        ('Ohs et al. 2025 · solar only\n(no eclipse battery)', 6.9, (6.3, 7.5), COHL, True, False),
        ('Ohs et al. 2025 · Starship\n(5 yr, +battery +re-entry)', 52.1, None, COH, True, False),
        ('Ohs et al. 2025 · Falcon-9', 66.3, None, COH, True, False),
    ]
    fig, ax = plt.subplots(figsize=(8.8, 5.6))
    y = np.arange(len(rows))[::-1]

    # decarbonised-ground range: nuclear (longer-term) -> solar+storage (near-term)
    g_nuc = M.GROUND_NUCLEAR_TOTAL
    g_sol = M.GROUND_NOGAS_TOTAL
    ax.axvspan(g_nuc, g_sol, color='#888888', alpha=0.12, zorder=0)
    ax.text((g_nuc + g_sol) / 2, max(y) + 1.55,
            'decarbonised ground (this work):\nnuclear ~%.0f $\\rightarrow$ solar+storage ~%.0f g kWh$^{-1}$'
            % (g_nuc, g_sol), ha='center', va='top', fontsize=7.8, color='#555')

    for yi, (lab, val, rng, col, filled, approx) in zip(y, rows):
        if rng:
            ax.plot([rng[0], rng[1]], [yi, yi], color=col, lw=2.2, zorder=3,
                    solid_capstyle='round')
        ax.plot([val], [yi], 'o', color=col, mfc=(col if filled else 'white'),
                mec=col, ms=9, mew=1.8, zorder=4)
        ax.text(val, yi + 0.27, ('~' if approx else '') + f'{val:.0f}',
                ha='center', va='bottom', fontsize=9, color=col, fontweight='bold')

    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=8.6, linespacing=1.2)
    ax.set_xlabel('Lifecycle GHG intensity (g CO$_2$e per kWh delivered)')
    ax.set_xlim(0, 120); ax.set_ylim(-0.7, max(y) + 1.85)
    ax.grid(axis='x', linestyle=':', alpha=0.45)
    ax.text(0.99, 0.03, 'Gas-fired ground = 590 g kWh$^{-1}$ (off scale)',
            transform=ax.transAxes, ha='right', va='bottom', fontsize=8.4, color=C['gas'])
    save(fig, "literature_comparison")


# ---------------------------------------------------------------------------
# Sensitivity tornado (mid-mass orbital total)
# ---------------------------------------------------------------------------
def fig_tornado():
    base = M.total(M.space_scenario(M.MASS_MID, radiator_kg_per_kw_it_=M.RADIATOR_KG_PER_KW_IT_MID))
    rows = []
    for pname, lo_l, base_l, hi_l, lo_v, base_v, hi_v in M.sensitivity_table():
        if 'Ground PV' in pname:   # ground parameter; shown as reference line instead
            continue
        rows.append((pname, lo_l, hi_l, lo_v, hi_v))
    rows.sort(key=lambda r: abs(r[4] - r[3]))   # ascending span -> widest on top

    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    y = np.arange(len(rows))
    for yi, (pname, lo_l, hi_l, lo_v, hi_v) in zip(y, rows):
        left, right = min(lo_v, hi_v), max(lo_v, hi_v)
        ax.barh(yi, right - left, left=left, height=0.6,
                color=C['space'], alpha=0.85, edgecolor='white')
        ax.text(left - 1.2, yi, f'{lo_l}', va='center', ha='right', fontsize=8.5, color='#333')
        ax.text(right + 1.2, yi, f'{hi_l}', va='center', ha='left', fontsize=8.5, color='#333')
        ax.text(left + 0.5, yi, f'{lo_v:.0f}', va='center', ha='left', fontsize=8, color='white')
        ax.text(right - 0.5, yi, f'{hi_v:.0f}', va='center', ha='right', fontsize=8, color='white')

    ax.axvline(base, color='#333', lw=1.4)
    ax.text(base, len(rows) - 0.3, f'space mid base = {base:.0f}', ha='center',
            va='bottom', fontsize=9, fontweight='bold')

    gcen = M.GROUND_NOGAS_TOTAL
    ax.axvline(gcen, color=C['ground'], lw=1.4, ls='--')
    ax.text(gcen, -0.85, f'solar+storage ground = {gcen:.0f}', ha='center', va='top',
            fontsize=9, color=C['ground'])

    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=9.5)
    ax.set_xlabel('Space lifecycle GHG intensity (g CO$_2$e kWh$^{-1}$)')
    ax.set_xlim(20, 100); ax.set_ylim(-1.3, len(rows) - 0.0)
    ax.grid(axis='x', linestyle=':', alpha=0.45)
    save(fig, "sensitivity_tornado")


# ---------------------------------------------------------------------------
# Radiator mass from radiative physics
# ---------------------------------------------------------------------------
def fig_radiator():
    T = np.linspace(280, 520, 200)
    fig, (a, b) = plt.subplots(1, 2, figsize=(10.2, 4.3))

    for rho, col, lab in [(8.0, '#003f5c', '8 kg m$^{-2}$ (ISS-heritage)'),
                          (4.0, C['space'], '4 kg m$^{-2}$ (deployable panel)'),
                          (2.0, C['space2'], '2 kg m$^{-2}$ (advanced)')]:
        m = [M.radiator_kg_per_kw_it(t, rho) for t in T]
        a.plot(T, m, color=col, lw=2, label=lab)
    for kw, col, name in [(M.RAD_HIGH, '#003f5c', 'conventional'),
                          (M.RAD_MID, C['space'], 'near-term'),
                          (M.RAD_LOW, C['space2'], 'advanced')]:
        a.plot([kw['t_rad_k']], [M.radiator_kg_per_kw_it(**kw)], 'o', color=col, ms=7, zorder=5)
    a.axvspan(300, 350, color='#D55E00', alpha=0.10)
    a.text(325, a.get_ylim()[1] * 0.92 if False else 11.5, 'GPU-compatible\n(300–350 K)',
           ha='center', fontsize=8.5, color='#D55E00')
    a.set_xlabel('Radiator rejection temperature (K)')
    a.set_ylabel('Radiator specific mass (kg per kW$_{IT}$)')
    a.set_xlim(280, 520); a.set_ylim(0, 13)
    a.grid(linestyle=':', alpha=0.45); a.legend(frameon=False, fontsize=8.6, loc='upper right')
    a.set_title('(a) Specific mass vs. temperature (Stefan–Boltzmann)', fontsize=10.5)

    Th = np.linspace(330, 520, 200)
    w = [M.heat_pump_power_fraction(330, t) * 100 for t in Th]
    b.plot(Th, w, color=C['gas'], lw=2.2)
    b.axhline(100, color='#888', lw=0.9, ls=':')
    b.text(335, 103, 'equals full IT power', fontsize=8.5, color='#555')
    b.set_xlabel('Heat-pump target temperature (K)')
    b.set_ylabel('Added power (% of IT load)')
    b.set_xlim(330, 520); b.set_ylim(0, 130)
    b.grid(linestyle=':', alpha=0.45)
    b.set_title('(b) Heat-pump penalty to raise rejection T from 330 K', fontsize=10.5)
    save(fig, "radiator_mass")


# ---------------------------------------------------------------------------
# Orbit dependence (dawn-dusk SSO vs generic LEO)
# ---------------------------------------------------------------------------
def fig_orbit():
    tiers = [('low', M.MASS_LOW, M.RADIATOR_KG_PER_KW_IT_LOW),
             ('mid', M.MASS_MID, M.RADIATOR_KG_PER_KW_IT_MID),
             ('high', M.MASS_HIGH, M.RADIATOR_KG_PER_KW_IT_HIGH)]
    sso = [M.total(M.space_scenario(m, radiator_kg_per_kw_it_=r)) for _, m, r in tiers]
    leo = [M.total(M.generic_leo_scenario(m, radiator_kg_per_kw_it_=r)) for _, m, r in tiers]
    x = np.arange(len(tiers)); w = 0.36
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    ax.bar(x - w/2, sso, w, color=C['space'], label='Dawn–dusk SSO (~5% eclipse)')
    ax.bar(x + w/2, leo, w, color=C['space3'], label='Generic LEO (~39% eclipse)')
    for xi, v in zip(x - w/2, sso):
        ax.text(xi, v + 1, f'{v:.0f}', ha='center', fontsize=9)
    for xi, v in zip(x + w/2, leo):
        ax.text(xi, v + 1, f'{v:.0f}', ha='center', fontsize=9)
    gcen = M.GROUND_NOGAS_TOTAL
    ax.axhline(gcen, color=C['ground'], lw=1.3, ls='--')
    ax.text(2.4, gcen + 1, 'solar + storage ground', color=C['ground'], ha='right', fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels([f'{t[0]}\nmass' for t in tiers])
    ax.set_ylabel('Lifecycle GHG intensity (g CO$_2$e kWh$^{-1}$)')
    ax.set_ylim(0, max(leo) + 15)
    ax.grid(axis='y', linestyle=':', alpha=0.45)
    ax.legend(frameon=False, fontsize=9, loc='upper left')
    save(fig, "orbit_eclipse")


# ---------------------------------------------------------------------------
# Methane-leakage sensitivity (gas and rocket propellant)
# ---------------------------------------------------------------------------
def fig_methane():
    leak = np.linspace(0.0, 0.04, 200)
    gas = [M.gas_intensity(l) for l in leak]
    spc = [M.total(M.space_scenario(M.MASS_MID, radiator_kg_per_kw_it_=M.RADIATOR_KG_PER_KW_IT_MID, leak=l))
           for l in leak]
    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    ax.plot(leak * 100, gas, color=C['gas'], lw=2.2, label='Ground: gas CCGT (left axis)')
    ax.set_xlabel('Upstream methane leakage rate (% of throughput)')
    ax.set_ylabel('Gas CCGT intensity (g CO$_2$e kWh$^{-1}$)', color=C['gas'])
    ax.tick_params(axis='y', labelcolor=C['gas'])
    ax.set_ylim(380, 580); ax.set_xlim(0, 4)
    ax.axvline(M.CH4_LEAK_CENTRAL * 100, color='#555', lw=0.9, ls=':')
    ax.text(M.CH4_LEAK_CENTRAL * 100 + 0.05, 565, 'Alvarez et al.\n(2.3%)', fontsize=8.3, color='#555')

    ax2 = ax.twinx()
    ax2.spines['top'].set_visible(False)
    ax2.plot(leak * 100, spc, color=C['space'], lw=2.2, label='Space: mid mass (right axis)')
    ax2.set_ylabel('Space lifecycle intensity (g CO$_2$e kWh$^{-1}$)', color=C['space'])
    ax2.tick_params(axis='y', labelcolor=C['space'])
    ax2.set_ylim(30, 45)

    lines = ax.get_lines()[:1] + ax2.get_lines()[:1]
    ax.legend(lines, [l.get_label() for l in lines], frameon=False, fontsize=9, loc='upper left')
    save(fig, "methane_leakage")


# ---------------------------------------------------------------------------
# Non-GHG co-benefits (land, water)
# ---------------------------------------------------------------------------
def fig_cobenefits():
    fig, (a, b) = plt.subplots(1, 2, figsize=(9.4, 4.0))
    land = M.ground_solar_land_km2()
    a.bar(['Gas-fired\nground', 'Solar-powered\nground', 'Space\n(solar)'],
          [0.2, land, 0.0], color=[C['gas'], C['solar_storage'], C['space']])
    a.axhline(M.MANHATTAN_KM2, color='#333', lw=1.2, ls='--')
    a.text(2.4, M.MANHATTAN_KM2 + 3, 'Manhattan (59 km$^2$)', ha='right', fontsize=8.6)
    a.set_ylabel('Solar-array land footprint (km$^2$)')
    a.set_title('(a) Land for a 1 GW datacentre', fontsize=10.5)
    a.text(1, land + 4, f'{land:.0f} km$^2$', ha='center', fontsize=9, fontweight='bold')
    a.grid(axis='y', linestyle=':', alpha=0.45)

    water = M.datacenter_cooling_water_megatons()
    a_yr = water / M.LIFE_YR
    b.bar(['Evaporatively\ncooled ground', 'Space\n(radiative)'],
          [a_yr, 0.0], color=[C['launch'], C['space']])
    b.set_ylabel('Cooling water (Mt yr$^{-1}$)')
    b.set_title('(b) Cooling water for a 1 GW datacentre', fontsize=10.5)
    b.text(0, a_yr + 0.05, f'{a_yr:.1f} Mt yr$^{{-1}}$', ha='center', fontsize=9, fontweight='bold')
    b.grid(axis='y', linestyle=':', alpha=0.45)
    save(fig, "land_water")


if __name__ == "__main__":
    fig_comparison()
    fig_breakeven()
    fig_literature()
    fig_radiator()
    fig_orbit()
    fig_methane()
    fig_cobenefits()
    fig_tornado()
    print("\nAll figures written to", OUT)
