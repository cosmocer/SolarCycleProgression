#!/usr/bin/env python3
"""Build static JSON used by index.html.
Run occasionally (for example monthly) before publishing to GitHub Pages.
Dependencies: requests
"""
from __future__ import annotations
import concurrent.futures as cf
import datetime as dt
import json, re, time
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

def fetch_events(d):
    u=f'https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/{d:%Y/%m}/{d:%Y%m%d}events.txt'
    try:return d,get(u,12).text
    except:return d,''

def build_flares(start=dt.date(1996,1,1)):
    days=list(daterange(start,dt.date.today())); annual={}
    print('flares: downloading',len(days),'daily event files (one-time build; can take a while)')
    with cf.ThreadPoolExecutor(max_workers=16) as ex:
        for n,(d,txt) in enumerate(ex.map(fetch_events,days),1):
            if txt:
                y=d.year; annual.setdefault(y,{'year':y,'C':0,'M':0,'X':0})
                # Count XRA event rows and extract GOES class from Particulars.
                # Event files have fixed-width/space-separated rows; only rows containing XRA are used.
                for line in txt.splitlines():
                    if ' XRA ' not in f' {line} ': continue
                    m=re.search(r'\b([CMX])\s*([0-9]+(?:\.[0-9]+)?)\b',line)
                    if m: annual[y][m.group(1)]+=1
            if n%1000==0: print(' ',n,'/',len(days))
    data=[annual.get(y,{'year':y,'C':0,'M':0,'X':0}) for y in range(start.year,dt.date.today().year+1)]
    (OUT/'flares.json').write_text(json.dumps(data,separators=(',',':')))
    print('flares:',len(data),'years')

if __name__=='__main__':
    build_spotless(); build_storms(); build_butterfly(); build_flares()
    print('\nDone. Serve this folder with: python -m http.server 8000')
