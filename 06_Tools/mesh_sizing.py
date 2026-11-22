"""Pick FDS mesh counts so that R* = dl*/D* falls inside the Table 1 bands.

Domain 6.6 x 1.3 x 0.76 m, D* = 0.3911 m (106.2 kW).
Bands: coarse/medium 1/10 < R* < 1/5, fine 1/15 < R* < 1/10.
"""
import math

LX, LY, LZ = 6.6, 1.3, 0.76
DSTAR = 0.3911          # 106.2 kW
DSTAR47 = 0.2827        # 47.2 kW, for cross-check

# target R* for each level (aim mid-band or near the coarse edge)
TARGETS = [("Coarse", 1 / 5.2), ("Medium", 1 / 7.5), ("Fine", 1 / 12.0)]
BANDS = {"Coarse": (1 / 10, 1 / 5), "Medium": (1 / 10, 1 / 5), "Fine": (1 / 15, 1 / 10)}


def cells(length, target_dl):
    n = max(1, round(length / target_dl))
    return n, length / n


print(f"{'level':8} {'Nx x Ny x Nz':16} {'dx':>7} {'dy':>7} {'dz':>7} "
      f"{'dl*':>7} {'R*(106kW)':>10} {'R*(47kW)':>9} {'cells':>8}")
for name, r in TARGETS:
    dl = DSTAR * r
    nx, dx = cells(LX, dl)
    ny, dy = cells(LY, dl)
    nz, dz = cells(LZ, dl)
    dl_avg = (dx + dy + dz) / 3
    r106 = dl_avg / DSTAR
    r47 = dl_avg / DSTAR47
    lo, hi = BANDS[name]
    ok = "OK" if lo < r106 < hi else "FAIL"
    print(f"{name:8} {nx:>3}x{ny:>3}x{nz:>3}   {dx:7.5f} {dy:7.5f} {dz:7.5f} "
          f"{dl_avg:7.5f} {r106:10.4f} {r47:9.4f} {nx*ny*nz:8d}  {ok}  "
          f"(1/{1/r106:.1f})")

# also: what does exact R* = 1/5, 1/7, 1/12 require?
print("\nexact targets:")
for name, r in [("1/5", 1 / 5), ("1/7.5", 1 / 7.5), ("1/12", 1 / 12)]:
    dl = DSTAR * r
    print(f"  R*={name}: dl*={dl:.4f} m -> Nx={LX/dl:.1f}, Ny={LY/dl:.1f}, Nz={LZ/dl:.1f}")
