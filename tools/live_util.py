"""Shared helpers for Ramu's stage and TV videos (used by discover_videos.py and approve_videos.py)."""
import json, re, urllib.request

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'

# Channels where "Ramu" is him (checked by face and credits, Oct 2026): name -> channel id.
TRUSTED = {
    'Gopal Sapthaswaram': 'UCSVl6kNZZIYLLnQBVCGhC1g',
    'NEZA VISION': 'UCK2nU3G6jkc7YiZaGNWCzaQ',
    'SAREGA Music School of Fine Arts': 'UCDn89PHsD-eVmwqQ4hsTBlA',
    'etvteluguindia': 'UCSs9H1cyB3OHdy8wkit8ZKg',
    'ETV Saragalu': 'UC0TI4DZ_Ql_yXzthxibIK1Q',
    'ChimataMusic-Kuteeram Concerts': 'UCINYxVwnR54-Js07MJN4s_g',
    'chimatamusic1': 'UC1VmC_yRj8I4_1VuMHQ9BQA',
    'DRUTGAMI PRODUCTIONS': 'UCkwmoOfYekdY9jTiKYQwEGQ',
    'Ramana Juvvadi': 'UCySn4ODSL_ntWL2611cyMNw',
    'enoch eno': 'UCwx9UyG01nvISRFt91UJ0kg',
}
# Channels whose owners block playing their videos on other websites.
EMBED_BLOCKED_CHANNELS = {'etvteluguindia', 'ETV Saragalu', 'ETV Telugu', 'ETV Plus India'}
# Other people called Ramu, and channels that only post SPB's own recordings.
NOT_HIM = re.compile(r'ramachandran|santhanam|vaibhav ramu|ramu thangaraj|ramu rathod|ramu yadav|nurani ramu|'
                     r'ramu music|ramu kaka|sridevi drama|jabardasth|ramu master|dance perf|#shorts|idhi kadha pandagante|hyper aadi|\bramu\b.*\b(1966|1968)\b|ramu telugu (full )?movie|- topic', re.I)
TELUGU_CHANNELS = {'etvteluguindia', 'ETV Saragalu', 'ChimataMusic-Kuteeram Concerts', 'chimatamusic1', 'Ramana Juvvadi'}
TAMIL_CHANNELS = {'Gopal Sapthaswaram'}


def watch_page(vid):
    """Title, description, publish date, length and channel from a video's page."""
    page = urllib.request.urlopen(urllib.request.Request(f'https://www.youtube.com/watch?v={vid}',
                                  headers={'User-Agent': UA, 'Accept-Language': 'en'}), timeout=30).read().decode()
    g = lambda rx: (re.search(rx, page) or [None, ''])[1]
    desc = g(r'"shortDescription":"(.*?)","isCrawlable"')
    try:
        desc = json.loads('"' + desc + '"')
    except Exception:
        pass
    return {'desc': desc, 'date': g(r'"publishDate":"([^"]+)"')[:10], 'secs': int(g(r'"lengthSeconds":"(\d+)"') or 0),
            'channel': json.loads('"' + g(r'"ownerChannelName":"(.*?)"') + '"') if g(r'"ownerChannelName":"(.*?)"') else ''}


def gopal_credits(desc):
    """Gopal Sapthaswaram descriptions carry 'Movie: X (year)' and 'Singer(s): ...' lines."""
    mv = re.search(r'Movie:\s*([^\n(]+?)\s*\((\d{4})\)', desc)
    sg = re.search(r'Singers?:\s*([^\n]+)', desc)
    if not (mv and sg):
        return None
    singers = [x.strip() for x in re.split(r',| and ', sg.group(1)) if x.strip()]
    return {'film': mv.group(1).strip(), 'year': int(mv.group(2)), 'orig': singers,
            'spb': any(re.search(r'balasubra', x, re.I) for x in singers)}


def song_from_title(title):
    """Best guess at the song name. Titles look like "Song | Film | Singers" or "Band | Singer Ramu | X song",
    so prefer the part that says "song", then the first part that isn't about the band, show or singer."""
    parts = [p.strip() for p in re.split(r'\s*[|｜]\s*|\s+[-–—]{1,2}\s+', title) if p.strip()]
    junk = re.compile(r'ramu|perform|band|orchestra|event|concert|channel|tv\b|etv|show|#|@', re.I)
    pick = next((p for p in parts if re.search(r'\bsong\b', p, re.I) and not re.search(r'ramu', p, re.I)), None) \
        or next((p for p in parts if not junk.search(p)), parts[0] if parts else title)
    t = re.sub(r'[#@]\w+', '', pick)
    t = re.split(r'\s+by\s+|\s+sung\s+by|\s+(?:Maharajapuram\s+)?Ramu\b|\s+Maharajapuram\b', t, flags=re.I)[0]
    if t.isupper():
        t = t.title()
    t = re.sub(r'[^\w\s\'’.,()&-]', '', t)
    t = re.sub(r'\b(song|live( orchestra)?|full video|video song|lyrical|performance)\b', '', t, flags=re.I)
    t = re.sub(r'^\d+\s+', '', t)
    t = ' '.join(t.split()).strip(' -,')
    return (t[:1].upper() + t[1:]) if t else title[:60]


def partner(title, desc=''):
    m = re.search(r'Ramu\s*(?:&|and|,)\s*([A-Z][a-z]+(?: [A-Z][a-z]+)?)', title + ' ' + desc[:300])
    if m:
        n = re.sub(r' (Performance|Chimata)$', '', m.group(1))
        if n not in ('Chorus', 'Others', 'Sai', 'Janaki'):
            return n
    return ''


def venue(channel, title, desc, date):
    y = (date or '')[:4]
    if channel == 'Gopal Sapthaswaram':
        return f'Live in Chennai, {y}'
    if channel == 'NEZA VISION':
        return f'Live in Kozhikode, {y}'
    if channel.startswith('SAREGA'):
        return f'Live in Toronto, {y}'
    if channel.startswith('DRUTGAMI'):
        return f'SPB tribute, {y}'
    if channel in ('etvteluguindia', 'ETV Saragalu') and 'Shivaratri' not in title:
        m = re.search(r'(20\d\d)', title)
        yy = m.group(1) if m else ''
        show = 'ETV Padutha Theeyaga' if 'Padutha' in title else 'ETV Swarabhishekam' if re.search('Swarabhishekam|స్వరాభిషేకం', title) else 'ETV'
        return show + (f', {yy}' if yy else '')
    if 'Shivaratri' in title:
        m = re.search(r'(20\d\d)', title)
        return 'ETV Maha Shivaratri special' + (f', {m.group(1)}' if m else '')
    if 'Bay Area' in title:
        return f'Live in San Francisco Bay Area, {y}'
    if 'Greenbelt' in desc:
        return f'Live in Washington DC area, {y}'
    if 'TANTEX' in desc:
        return f'Live in Dallas, {y}'
    if channel == 'enoch eno' or 'trichy' in (title + desc).lower():
        return f'Live in Trichy, {y}'
    if 'Ravindra Bharathi' in title + desc:
        return f'Live in Hyderabad, {y}'
    return f'Live, {y}' if y else 'Live'


def lang_guess(channel, title):
    if re.search(r'[ఀ-౿]', title) or channel in TELUGU_CHANNELS:
        return 'telugu'
    if re.search(r'[஀-௿]', title) or channel in TAMIL_CHANNELS:
        return 'tamil'
    if re.search(r'[ऀ-ॿ]', title):
        return 'hindi'
    return 'other'
