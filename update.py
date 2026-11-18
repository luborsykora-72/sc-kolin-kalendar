import re
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup

URL = 'https://sckolin.cz/matches/MUZ'
TZ = ZoneInfo('Europe/Prague')
DATE_RE = re.compile(r'(?P<round>\d+)\.\s*kolo\s*,\s*(?P<day>\d{1,2})\.\s*(?P<month>\d{1,2})\.\s*(?P<year>20\d{2})\s*[-–]\s*(?P<hour>\d{1,2}):(?P<minute>\d{2})', re.I)
TEAM_RE = re.compile(r'Kolín\s*-|\s*-\s*Kolín\b', re.I)

def escape(value):
    return str(value).replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')

def fold(line):
    result, current = [], ''
    for ch in line:
        if len((current + ch).encode('utf-8')) > 75:
            result.append(current)
            current = ' ' + ch
        else:
            current += ch
    result.append(current)
    return '\r\n'.join(result)

def main():
    request = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0 SC-Kolin-Calendar/1.0'})
    with urllib.request.urlopen(request, timeout=40) as response:
        html = response.read().decode('utf-8', errors='replace')
    soup = BeautifulSoup(html, 'html.parser')
    for element in soup(['script', 'style', 'noscript']):
        element.decompose()
    # The club's page contains a heading "Všechny zápasy" followed by date
    # labels (e.g. "24. kolo, 18. 11. 2026 - 18:00") and team headings.
    # Extracting stripped text also works if the HTML wrapper changes.
    lines = [' '.join(s.split()) for s in soup.stripped_strings]
    matches = {}
    for i, line in enumerate(lines):
        m = DATE_RE.search(line)
        if not m:
            continue
        teams = next((candidate for candidate in lines[i+1:i+12]
                      if TEAM_RE.search(candidate) and not DATE_RE.search(candidate)
                      and len(candidate) < 120), None)
        if not teams:
            continue
        parts = {k: int(v) for k, v in m.groupdict().items()}
        start = datetime(parts['year'], parts['month'], parts['day'],
                         parts['hour'], parts['minute'], tzinfo=TZ)
        # Stable ID per round and season, so time changes update the event.
        season = parts['year'] if parts['month'] >= 7 else parts['year'] - 1
        key = (season, parts['round'])
        matches[key] = (start, teams)
    print(f'DIAGNOSTIKA: HTML znaku={len(html)}, textovych radku={len(lines)}, zapasu={len(matches)}', flush=True)
    print('DIAGNOSTIKA: Prvnich 30 textovych radku:', repr(lines[:30]), flush=True)
    if len(matches) < 20:
        raise RuntimeError(f'Nalezeno jen {len(matches)} zapasu; kalendar nebude prepsan.')
    now = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//SC Kolin Fan Calendar//CS',
              'CALSCALE:GREGORIAN', 'METHOD:PUBLISH', 'X-WR-CALNAME:SC Kolín – A-tým',
              'X-WR-TIMEZONE:Europe/Prague']
    for (season, round_number), (start, teams) in sorted(matches.items(), key=lambda item: item[1][0]):
        end = start + timedelta(hours=2, minutes=30)
        output.extend(['BEGIN:VEVENT', f'UID:sckolin-{season}-{round_number}@fan-calendar.local',
                       f'DTSTAMP:{now}',
                       f'DTSTART:{start.astimezone(timezone.utc):%Y%m%dT%H%M%SZ}',
                       f'DTEND:{end.astimezone(timezone.utc):%Y%m%dT%H%M%SZ}',
                       f'SUMMARY:{escape(teams)}',
                       f'DESCRIPTION:{escape(str(round_number) + ". kolo – zdroj: " + URL)}',
                       f'URL:{URL}',
                       'BEGIN:VALARM', 'TRIGGER:-PT1H', 'ACTION:DISPLAY',
                       'DESCRIPTION:Za hodinu začíná zápas SC Kolín', 'END:VALARM',
                       'END:VEVENT'])
    output.append('END:VCALENDAR')
    Path('kalendar.ics').write_bytes(('\r\n'.join(fold(line) for line in output) + '\r\n').encode('utf-8'))
    print(f'Vygenerovano {len(matches)} zapasu.', flush=True)

if __name__ == '__main__':
    main()
