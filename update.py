import re
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup

URL = 'https://sckolin.cz/matches/MUZ'
TZ = ZoneInfo('Europe/Prague')
MONTHS = {str(i): i for i in range(1,13)}

def escape(s):
    return str(s).replace('\\','\\\\').replace(';','\\;').replace(',','\\,').replace('\n','\\n')

def folded(line):
    # RFC 5545: fold at 75 octets, preserving UTF-8 codepoints
    chunks=[]; part=''
    for c in line:
        if len((part+c).encode('utf-8')) > 73:
            chunks.append(part); part=' '+c
        else: part+=c
    chunks.append(part)
    return '\r\n'.join(chunks)

def main():
    req = urllib.request.Request(URL, headers={'User-Agent':'Mozilla/5.0 (compatible; SC-Kolin-Calendar/1.0)'})
    with urllib.request.urlopen(req, timeout=35) as response:
        html = response.read().decode('utf-8', errors='replace')
    soup=BeautifulSoup(html,'html.parser')
    section=soup.find(string=re.compile(r'Všechny zápasy', re.I))
    if section is None:
        raise RuntimeError('Nenalezen seznam Všechny zápasy; kalendář se nepřepíše')
    # Read text after the heading, not the "nearest match" widget.
    heading=section.parent
    while heading and heading.name not in ('h1','h2','h3','h4'):
        heading=heading.parent
    if not heading: raise RuntimeError('Nenalezen nadpis seznamu')
    lines=[]
    for node in heading.next_elements:
        if getattr(node,'name',None) in ('h1','h2') and node is not heading:
            break
        if isinstance(node,str):
            value=' '.join(node.split())
            if value: lines.append(value)
    entries=[]
    date_re=re.compile(r'(\d+)\.\s*kolo,\s*(\d{1,2})\.\s*(\d{1,2})\.\s*(20\d{2})\s*-\s*(\d{1,2}):(\d{2})')
    for i, line in enumerate(lines):
        m=date_re.search(line)
        if not m: continue
        round_, day,month,year,hour,minute=map(int,m.groups())
        opponents=None
        for nextline in lines[i+1:i+7]:
            if ' - ' in nextline and 'Kolín' in nextline and not date_re.search(nextline):
                opponents=nextline; break
        if opponents is None: continue
        start=datetime(year,month,day,hour,minute,tzinfo=TZ)
        entries.append((round_,start,opponents))
    if len(entries)<20:
        raise RuntimeError(f'Nalezeno pouze {len(entries)} zápasů; bezpečnostní kontrola zabránila přepsání')
    now=datetime.now(TZ)
    out=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//SC Kolin Fan Calendar//CS','CALSCALE:GREGORIAN','METHOD:PUBLISH','X-WR-CALNAME:SC Kolín – A-tým','X-WR-TIMEZONE:Europe/Prague','REFRESH-INTERVAL;VALUE=DURATION:PT6H','X-PUBLISHED-TTL:PT6H']
    for round_,start,teams in entries:
        uid=f'sckolin-2026-27-round-{round_}@fan-calendar.local'
        # stable per round; changes to dates do not duplicate events
        end=start+timedelta(hours=2,minutes=30)
        out.extend(['BEGIN:VEVENT',f'UID:{uid}',f'DTSTAMP:{now.astimezone(ZoneInfo("UTC")):%Y%m%dT%H%M%SZ}',f'DTSTART;TZID=Europe/Prague:{start:%Y%m%dT%H%M%S}',f'DTEND;TZID=Europe/Prague:{end:%Y%m%dT%H%M%S}',f'SUMMARY:{escape(teams)}',f'DESCRIPTION:{escape("SC Retia Kolín – "+str(round_)+". kolo. Zdroj: "+URL)}',f'URL:{URL}','BEGIN:VALARM','ACTION:DISPLAY','DESCRIPTION:Za hodinu začíná zápas SC Kolín','TRIGGER:-PT1H','END:VALARM','END:VEVENT'])
    out.append('END:VCALENDAR')
    Path('kalendar.ics').write_bytes(('\r\n'.join(folded(s) for s in out)+'\r\n').encode('utf-8'))
    print(f'Vygenerováno {len(entries)} zápasů')

if __name__=='__main__': main()
