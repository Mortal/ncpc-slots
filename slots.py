import os
import requests
import html5lib


NS = {'h': 'http://www.w3.org/1999/xhtml'}

YEAR = 2016


def element_text_content(element):
    return ' '.join(''.join(element.itertext()).split())


def get_document(url, filename):
    if not os.path.exists(filename):
        r = requests.get(url)
        try:
            t = r.content.decode('utf8')
        except UnicodeDecodeError:
            raise ValueError('Page is not UTF8')
        if t != r.text:
            print('Warning: requests does not think this is UTF8, but %s' %
                  r.encoding)
        with open(filename, 'w') as fp:
            fp.write(t)
    with open(filename) as fp:
        return html5lib.parse(fp.read())


def nwerc_scoreboard():
    url = ('http://nwerc%s-scoreboard.bath.ac.uk' % YEAR +
           '/static/scoreboard/static.html')
    filename = 'nwerc%s.html' % YEAR
    document = get_document(url, filename)
    tbodies = document.findall('.//h:table[@class="scoreboard"]/h:tbody', NS)
    tbody = tbodies[0]
    teams = []
    for row in tbody.findall('./h:tr', NS):
        uni_element = row.find('.//*[@class="univ"]')
        teams.append(dict(
            uni=element_text_content(uni_element),
        ))
    return teams


def ncpc_scoreboard():
    url = 'https://ncpc%s.kattis.com/standings?filter=621' % (YEAR % 100)
    filename = 'ncpc%s.html' % YEAR
    document = get_document(url, filename)
    rows = document.findall('.//h:table[@id="standings"]/h:tbody/h:tr', NS)
    teams = []
    for row in rows:
        if any(cell.get('colspan') for cell in row):
            continue
        uni_img_class = 'university-logo table-min-wrap'
        uni_img = row.find('./h:td[@class="%s"]/h:img' % uni_img_class, NS)
        uni_name = uni_img.get('alt')
        uni_name = uni_name.replace('Reykjavík', 'Reykjavik')
        teams.append(dict(
            uni=uni_name,
        ))
    if not teams:
        raise ValueError('No teams found')
    return teams


def get_uni_placements(teams):
    unis = {}
    for i, t in enumerate(teams):
        unis.setdefault(t['uni'], []).append(i)
    return unis


def uni_abbr(name):
    SPECIAL = ['NTNU', 'Forsvarets Ingeniørhøgskole',
               'IT University of Copenhagen']
    for s in SPECIAL:
        if s in name:
            return s
    abbr = name.split()[0]
    if abbr == 'University':
        abbr = name.split()[-1]
    return abbr


def find_uni(name, iterable):
    exact_name = [name]
    exact = []
    fuzzy = []
    fuzzy_search = uni_abbr(name)
    if fuzzy_search == 'NTNU':
        exact_name.append('Norwegian University of Science and Technology')
    for n in iterable:
        if n in exact_name:
            exact.append(n)
        elif fuzzy_search in n.split():
            fuzzy.append(n)
    result = exact or fuzzy
    if not result:
        return None
    if len(result) > 1:
        raise ValueError('Multiple matches for %r: %r' % (name, result))
    return result[0]


def print_not_found(uni_tr):
    for k, v in uni_tr.items():
        if v is None:
            print('Could not find NCPC uni %r in NWERC scoreboard' % k)


def print_nwerc_placements(nwerc_placements, uni_tr):
    for uni_name, p in sorted(nwerc_placements.items()):
        try:
            k = next(k for k, v in uni_tr.items() if v == uni_name)
        except StopIteration:
            k = ''
        print('%s\t%s\t%s' % (len(p), uni_name, k))


def print_nordic_counts(nwerc_placements, uni_tr):
    for k, v in sorted(uni_tr.items()):
        print('%s: %s' % (k, v and len(nwerc_placements[v])))
    tot = sum(len(nwerc_placements[v])
              for k, v in uni_tr.items() if v is not None)
    print('TOTAL: %s' % tot)


def print_second_slot(ncpc_placements, nwerc_placements, uni_tr):
    second_placement = {
        k: (p[1], p[0]) if len(p) >= 2 else (float('inf'), p[0])
        for k, p in ncpc_placements.items()}
    unis = sorted(ncpc_placements.keys(), key=lambda k: second_placement[k])
    print('%s Nordic universities ' % len(unis) +
          'sorted by second placement in NCPC')
    nwerc_slots = sum(len(nwerc_placements.get(v, ()))
                      for k, v in uni_tr.items())
    nwerc_unis = sum(1 for k, v in uni_tr.items()
                     if nwerc_placements.get(v, ()))
    print('(%s slots at NWERC filled by %s universities ' %
          (nwerc_slots, nwerc_unis) +
          '=> %s slots for seconds)' % (nwerc_slots - nwerc_unis))
    for k in unis:
        ncpc_p = [str(v+1) for v in ncpc_placements[k]]
        if len(ncpc_p) > 5:
            ncpc_p[4:] = ['...']
        print('%s (placed %s at NCPC)' % (uni_abbr(k), ', '.join(ncpc_p)))
        nwerc_p = nwerc_placements.get(uni_tr.get(k), ())
        s = ' who placed %s' % ', '.join(str(v+1) for v in nwerc_p)
        print('- sent %s team%s to NWERC%s' %
              (len(nwerc_p) or 'no', '' if len(nwerc_p) == 1 else 's',
               s if nwerc_p else ''))


def main():
    nwerc_teams = nwerc_scoreboard()
    nwerc_placements = get_uni_placements(nwerc_teams)
    ncpc_teams = ncpc_scoreboard()
    ncpc_placements = get_uni_placements(ncpc_teams)
    uni_tr = {
        name: find_uni(name, nwerc_placements.keys())
        for name in sorted(ncpc_placements.keys())}
    # print_not_found(uni_tr)
    # print_nwerc_placements(nwerc_placements, uni_tr)
    # print_nordic_counts(nwerc_placements, uni_tr)
    print_second_slot(ncpc_placements, nwerc_placements, uni_tr)


if __name__ == '__main__':
    main()
