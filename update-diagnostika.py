"""SC Kolín fan calendar: scrape official A-team fixtures and publish ICS."""
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

URL = 'https://sckolin.cz/matches/MUZ'
TZ = ZoneInfo('Europe/Prague')
ROUND = re.compile(r'(?P<round>\d+)\.\s*kolo\s*,\s*(?P<day>\d{1,2})\.\s*(?P<month>\d{1,2})\.\s*(?P<year>20\d{2})\s*[-–]\s*(?P<hour>\d{1,2}):(?P<minute>\d{2})', re.I)
TEAM = re.compile(r'Kolín', re.I)


def clean(value):
    return ' '.join(value.split())


def ical_escape(value):
    return str(value).replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')


def fold(line):
    """Fold ICS content lines at max 75 UTF-8 octets."""
    out = []
    part = ''
    for char in line:
        if len((part + char).encode('utf-8')) > 75:
            out.append(part)
            part = ' ' + char
        else:
            part += char
    out.append(part)
    return '\r\n'.join(out)


def parse(html):
    soup = BeautifulSoup(html, 'html.parser')
    for element in soup(['script', 'style', 'noscript']):
        element.decompose()
    # Restrict to the full match list when possible, to avoid the nearest-match duplicate.
    heading = soup.find(string=lambda s: s and clean(s).lower() == 'všechny zápasy')
    if heading:
        parent = heading.parent
        while parent and parent.name not in ('h1', 'h2', 'h3', 'h4'):
            parent = parent.parent
        if parent:
            text = []
            for node in parent.next_elements:
                if getattr(node, 'name', None) in ('h1', 'h2', 'h3') and node is not parent:
                    if clean(node.get_text(' ', strip=True)).lower() == 'partneři kolínského hokeje':
                        break
                if isinstance(node, str):
                    val = clean(node)
                    if val:
                        text.append(val)
            lines = text
        else:
            lines = [clean(s) for s in soup.stripped_strings]
    else:
        lines = [clean(s) for s in soup.stripped_strings]

    matches = {}
    for i, line in enumerate(lines):
        m = ROUND.search(line)
        if not m:
            continue
        # Team fixture must follow the round/date line, not a score or navigation label.
        team_line = None
        for candidate in lines[i + 1:i + 12]:
            if ROUND.search(candidate):
                break
            if TEAM.search(candidate) and ' - ' in candidate and len(candidate) < 140:
                team_line = candidate
                break
        if not team_line:
            continue
        gd = {k: int(v) for k, v in m.groupdict().items()}
        start = datetime(gd['year'], gd['month'], gd['day'], gd['hour'], gd['minute'], tzinfo=TZ)
        key = (gd['year'], gd['round'])
        matches[key] = (gd['round'], start, team_line)
    return sorted(matches.values(), key=lambda x: x[1])


def build_ics(matches):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    rows = [
        'BEGIN:VCALENDAR', 'VERSION:2.0',
        'PRODID:-//SC Kolin Fan Calendar//CS',
        'CALSCALE:GREGORIAN', 'METHOD:PUBLISH',
        'X-WR-CALNAME:SC Kolín – A-tým',
        'X-WR-TIMEZONE:Europe/Prague',
        'REFRESH-INTERVAL;VALUE=DURATION:PT6H',
    ]
    for round_no, start, teams in matches:
        end = start + timedelta(hours=2, minutes=30)
        home = teams.startswith('Kolín - ')
        rows.extend([
            'BEGIN:VEVENT',
            f'UID:sckolin-{start.year}-round-{round_no}@fan-calendar.local',
            f'DTSTAMP:{stamp}',
            f'DTSTART:{start.strftime("%Y%m%dT%H%M%S")}',
            f'DTEND:{end.strftime("%Y%m%dT%H%M%S")}',
            f'SUMMARY:{ical_escape(teams)}',
            f'DESCRIPTION:{ical_escape(f"SC Kolín, {round_no}. kolo. Zdroj: {URL}")}',
            f'LOCATION:{ical_escape("Zimní stadion Kolín" if home else "Venkovní utkání – ověř místo u pořadatele")}',
            'BEGIN:VALARM', 'TRIGGER:-PT1H', 'ACTION:DISPLAY',
            f'DESCRIPTION:{ical_escape(teams)}', 'END:VALARM',
            'END:VEVENT',
        ])
    rows.append('END:VCALENDAR')
    return ('\r\n'.join(fold(row) for row in rows) + '\r\n').encode('utf-8')


def main():
    req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0 (compatible; SC-Kolin-Calendar/1.1)'})
    with urllib.request.urlopen(req, timeout=35) as response:
        html = response.read().decode('utf-8', errors='replace')
    # Diagnostics: show what GitHub actually received (no credentials involved).
    soup = BeautifulSoup(html, 'html.parser')
    visible = [clean(x) for x in soup.stripped_strings if clean(x)]
    print(f'DIAGNOSTIKA: HTTP HTML bytes={len(html.encode("utf-8"))}, title={soup.title.get_text(" ", strip=True) if soup.title else "(bez title)"}', flush=True)
    print(f'DIAGNOSTIKA: pocet textovych polozek={len(visible)}, regex kola={len(ROUND.findall(html))}, regex kola v textu={sum(bool(ROUND.search(x)) for x in visible)}', flush=True)
    for idx, item in enumerate(visible[:100]):
        print(f'DIAGNOSTIKA [{idx:03}]: {item[:220]}', flush=True)
    matches = parse(html)
    if len(matches) < 20:
        raise RuntimeError(f'Nalezeno jen {len(matches)} zápasů; kalendář nebude přepsán.')
    Path('kalendar.ics').write_bytes(build_ics(matches))
    print(f'Vygenerováno {len(matches)} zápasů; první: {matches[0][1].isoformat()}')


if __name__ == '__main__':
    main()
