#!/usr/bin/env python3
"""Build static JSON used by index.html.
Run occasionally (for example monthly) before publishing to GitHub Pages.
Dependencies: requests
"""
from __future__ import annotations
import concurrent.futures as cf
import datetime as dt
import argparse, csv, io, json, re
from pathlib import Path
import requests

OUT=Path(__file__).with_name('data'); OUT.mkdir(exist_ok=True)
S=requests.Session(); S.headers.update({'User-Agent':'SolarCycleClassroom/1.0 (educational use)'})

def get(url, timeout=25):
    r=S.get(url,timeout=timeout); r.raise_for_status(); return r

def build_spotless(start=1997):
    url='https://www.sidc.be/SILSO/DATA/SN_d_tot_V2.0.csv'
    counts={}
    for line in get(url).text.splitlines():
        p=[x.strip() for x in line.split(';')]
        if len(p)<5: continue
        try: y=int(p[0]); sn=float(p[4])
        except: continue
        if y>=start and sn==0: counts[y]=counts.get(y,0)+1
    now=dt.date.today().year
    data=[{'year':y,'count':counts.get(y,0)} for y in range(start,now+1)]
    (OUT/'spotless.json').write_text(json.dumps(data,separators=(',',':')))
    print('spotless:',len(data),'years')

def build_storms(start=1997):
    end=dt.date.today().isoformat()
    url=f'https://kp.gfz.de/app/json/?start={start}-01-01T00:00:00Z&end={end}T23:59:59Z&index=Kp'
    j=get(url,60).json(); times=j.get('datetime') or j.get('time'); vals=j.get('Kp') or j.get('kp')
    daily={}
    for t,v in zip(times,vals):
        day=str(t)[:10]; daily[day]=max(daily.get(day,-99),float(v))
    annual={}
    def cls(k):
        return 'G5' if k>=9 else 'G4' if k>=8 else 'G3' if k>=7 else 'G2' if k>=6 else 'G1' if k>=5 else None
    for day,k in daily.items():
        c=cls(k)
        if not c: continue
        y=int(day[:4]); annual.setdefault(y,{'year':y,'G1':0,'G2':0,'G3':0,'G4':0,'G5':0})[c]+=1
    data=[annual.get(y,{'year':y,'G1':0,'G2':0,'G3':0,'G4':0,'G5':0}) for y in range(start,dt.date.today().year+1)]
    (OUT/'storms.json').write_text(json.dumps(data,separators=(',',':')))
    print('storms:',len(data),'years')

def daterange(a,b):
    d=a
    while d<=b:
        yield d; d+=dt.timedelta(days=1)

def fetch_srs(d):
    u=f'https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_region_summaries/{d:%Y/%m}/{d:%Y%m%d}SRS.txt'
    try:return d,get(u,12).text
    except:return d,''

def build_butterfly(start=dt.date(2004,1,1)):
    # One point per reported region per daily SRS. Area is parsed where possible.
    days=list(daterange(start,dt.date.today())); out=[]
    print('butterfly: downloading',len(days),'daily SRS files (one-time build; can take a while)')
    with cf.ThreadPoolExecutor(max_workers=16) as ex:
        for n,(d,txt) in enumerate(ex.map(fetch_srs,days),1):
            if not txt: continue
            for line in txt.splitlines():
                # Typical Part I lines begin: region  location  Lo  area ... e.g. 4532 N15W20 ...
                m=re.match(r'^\s*(\d{3,5})\s+([NS])(\d{2})[EW]\d{2,3}\s+\d+\s+(\d+)',line)
                if not m: continue
                lat=float(m.group(3))*(1 if m.group(2)=='N' else -1); area=float(m.group(4))
                out.append({'date':d.isoformat(),'latitude':lat,'area':area,'region':m.group(1)})
            if n%500==0: print(' ',n,'/',len(days))
    (OUT/'butterfly.json').write_text(json.dumps(out,separators=(',',':')))
    print('butterfly:',len(out),'region-day points')

FLARE_REPORT='https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/multi/l2/data/xrsf-l2-flrpt_science/csv/'

def build_flares():
    """Use one science-quality event list for both annual counts and peak fluxes."""
    listing=get(FLARE_REPORT).text
    names=re.findall(r'sci_xrsf-l2-flrpt_geo_s\d+_e\d+_v[\d-]+\.csv',listing)
    if not names: raise RuntimeError('NOAA GOES XRS flare report not found')
    filename=max(names)
    print('flares: downloading',filename)
    report=get(FLARE_REPORT+filename,120).text
    peaks=[]
    annual={year:{'year':year,'C':0,'M':0,'X':0} for year in range(1996,2027)}
    reader=csv.DictReader(io.StringIO(report))
    if not {'time','flare_class','xrsb_irrad'}<=set(reader.fieldnames or []):
        raise ValueError('NOAA GOES flare report is missing required columns')
    for row in reader:
        date=row['time'].strip()
        if len(date)<16 or not date[:4].isdigit(): continue
        year=int(date[:4]); flare_class=row['flare_class'].strip()
        if year not in annual or not re.match(r'^[CMX]\d',flare_class): continue
        try: peak=float(row['xrsb_irrad'])
        except (TypeError,ValueError): continue
        if not 0<peak<0.1: continue
        peaks.append({'date':date.replace(' ','T'),'class':flare_class,'peak':peak})
        annual[year][flare_class[0]]+=1
    if len(peaks)<1000: raise ValueError('GOES flare report yielded too few events')
    old_file=OUT/'flares.json'
    if old_file.exists():
        old={row['year']:row for row in json.loads(old_file.read_text())}
        different=[year for year,counts in annual.items() if year in old and any(counts[c]!=old[year].get(c,0) for c in 'CMX')]
        print('flares: annual counts differ from old SWPC XRA-row counts in',len(different),'years')
    (OUT/'flare_peaks.json').write_text(json.dumps(peaks,separators=(',',':')))
    (OUT/'flares.json').write_text(json.dumps(list(annual.values()),separators=(',',':')))
    print('flares:',len(peaks),'C/M/X peaks, 1996–2026')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--flares-only',action='store_true',help='rebuild the GOES flare counts and peak-flux data only')
    args=parser.parse_args()
    if not args.flares_only:
        build_spotless(); build_storms(); build_butterfly()
    build_flares()
    print('\nDone. Serve this folder with: python -m http.server 8000')
