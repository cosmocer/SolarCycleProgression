# Solar Cycle Classroom Explorer

A small static Plotly page designed for projection in class. It contains:

1. International Sunspot Number progression (monthly + 13-month smoothed)
2. Spotless days per year
3. Butterfly diagram
4. F10.7 solar radio flux
5. C/M/X solar flares per year
6. Geomagnetic storm days per year, with G1–G5 selectors and a stacked-all view

## Quick preview

From this folder:

```bash
python -m http.server 8000
```

Open `http://localhost:8000`.

The sunspot and F10.7 plots load directly from NOAA/SWPC. Spotless days and Kp statistics try their official web services first and fall back to local JSON.

For the butterfly and flare-count plots, build the static historical JSON once:

```bash
pip install requests
python build_data.py
```

The first full build downloads many small NOAA/NCEI daily archive files and can therefore take a while. Subsequent use of the web page is static and fast. You can run the builder periodically (for example monthly) and commit the updated `data/*.json` files to GitHub.

## Data sources

- Sunspot progression and F10.7: NOAA/SWPC ISES solar-cycle JSON service
- Spotless days: WDC-SILSO daily total sunspot number
- Butterfly diagram: NOAA/NCEI Solar Region Summary archive
- Solar flare counts: NOAA/NCEI SWPC Solar Event Reports
- Geomagnetic storms: GFZ Potsdam Kp web service

Storm-day classification uses the strongest 3-hour Kp value in each UTC day: G1 = 5≤Kp<6, G2 = 6≤Kp<7, G3 = 7≤Kp<8, G4 = 8≤Kp<9, G5 = Kp≥9. This makes the stacked bars mutually exclusive: each storm day is counted once, at its strongest level.
