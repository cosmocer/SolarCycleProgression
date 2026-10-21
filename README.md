# Solar Cycle Classroom Explorer

A small static Plotly page designed for projection in class. It contains:

1. International Sunspot Number progression (monthly + 13-month smoothed)
2. Spotless days per year
3. Butterfly diagram
4. F10.7 solar radio flux
5. C/M/X solar flares per year
6. Individual GOES flare peak X-ray fluxes (1996–2026, logarithmic scale)
7. Geomagnetic storm days per year, with G1–G5 selectors and a stacked-all view

## Quick preview

From this folder:

```bash
python -m http.server 8000
```

Open `http://localhost:8000`.

Use the handle at the top of a panel to drag it into a new position. The arrow buttons also move panels one place at a time. Choose **Half width** on two panels and place them next to each other for side-by-side comparison. The layout is saved in the browser; **Reset panel layout** restores the original order and full-width panels. On narrow screens, panels display in one column.

The sunspot plot loads directly from NOAA/SWPC. The F10.7 plot combines the local monthly archive for January 1995–September 2004 with live NOAA/SWPC values; NOAA/SWPC takes precedence in overlapping months. Spotless days and Kp statistics try their official web services first and fall back to local JSON.

For the butterfly and flare plots, build the static historical JSON once:

```bash
pip install requests
python build_data.py
```

The first full build downloads many small NOAA/NCEI daily archive files and can therefore take a while. Subsequent use of the web page is static and fast. You can run the builder periodically (for example monthly) and commit the updated `data/*.json` files to GitHub.

To update only the GOES flare data, run `python build_data.py --flares-only`. This downloads NOAA's composite flare report and writes both `data/flare_peaks.json` and `data/flares.json` from the same event records. If the local peak file is absent, the page attempts to load the composite report directly from NOAA; direct loading depends on the archive allowing browser requests. The local files are the reliable option for GitHub Pages.

## GitHub Pages

Commit `index.html`, `build_data.py`, and the `data` folder to a repository. After running `build_data.py`, enable GitHub Pages for the repository. The page itself needs no Python server in production.

## Data sources

- Sunspot progression and F10.7 since September 2004: NOAA/SWPC ISES solar-cycle JSON service
- F10.7, January 1995–September 2004: [NOAA/PSL monthly solar flux](https://psl.noaa.gov/data/correlation/solar.data), divided by 10 to convert its tenths of an sfu to sfu. The local copy is `data/f107_1995_2004.json`. Missing smoothed values are calculated with a centered 13-month mean, with the first and last months weighted by half; six months of observations on either side are required.
- Spotless days: WDC-SILSO daily total sunspot number
- Butterfly diagram: NOAA/NCEI Solar Region Summary archive
- Solar flare counts and individual peak fluxes: [NOAA/NCEI GOES XRS science-quality flare report](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/multi/l2/data/xrsf-l2-flrpt_science/csv/). The 0.1–0.8 nm peak irradiance is in W/m². The graph shows C-, M- and X-class events from 1996 through 2026; its time axis begins in 1995. The current checked-in `data/flares.json` is from the older SWPC Solar Event Reports and will be replaced by the builder.
- Geomagnetic storms: GFZ Potsdam Kp web service

Storm-day classification uses the strongest 3-hour Kp value in each UTC day: G1 = 5≤Kp<6, G2 = 6≤Kp<7, G3 = 7≤Kp<8, G4 = 8≤Kp<9, G5 = Kp≥9. This makes the stacked bars mutually exclusive: each storm day is counted once, at its strongest level.

The old annual flare counts counted `XRA` rows in SWPC daily event reports. The composite GOES XRS report uses one science-quality record per detected flare, merges observations from multiple satellites, and recalibrates pre-GOES-16 magnitudes. Its event definitions and class counts can differ from the old extract. Once the composite data load, both flare graphs use that same event list. A few large historical peaks were saturated and their reported peak irradiances may be lower limits. See the [GOES Flare Report ReadMe](https://archive.data.noaa.gov/satellite-spaceweather/GOES1-15/docs/goes_science_quality_data/GOES_Flare_Report_ReadMe.pdf) for matching rules and caveats.
