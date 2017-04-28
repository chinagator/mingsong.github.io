#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

from jinja2 import Environment, Template


def dict_from_tuple(keys, data):
    return dict(zip(keys, data))


def make_dict(key, data, f):
    return dict((d[key], d) for d in map(f, data))


def make_venue(data):
    return dict_from_tuple(['year', 'month', 'city', 'country'], data)


def make_conference(data):
    d = dict_from_tuple(['key', 'shortname', 'name', 'publisher', 'venues', 'type'], data + ('conf',))
    d['venues'] = make_dict('year', d['venues'], make_venue)
    return d


def make_journal(data):
    return dict_from_tuple(['key', 'name', 'publisher', 'webpage'], data)


def make_author(data):
    return dict_from_tuple(['key', 'firstname', 'lastname'], data)


def make_university(data):
    return dict_from_tuple(['key', 'name', 'city', 'country', 'webpage', 'original_name'], data)


def make_conference_paper(data):
    global conferences
    global authors

    d = dict_from_tuple(['authors', 'conf', 'year', 'title', 'pages', 'doi', 'tools','ppt','award'], data)
    d['authors'] = [authors[k] for k in d['authors']]
    d['conf'] = conferences[d['conf']]
    return d


def make_article(data):
    global journals
    global authors

    d = dict_from_tuple(['authors', 'journal', 'volume', 'number', 'year', 'title', 'pages', 'doi', 'tools','benchmarks'], data)
    d['authors'] = [authors[k] for k in d['authors']]
    d['journal'] = journals[d['journal']]
    return d


def make_preprint(data):
    global authors

    d = dict_from_tuple(['authors', 'id', 'title', 'comments', 'ref', 'subj'], data)
    d['authors'] = [authors[k] for k in d['authors']]
    return d


def make_news(data):
    global conferences
    global journals
    global confpapers
    global articles

    d = dict_from_tuple(['name', 'year'], data)

    if d['name'] == 'words':
        d['type'] = 'word'
    elif d['name'] in conferences:
        d['type'] = 'conf'
        d['papers'] = list(
            reversed([p for p in confpapers if p['conf']['key'] == d['name'] and p['year'] == d['year']]))
    else:
        d['type'] = 'journal'
        d['papers'] = list(
            reversed([a for a in articles if a['journal']['key'] == d['name'] and a['volume'] == d['year']]))

    return d


def make_invited(data):
    global conferences
    global universities

    d = dict_from_tuple(['year', 'month', 'type', 'type_key', 'host', 'title', 'webpage'], data)

    if d['type'] == 'uni':
        d['uni'] = universities[d['type_key']]
    elif d['type'] == 'conf':
        d['conf'] = conferences[d['type_key']]

    return d


def make_filename(c, collection):
    conf = c['conf']['key']
    year = c['year']

    same_venue = [c2 for c2 in collection if c2['conf']['key'] == conf and c2['year'] == year]

    if len(same_venue) == 1:
        return "%s_%s" % (year, conf)
    else:
        return "%s_%s_%d" % (year, conf, same_venue.index(c) + 1)


def make_bibtex_title(title):
    global capitalize, replacements

    for c in capitalize:
        title = title.replace(c, "{%s}" % c)
    for r, s in replacements:
        title = title.replace(r, s)
    return title


def format_bibtex_incollection(paper, collection, keyword):
    global capitalize

    conf = paper['conf']
    venue = conf['venues'][paper['year']]

    title = make_bibtex_title(paper['title'])

    print("@inproceedings{%s," % make_filename(paper, collection))
    print("  author    = {%s}," % " and ".join("%s, %s" % (a['lastname'], a['firstname']) for a in paper['authors']))
    print("  title     = {%s}," % title)
    print("  booktitle = {%s}," % conf['name'])
    print("  year      = %d," % paper['year'])
    print("  month     = %s," % venue['month'])
    print("  address   = {%s, %s}," % (venue['city'], venue['country']))
    if paper['pages'] != "XXXX":
        print("  pages     = {%s}," % paper['pages'])
    if conf['publisher'] != "":
        print("  publisher = {%s}," % conf['publisher'])
    print("  keywords  = {%s}" % keyword)
    print("}")


def format_haml_incollection(paper, id):
    global best_paper_data

    conf = paper['conf']
    venue = conf['venues'][paper['year']]

    env = Environment()
    template = env.from_string('''
.item
  .pubmain
    .pubassets
      {{external}}
      %a.paper(href="papers/{{filename}}.pdf" data-toggle="tooltip" data-placement="top" title="View PDF")
        %span.glyphicon.glyphicon-cloud-download
    -#%a.paper(href="papers/{{filename}}.pdf")
      -#%img.pubthumb(src="images/{{image}}.png")
    %h4.pubtitle#c{{id}}
      %a(href="{{doi}}" target="_blank") {{title}}
    .pubauthor
      {{authors}}
    .pubcite
      %span.label.label-warning C{{id}}
      In {{conf}} ({{shortname}}) | {{city}}, {{country}}, {{month}} {{year}} {{pages}} {{tools}} {{ppt}} {{award}} ''')

    authors = ",\n      ".join("%s %s" % (a['firstname'], a['lastname']) for a in paper['authors'])
    authors = authors.replace("Mingsong Chen", "%strong Mingsong Chen")

    filename = make_filename(paper, confpapers)
    image = "thumbs/" + filename if os.path.exists("images/thumbs/%s.png" % filename) else "nothumb"

    external = ""
    if paper['doi'] != "":
        external = "%%a(href=\"%s\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Open paper\" target=\"_blank\")\n        %%span.glyphicon.glyphicon-new-window" % \
                   paper['doi']

    besta = [b[1] for b in best_paper_data if b[0] == filename]
    if len(besta) == 0:
        best = ""
    elif besta[0] == 'c':
        best = "\n    .pubcite(style=\"color: #990000\")\n      %%span.glyphicon.glyphicon-certificate\n      %b Best paper candidate"

    print(template.render({'title': paper['title'],
                           'id': id,
                           'doi': paper['doi'],
                           'filename': "C%s"%id,
                           'image': image,
                           'authors': authors,
                           'conf': conf['name'],
                           'shortname': conf['shortname'],
                           'city': venue['city'],
                           'country': venue['country'],
                           'month': monthnames[venue['month']],
                           'year': venue['year'],
                           'external': external,
                           'pages': " | Pages %s" % paper['pages'].replace("--", "&ndash;") if paper[
                                                                                                   'pages'] != "XXXX" else "",
                           'tools': " | <a href=\"%s\" target=\"_blank\"> tools </a>" % paper[
                               'tools'] if 'tools' in paper else "",
                           'ppt': " | <a href=\"%s\" target=\"_blank\"> ppt </a>" % paper[
                               'ppt'] if 'ppt' in paper else "",
                           'award': " | <span class='red'> %s</span>" % paper[
                               'award'] if 'award' in paper else "",
                           'publisher': conf['publisher'],
                           'best': best})[1:])


def format_haml_incollection_work(paper, id):
    conf = paper['conf']
    venue = conf['venues'][paper['year']]

    env = Environment()
    template = env.from_string('''
.item
  .pubmain
    %h4.pubtitle#w{{id}}
      {{title}}
    .pubauthor
      {{authors}}
    .pubcite
      %span.label.label-warning Workshop Paper {{id}}
      In {{conf}} ({{shortname}}) | {{city}}, {{country}}, {{month}} {{year}}{{pages}} | Publisher: {{publisher}}''')

    authors = ",\n      ".join("%s %s" % (a['firstname'], a['lastname']) for a in paper['authors'])
    authors = authors.replace("Mathias Soeken", "%strong Mathias Soeken")

    filename = make_filename(paper, workpapers)
    image = "thumbs/" + filename if os.path.exists("images/thumbs/%s.png" % filename) else "nothumb"

    external = ""
    if paper['doi'] != "":
        external = "%%a(href=\"%s\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Open paper\" target=\"_blank\")\n        %%span.glyphicon.glyphicon-new-window" % \
                   paper['doi']

    print(template.render({'title': paper['title'],
                           'id': id,
                           'filename': filename,
                           'image': image,
                           'authors': authors,
                           'conf': conf['name'],
                           'shortname': conf['shortname'],
                           'city': venue['city'],
                           'country': venue['country'],
                           'month': monthnames[venue['month']],
                           'year': venue['year'],
                           'external': external,
                           'pages': " | Pages %s" % paper['pages'].replace("--", "&ndash;") if paper[
                                                                                                   'pages'] != "XXXX" else "",
                           'publisher': conf['publisher']})[1:])


def format_bibtex_article(paper):
    global capitalize

    journal = paper["journal"]

    name = make_bibtex_title(journal["name"])
    title = make_bibtex_title(paper['title'])

    print("@article{%s%d," % (journal['key'], paper['year']))
    print("  author    = {%s}," % " and ".join("%s, %s" % (a['lastname'], a['firstname']) for a in paper['authors']))
    print("  title     = {%s}," % title)
    print("  journal   = {%s}," % name)
    if paper['volume'] == -1:
        print("  note      = {in press},")
    else:
        print("  year      = %d," % paper['year'])
        print("  volume    = %d," % paper['volume'])
        print("  number    = {%s}," % paper['number'])
        if paper['pages'] != "XXXX":
            print("  pages     = {%s}," % paper['pages'])
    print("  publisher = {%s}," % journal['publisher'])
    print("  keywords  = {article}")
    print("}")


def format_haml_article(paper, id):
    journal = paper['journal']

    env = Environment()
    template = env.from_string('''
.item
  .pubmain
    .pubassets
      {{external}}
      %a(href="papers/{{filename}}.pdf" data-toggle="tooltip" data-placement="top" title="View PDF")
        %span.glyphicon.glyphicon-cloud-download
      -#%a(href="{{webpage}}" target="_blank")
      -#%img.pubthumb(src="images/covers/{{key}}.png" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Open journal homepage\")
    %h4.pubtitle#j{{id}} 
      %a(href="{{doi}}" target="_blank") {{title}}
    .pubauthor
      {{authors}}
    .pubcite
      %span.label.label-info J{{id}}
      In {{journal}} {{info}}{{pages}} {{tools}} {{benchmarks}}''')

    authors = ",\n      ".join("%s %s" % (a['firstname'], a['lastname']) for a in paper['authors'])
    authors = authors.replace("Mingsong Chen", "%strong Mingsong Chen")
    authors = authors.replace("陈铭松", "%strong 陈铭松")

    number = "(%s)" % paper['number'] if paper['number'] != "" else ""

    external = ""
    if paper['doi'] != "":
        external = "%%a(href=\"%s\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Open paper\" target=\"_blank\")\n        %%span.glyphicon.glyphicon-new-window" % \
                   paper['doi']

    if paper['volume'] == -1:
        info = ""
    else:
        info = "%s%s, %s" % (paper['volume'], number, paper['year'])

    print(template.render({'title': paper['title'],
                           'doi': paper['doi'],
                           'id': id,
                           'key': journal['key'],
                           'filename': "J%s"%id,
                           'webpage': paper['journal']['webpage'],
                           'authors': authors,
                           'journal': paper['journal']['name'],
                           'info': info,
                           'pages': " | Pages %s" % paper['pages'].replace("--", "&ndash;") if paper[
                                                                                                   'pages'] != "XXXX" else "",
                           'tools': " | <a href=\"%s\" target=\"_blank\"> tools </a>" % paper[
                               'tools'] if 'tools' in paper else "",
                           'benchmarks': " | <a href=\"%s\" target=\"_blank\"> benchmarks </a>" % paper[
                               'benchmarks'] if 'benchmarks' in paper else "",
                           'external': external,
                           'publisher': journal['publisher']})[1:])


def format_bibtex_preprint(paper):
    global capitalize

    title = make_bibtex_title(paper['title'])

    print("@article{arxiv_%s," % paper['id'])
    print("  author    = {%s}," % " and ".join("%s, %s" % (a['lastname'], a['firstname']) for a in paper['authors']))
    print("  title     = {%s}," % title)
    print("  journal   = {arXiv},")
    print("  year      = {%s}," % ('20' + paper['id'][0:2]))
    print("  volume    = {%s}," % paper['id'])
    print("  keywords  = {preprint}")
    print("}")


def format_haml_preprint(paper, id):
    global months

    env = Environment()
    template = env.from_string('''
.item
  .pubmain
    .pubassets
      %a(href="http://arxiv.org/abs/{{id}}" data-toggle="tooltip" data-placement="top" title="Open webpage" target="_blank")
        %span.glyphicon.glyphicon-new-window
      %a(href="http://arxiv.org/pdf/{{id}}" data-toggle="tooltip" data-placement="top" title="View PDF" target="_blank")
        %span.glyphicon.glyphicon-cloud-download
    %a.paper(href="http://arxiv.org/pdf/{{id}}" target="_blank")
      %img.pubthumb(src="images/thumbs/arxiv_{{id}}.png")
    %h4.pubtitle#p{{nid}} {{title}}
    .pubauthor
      {{authors}}
    .pubcite
      %span.label.label-danger Preprint {{nid}}
      arXiv:{{id}} | {{month}} {{year}}
      {{ref}}| Comments: {{comments}} | Subjects: {{subjects}}''')

    authors = ",\n      ".join("%s %s" % (a['firstname'], a['lastname']) for a in paper['authors'])
    authors = authors.replace("Mathias Soeken", "%strong Mathias Soeken")

    subjects = "; ".join(paper['subj'])

    ref = ""
    if paper['ref'] != "":
        ref = "|\n      %%a(href=\"publications.html#%s\") Reference\n      " % paper['ref']

    print(template.render({'title': paper['title'],
                           'authors': authors,
                           'id': paper['id'],
                           'nid': id,
                           'month': months[int(paper['id'][2:4]) - 1],
                           'year': '20' + paper['id'][0:2],
                           'comments': paper['comments'],
                           'ref': ref,
                           'subjects': subjects}))


def format_haml_news(news):
    # print("%li.list-group-item")
    print("%li")

    if news['type'] == "conf":
        papers = news['papers']

        if len(papers) == 1:
            article = "  %%a(href=\"publications.html#c%i\") %s\n" % (
                confpapers.index(papers[0]) + 1, papers[0]["title"])
        else:
            article = "  %ul\n"
            for p in papers:
                article += "    %%li\n      %%a(href=\"publications.html#c%i\") %s\n" % (
                    confpapers.index(p) + 1, p["title"])
        print(
            "  The paper%s\n%s  %s been accepted by the %s %d conference.\n  " % (
                "s" if len(papers) > 1 else "", article, "have" if len(papers) > 1 else "has",
                papers[0]["conf"]["shortname"], papers[0]["year"]))
    if news['type'] == "journal":
        papers = news['papers']

        if len(papers) == 1:
            article = "  %%a(href=\"publications.html#j%i\") %s\n" % (articles.index(papers[0]) + 1, papers[0]["title"])
        else:
            article = "  %ul\n"
            for p in papers:
                article += "    %%li\n      %%a(href=\"publications.html#j%i\") %s\n" % (
                    articles.index(p) + 1, p["title"])
        print(
            "  The article%s\n%s  got accepted for publication in\n  %%i %s.\n  " % (
                "s" if len(papers) > 1 else "", article, papers[0]["journal"]["name"]))

    if news['type'] == "word":
        print(news['word'])


def write_publications():
    global confpapers

    text = Template('''
\documentclass[conference]{IEEEtran}
\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}

    \\usepackage[backend=biber,style=ieee]{biblatex}
\\addbibresource{publications.bib}

\\title{List of Publications}
\\author{
  \IEEEauthorblockN{Mathias Soeken}
  \IEEEauthorblockA{Integrated Systems Laboratory, EPFL, Switzerland}
}

\\begin{document}
  \\maketitle

  \\nocite{*}
  \printbibliography[type=book,title={Books}]
  \printbibliography[type=incollection,title={Book chapters}]
  \printbibliography[type=article,keyword=article,title={Journal articles}]
  \printbibliography[type=inproceedings,keyword=conference,title={Conference papers}]
  \printbibliography[type=article,keyword=preprint,title={Preprints}]
  \printbibliography[type=inproceedings,keyword=workshop,title={Refereed papers without formal proceedings}]
\end{document}''')

    with open("publications.tex", "w") as f:
        f.write(text.render().strip() + "\n")


def format_haml_invited(invited):
    template = Template('''
.pitem
  .pubmain(style="min-height:0px")
    {{ logo }}
    %h4.pubtitle {{ title }}
    .project-description
      Talk
      %i {{ talk_title }}
      {{ host }}
      ({{ month }}{{ year }})
    {{ more }}''')

    if invited['type'] == "uni":
        uni = invited['uni']
        title = uni['name']
        if uni['original_name'] != '':
            title += " (" + uni['original_name'] + ")"
        logo = '%%a(href="%s" target="_blank")\n      %%img.project-thumb(src="images/logos/%s.png" border="0")' % (
            uni['webpage'], uni['key'])
        host = 'invited by ' + invited['host']
    else:
        conf = invited['conf']
        title = conf['name'] + " " + str(invited['year'])
        logo = ''
        host = ''

    if invited['webpage'] != '':
        more = '.project-description\n      %%a(href="%s" target="_blank") More information' % invited['webpage']
    else:
        more = ''

    talk_title = invited['title']
    month = monthnames[invited['month']] + " " if invited['month'] != '' else ''
    year = invited['year']

    print(template.render(title=title, logo=logo, talk_title=talk_title, host=host, month=month, year=year, more=more))


monthnames = {'jan': 'January', 'feb': 'February', 'mar': 'March', 'apr': 'April', 'may': 'May', 'jun': 'June',
              'jul': 'July', 'aug': 'August', 'sep': 'September', 'oct': 'October', 'nov': 'November',
              'dec': 'December'}
months = ["January", "Feburary", "March", "April", "May", "June", "July", "August", "September", "October", "November",
          "December"]
capitalize = ["AIGs", "Alle", "Ausdrücken", "BDD", "Beschreibungen", "Boolean", "CMOS",
              "Completeness-Driven Development", "CPU", "ESL", "Formal Specification Level", "Fredkin", "Gröbner",
              "Hadamard", "HDL", "IDE", "Industrie", "LEXSAT", "lips", "LUT", "LUTs", "metaSMT", "Methoden", "MIG",
              "NCV", "NoC", "NPN", "OCL", "Pauli", "RevKit", "RISC", "RRAM", "SAT", "SMT-LIB2", "SyReC", "MPSoC",
              "Toffoli", "UML"]
replacements = [("Clifford+T", "{Clifford+$T$}"), ("ε", "{$\\varepsilon$}"), ("πDD", "{$\\pi$DD}"), ("&", "\&")]

conferences_data = [
    ('apms', 'APMS', 'Advances in Production Management Systems', 'IFIP', [
        (2014, 'sep', 'Ajaccio', 'France')
    ]),
    ('aspdac', 'ASP-DAC', 'Asia and South Pacific Design Automation Conference', 'IEEE', [
        (2012, 'jan', 'Sydney', 'Australia'),
        (2013, 'jan', 'Yokohama', 'Japan'),
        (2016, 'jan', 'Macau', 'China'),
        (2017, 'jan', 'Tokyo', 'Japan')
    ]),
    ('ast', 'AST', 'International Workshop on Automation of Software Test', 'ACM', [
        (2013, 'may', 'San Francisco, CA', 'USA')
    ]),
    ('cukeup', '', 'CukeUp!', 'Skills Matter', [
        (2012, 'apr', 'London', 'England'),
        (2013, 'apr', 'London', 'England')
    ]),
    ('dac', 'DAC', 'Design Automation Conference', 'ACM/IEEE', [
        (2010, 'jun', 'Anaheim, CA', 'USA'),
        (2016, 'jun', 'Austin, TX', 'USA'),
        (2017, 'jun', 'Austin, TX', 'USA')
    ]),
    ('date', 'DATE', 'Design, Automation and Test in Europe', 'IEEE', [
        (2010, 'mar', 'Dresden', 'Germany'),
        (2011, 'mar', 'Grenoble', 'France'),
        (2012, 'mar', 'Dresden', 'Germany'),
        (2013, 'mar', 'Grenoble', 'France'),
        (2014, 'mar', 'Dresden', 'Germany'),
        (2015, 'mar', 'Grenoble', 'Germany'),
        (2016, 'mar', 'Dresden', 'Germany'),
        (2017, 'mar', 'Lausanne', 'Switzerland')
    ]),
    ('ddecs', 'DDECS',
     'IEEE International Symposium on Design and Diagnostics of Electronic Circuits and Systems',
     'IEEE', [
         (2010, 'apr', 'Vienna', 'Austria'),
         (2011, 'apr', 'Cottbus', 'Germany'),
         (2013, 'apr', 'Karlovy Vary', 'Czech Republic'),
         (2015, 'apr', 'Belgrad', 'Serbia'),
         (2016, 'apr', 'Košice', 'Slovakia')
     ]),
    (
        'difts', 'DIFTS', 'International Workshop on Design and Implementation of Formal Tools and Systems',
        '', [
            (2014, 'oct', 'Lausanne', 'Switzerland')
        ]),
    ('dgk', 'DGK', 'Annual Conference of the German Crystallographic Society', '', [
        (2013, 'mar', 'Freiberg', 'Germany')
    ]),
    ('duhde', 'DUHDe', 'DATE Friday Workshop: Design Automation for Understanding Hardware Designs', '', [
        (2014, 'mar', 'Dresden', 'Germany'),
        (2015, 'mar', 'Grenoble', 'France'),
        (2016, 'mar', 'Dresden', 'Germany')
    ]),
    ('fdl', 'FDL', 'Forum on Specification and Design Languages', 'IEEE', [
        (2012, 'sep', 'Vienna', 'Austria'),
        (2014, 'oct', 'Munich', 'Germany')
    ]),
    ('fmcad', 'FMCAD', 'Formal Methods in Computer-Aided Design', 'IEEE', [
        (2015, 'sep', 'Austin, TX', 'USA'),
        (2016, 'oct', 'Mountain View, CA', 'USA')
    ]),
    ('fpl', 'FPL', 'International Conference on Field-Programmable Logic and Applications', 'IEEE', [
        (2016, 'sep', 'Lausanne', 'Switzerland')
    ]),
    ('gecco', 'GECCO', 'Genetic and Evolutionary Computation Conference', 'ACM', [
        (2015, 'jul', 'Madrid', 'Spain'),
        (2016, 'jul', 'Denver, CO', 'USA'),
        (2017, 'jul', 'Berlin', 'Germany')
    ]),
    ('gi', 'GI', 'Jahrestagung der Gesellschaft für Informatik', 'GI', [
        (2013, 'sep', 'Koblenz', 'Germany')
    ]),
    ('glsvlsi', 'GLSVLSI', 'Great Lakes Symposium on VLSI', 'ACM', [
        (2017, 'may', 'Banff, AB', 'Canada'),
        (2008, 'may', 'New York', 'USA'),
    ]),
    ('hldvt', 'HLDVT', 'International Workshop on High-Level Design Validation and Test', 'IEEE', [
        (2012, 'nov', 'Huntington Beach, CA', 'USA'),
        (2007, 'nov', 'Irvine, CA', 'USA'),
    ]),
    ('hvc', 'HVC', 'Haifa Verification Conference', 'Springer', [
        (2016, 'nov', 'Haifa', 'Israel')
    ]),
    ('iccad', 'ICCAD', 'International Conference on Computer-Aided Design', 'IEEE', [
        (2014, 'nov', 'San Jose, CA', 'USA'),
        (2016, 'nov', 'Austin, TX', 'USA')
    ]),
    ('icgt', 'ICGT', 'International Conference on Graph Transformation', 'Springer', [
        (2012, 'sep', 'Bremen', 'Germany')
    ]),
    ('idt', 'IDT', 'International Test and Design Symposium', 'IEEE', [
        (2010, 'dec', 'Abu Dhabi', 'United Arab Emirates'),
        (2013, 'dec', 'Marrakesh', 'Marocco')
    ]),
    ('iscas', 'ISCAS', 'International Symposium on Circuits and Systems', 'IEEE', [
        (2016, 'may', 'Montreal, QC', 'Canada'),
        (2017, 'may', 'Baltimore, MD', 'USA')
    ]),
    ('ismvl', 'ISMVL', 'International Symposium on Multiple-Valued Logic', 'IEEE', [
        (2011, 'may', 'Tuusula', 'Finland'),
        (2012, 'may', 'Victoria, BC', 'Canada'),
        (2013, 'may', 'Toyama', 'Japan'),
        (2015, 'may', 'Waterloo, ON', 'Canada'),
        (2016, 'may', 'Sapporo', 'Japan'),
        (2017, 'may', 'Novi Sad', 'Serbia')
    ]),
    ('isvlsi', 'ISVLSI', 'IEEE Computer Society Annual Symposium on VLSI', 'IEEE', [
        (2008, 'apr', 'Montpellier', 'France'),
        (2012, 'aug', 'Amherst, MA', 'USA'),
        (2013, 'aug', 'Natal', 'Brazil'),
    ]),
    ('iwls', 'IWLS', 'International Workshop on Logic Synthesis', '', [
        (2015, 'jul', 'Mountain View, CA', 'USA'),
        (2016, 'jul', 'Austin, TX', 'USA')
    ]),
    ('iwsbp', 'IWSBP', 'International Workshop on Boolean Problems', '', [
        (2012, 'sep', 'Freiberg', 'Germany'),
        (2014, 'sep', 'Freiberg', 'Germany'),
        (2016, 'sep', 'Freiberg', 'Germany')
    ]),
    ('lascas', 'LASCAS', 'IEEE Latin Amarican Symposium on Circuits and Systems', 'IEEE', [
        (2016, 'feb', 'Florianopolis', 'Brazil')
    ]),
    (
        'mbmv', 'MBMV',
        'Methoden und Beschreibungssprachen zur Modellierung und Verifikation von Schaltungen und Systemen',
        '', [
            (2010, 'mar', 'Dresden', 'Germany'),
            (2011, 'mar', 'Oldenburg', 'Germany'),
            (2013, 'mar', 'Rostock', 'Germany'),
            (2014, 'mar', 'Böblingen', 'Germany'),
            (2016, 'mar', 'Freiburg', 'Germany')
        ]),
    ('mecoes', 'MeCoES', 'International Workshop on and Code Generation for Embedded Systems', '', [
        (2012, 'oct', 'Tampere', 'Finland')
    ]),
    ('modevva', 'MoDeVVa', 'Model-Driven Engineering, Verification, And Validation', 'ACM', [
        (2011, 'oct', 'Wellington', 'New Zealand'),
        (2015, 'oct', 'Ottawa, ON', 'Canada')
    ]),
    ('nanoarch', 'NANOARCH', 'International Symposium on Nanoscale Architectures', 'IEEE', [
        (2016, 'jul', 'Beijing', 'China')
    ]),
    (
        'naturalise', 'NaturaLiSE',
        'International Workshop on Natural Language Analysis in Software Engineering',
        '', [
            (2013, 'may', 'San Francisco, CA', 'USA')
        ]),
    ('rc', 'RC', 'Conference on Reversible Computation', 'Springer', [
        (2011, 'jul', 'Ghent', 'Belgium'),
        (2012, 'jul', 'Copenhagen', 'Denmark'),
        (2013, 'jul', 'Victoria, BC', 'Canada'),
        (2014, 'jul', 'Kyoto', 'Japan'),
        (2015, 'jul', 'Grenoble', 'France'),
        (2016, 'jul', 'Bologna', 'Italy')
    ]),
    ('rcw', 'RC', 'Workshop on Reversible Computation', 'Springer', [
        (2010, 'jul', 'Bremen', 'Germany'),
        (2011, 'jul', 'Ghent', 'Belgium'),
    ]),
    ('rm', 'RM', 'Reed-Muller Workshop', '', [
        (2015, 'may', 'Waterloo, ON', 'Canada'),
        (2017, 'may', 'Novi Sad', 'Serbia')
    ]),
    (
        'sat', 'SAT', 'International Conference on Theory and Applications of Satisfiability Testing',
        'Springer',
        [
            (2016, 'jul', 'Bordeaux', 'France')
        ]),
    ('sbcci', 'SBCCI', 'Symposium on Integrated Circuits and Systems Design', 'ACM', [
        (2014, 'sep', 'Aracaju', 'Brazil')
    ]),
    ('sec', 'SEC', 'International Workshop on the Swarm at the Edge of the Cloud', '', [
        (2013, 'sep', 'Montreal, QC', 'Canada')
    ]),
    ('tap', 'TAP', 'International Conference on Tests and Proofs', 'Springer', [
        (2011, 'jun', 'Zürich', 'Switzerland'),
        (2014, 'jul', 'York', 'England'),
        (2015, 'jul', "L'Aquila", 'Italy')
    ]),
    ('tools', 'TOOLS', 'International Conference on Objects, Models, Components, Patterns', 'Springer', [
        (2012, 'may', 'Prague', 'Czech Republic')
    ]),
    ('vlsisoc', 'VLSI-SoC', 'International Conference on Very Large Scale Integration', 'IEEE', [
        (2015, 'oct', 'Daejon', 'Korea')
    ]),
    ('isssr', 'ISSSR', 'International Symposium on System and Software Reliability', 'IEEE', [
        (2016, 'dec', 'Shanghai', 'China')
    ]),

    ('icpads', 'ICPADS', 'International Conference on Parallel and Distributed Systems', 'IEEE', [
        (2016, 'dec', 'Wuhan', 'China')
    ]),

    ('qrs', 'QRS', 'International Conference on Software Quality, Reliability & Security', 'IEEE', [
        (2016, 'aug', 'Vienna', 'Austria')
    ]),

    ('seke', 'SEKE', 'International Conference on Software Engineering and Knowledge Engineering', 'IEEE', [
        (2016, 'jul', 'San Francisco, CA', 'USA')
    ]),

    ('compsac', 'COMPSAC', 'International Conference on Software Engineering and Knowledge Engineering',
     'IEEE', [
         (2016, 'jun', 'Georgia', 'USA'),
         (2015, 'jul', 'Taichung', 'Taiwan')
     ]),

    ('apsec', 'APSEC', 'Asia-Pacific Software Engineering Conference', 'IEEE', [
        (2016, 'dec', 'Hamilton', ' New Zealand'),
        (2014, 'dec', '', 'South Korea')
    ]),

    ('cloud', 'CLOUD', 'The IEEE International Conference on Cloud Computing', 'IEEE', [
        (2016, 'jun', 'San Francisco', 'USA')
    ]),

    ('qrs', 'QRS', 'International Conference on Software Quality, Reliability & Security', 'IEEE', [
        (2016, 'aug', 'Vienne', 'Ausria')
    ]),

    ('bdcloud', 'BdCloud', 'IEEE International Conference on Big Data and Cloud Computing ', 'IEEE', [
        (2014, 'dec', 'Sydney', 'Australia')
    ]),

    ('sere', 'SERE', 'IEEE International Conference on Software Security and Reliability', 'IEEE', [
        (2014, 'jun', 'CA', 'USA')
    ]),

    ('icse', 'ICSE', ' International Conference on Software Engineering', 'IEEE', [
        (2014, 'jul', 'hyderabad', 'india')
    ]),

    ('vlsid', 'ICSE', ' International Conference on VLSI Design', 'IEEE', [
        (2014, 'jan', 'Mumbai', 'india'),
        (2013, 'jan', 'Pune', 'india'),
        (2010, 'jan', 'Bangalore', 'india'),
    ]),

    ('iceccs', 'ICECCS', 'International Conference on Engineering of Complex Computer Systems', 'IEEE', [
        (2013, 'feb', '', 'Singapore')
    ]),

    ('codes', 'CODES+ISSS', ' International Conference on Hardware/Software Codesign and System Synthesis Design',
     'IEEE', [
         (2013, 'sep', '', ''),
         (2012, 'sep', '', ''),
     ]),

    ('isorc', 'ISORC',
     'IEEE International Symposium on Object/component/service-oriented Real-time distributed Computing', 'IEEE', [
         (2012, 'apr', 'Shenzhen', 'China')
     ]),

    ('apsi', 'APSI',
     'Proceedings of the Fourth Asia-Pacific Symposium on Internetware', 'ACM', [
         (2012, 'oct', 'QingDao', 'China')
     ]),

    ('crwadad', 'CRAWDAD',
     'CRAWDAD Workshop', 'ACM', [
         (2007, 'sep', 'Montréal', 'Canada')
     ]),

    ('ast', 'AST',
     'First International Workshop on Automation on Software Test', 'IEEE', [
         (2006, 'may', 'Shanghai', 'China')
     ]),
]

# 期刊简称
journals_data = [
    ('cnf', 'Combustion and Flame', 'Elsevier', 'http://www.journals.elsevier.com/combustion-and-flame/'),
    ('computer', 'Computer', 'IEEE', 'https://www.computer.org/computer-magazine/'),
    ('cps', 'Cyber-Physical Systems: Theory & Applications', 'IET',
     'http://digital-library.theiet.org/content/journals/iet-cps;jsessionid=15e1smt7vf2ux.x-iet-live-01'),
    ('integration', 'Integration', 'Elsevier', 'http://www.journals.elsevier.com/integration-the-vlsi-journal/'),
    ('ipl', 'Information Processing Letters', 'Elsevier',
     'http://www.journals.elsevier.com/information-processing-letters/'),
    ('jetc', 'Journal on Emerging Technologies in Computing Systems', 'ACM', 'http://jetc.acm.org/'),
    ('jsc', 'Journal of Symbolic Computation', 'Elsevier',
     'http://www.journals.elsevier.com/journal-of-symbolic-computation/'),
    ('mvl', 'Multiple-Valued Logic and Soft Computing', 'Old City Publishing',
     'http://www.oldcitypublishing.com/journals/mvlsc-home/'),
    ('pra', 'Physical Review A', 'American Physical Society', 'http://journals.aps.org/pra/'),
    ('sosym', 'Software and System Modeling', 'Springer', 'http://www.sosym.org/'),
    ('sttt', 'Journal on Software Tools for Technology Transfer', 'Springer',
     'http://www.springer.com/computer/swe/journal/10009'),
    ('tcad', 'IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems', 'IEEE', ''),
    ('tcs', 'Theoretical Computer Science', 'Elsevier',
     'http://www.journals.elsevier.com/theoretical-computer-science/'),
    ('zk', 'Zeitschrift für Kristallographie - Crystalline Materials', 'De Gruyter',
     'http://www.degruyter.com/view/j/zkri'),
    ('jmm', 'Journal of Microprocessors and Microsystems', 'Elsevier',
     'https://www.journals.elsevier.com/microprocessors-and-microsystems/'),
    ('tpds', 'IEEE Transactions on Parallel and Distributed Systems', 'IEEE',
     'http://ieeexplore.ieee.org/xpl/RecentIssue.jsp?punumber=71'),
    ('jcsc', 'Journal of Circuits, Systems and Computers', 'World Scientific',
     'http://www.worldscientific.com/worldscinet/jcsc'),
    ('tcc', 'IEEE Transactions on Cloud Computing', 'IEEE',
     'http://ieeexplore.ieee.org/xpl/RecentIssue.jsp?punumber=6245519'),
    ('todaes', 'ACM Transactions on Design Automation of Electronic Systems', 'ACM',
     'http://todaes.acm.org/'),
    ('tc', 'IEEE Transactions on Computers', 'IEEE',
     'https://www.computer.org/web/tc'),
    ('jetta', 'Journal of Electronic Testing', 'Springer',
     'http://www.springer.com/engineering/circuits+%26+systems/journal/10836'),
    ('fcsc', 'Frontiers of Computer Science in China', 'Springer',
     'https://link.springer.com/journal/117046'),
    ('tecs', 'ACM Transactions on Embedded Computing Systems', 'ACM',
     'http://tecs.acm.org/'),
    ('tcj', 'The Computer Journal', 'Oxford Academic',
     'https://academic.oup.com/comjnl'),
    ('jos', '软件学报', '',
     'http://www.jos.org.cn'),
    ('ceaj', '基于GPU平台的有效字典压缩与解压缩技术', '',
     'http://www.ceaj.org/'),
    ('zgjsjxhtx', '中国计算机学会通讯', '',
     'www.ccf.org.cn/sztsg/cbw/zgjsjxhtx/'),
    ('jsjkx', '计算机科学', '',
     'www.jsjkx.com'),
]

# 作者简称
authors_data = [
    ('aaa', 'Arman', 'Allahyari-Abhari'),
    ('ac', 'Anupam', 'Chattopadhyay'),
    ('ac2', 'Arun', 'Chandrasekharan'),
    ('adm', 'Anton', 'De Meester'),
    ('adv', 'Alexis', 'De Vos'),
    ('am', 'Alan', 'Mishchenko'),
    ('ap', 'Ana', 'Petkovska'),
    ('asa', 'Amr', 'Sayed Ahmed'),
    ('bb', 'Bernd', 'Becker'),
    ('bs', 'Baruch', 'Sterin'),
    ('cbh', 'Christopher B.', 'Harris'),
    ('cg', 'Christian', 'Gorldt'),
    ('ch', 'Christoph', 'Hilken'),
    ('co', 'Christian', 'Otterstedt'),
    ('cr', 'Christopher D.', 'Rosebrock'),
    ('cw', 'Clemens', 'Werther'),
    ('df', 'Daniel', 'Florez'),
    ('dg', 'Daniel', 'Große'),
    ('dmm', 'D. Michael', 'Miller'),
    ('eg', 'Esther', 'Guerra'),
    ('ek', 'Eugen', 'Kuksa'),
    ('es', 'Eleonora', 'Schönborn'),
    ('et', 'Eleonora', 'Testa'),
    ('fc', 'Francky', 'Catthoor'),
    ('fh', 'Finn', 'Haedicke'),
    ('gdm', 'Giovanni', 'De Micheli'),
    ('gf', 'Görschwin', 'Fey'),
    ('gg', 'Guy', 'Gogniat'),
    ('gwd', 'Gerhard W.', 'Dueck'),
    ('gz', 'Grace', 'Zgheib'),
    ('hml', 'Hoang M.', 'Le'),
    ('hr', 'Heinz', 'Riener'),
    ('igh', 'Ian G.', 'Harris'),
    ('ik', 'Ina', 'Kodrasi'),
    ('jd', 'Jeroen', 'Demeyer'),
    ('jp', 'Judith', 'Peters'),
    ('jpd', 'Jean-Philippe', 'Diguet'),
    ('js', 'Julia', 'Seiter'),
    ('js2', 'Johanna', 'Sepulveda'),
    ('kdt', 'Klaus-Dieter', 'Thoben'),
    ('la', 'Luca Gaetano', 'Amarù'),
    ('lm', 'Lutz', 'Mädler'),
    ('lt', 'Laura', 'Tague'),
    ('ma', 'Matthew', 'Amy'),
    ('md', 'Melanie', 'Diepenbeck'),
    ('mf', 'Martin', 'Freibothe'),
    ('mg', 'Martin', 'Gogolla'),
    ('mk', 'Mirko', 'Kuhlmann'),
    ('mkt', 'Michael Kirkedal', 'Thomsen'),
    ('mm', 'Marc', 'Michael'),
    ('mmr', 'Md. Mazder', 'Rahman'),
    ('mn', 'Max', 'Nitze'),
    ('mr', 'Martin', 'Roetteler'),
    ('ms', 'Mathias', 'Soeken'),
    ('ms2', 'Matthias', 'Sauer'),
    ('na', 'Nabila', 'Abdessaied'),
    ('np', 'Nils', 'Przigoda'),
    ('nr', 'Norbert', 'Riefler'),
    ('nw', 'Nathan', 'Wiebe'),
    ('ok', 'Oliver', 'Keszocze'),
    ('oz', 'Odysseas', 'Zografos'),
    ('peg', 'Pierre-Emmanuel', 'Gaillardon'),
    ('pi', 'Paolo', 'Ienne'),
    ('pr', 'Pascal', 'Raiola'),
    ('pr2', 'Praveen', 'Raghavan'),
    ('pv', 'Patrick', 'Vuillod'),
    ('rkb', 'Robert K.', 'Brayton'),
    ('rkj', 'Robin Kaasgaard', 'Jensen'),
    ('rd', 'Rolf', 'Drechsler'),
    ('rl', 'Rudy', 'Lauwereins'),
    ('rw', 'Robert', 'Wille'),
    ('rxf', 'Reinhard X.', 'Fischer'),
    ('sf', 'Stefan', 'Frehse'),
    ('sim', 'Shin-ichi', 'Minato'),
    ('sr', 'Sandip', 'Ray'),
    ('ss', 'Saeideh', 'Shirinzadeh'),
    ('sw', 'Stefan', 'Wiesner'),
    ('tw', 'Thomas', 'Wriedt'),
    ('uk', 'Ulrich', 'Kühne'),
    ('wc', 'Wouter', 'Castryck'),
    ('wh', 'Winston', 'Haaswijk'),

    # -- chen related
    ('xt', 'Xifan', 'Tang'),
    ('yx', 'Yinshui', 'Xia'),
    ('zc', 'Zhufei', 'Chu'),
    ('zs', 'Zahra', 'Sasanian'),
    ('mc', 'Mingsong', 'Chen'),
    ('cx', 'Chenhao', 'Xie'),
    ('jt', 'Jingweijia', 'Tan'),
    ('yy', 'Yang', 'Yi'),
    ('yy2', 'Yun', 'Yang'),
    ('lp', 'Lu', 'Peng'),
    ('xf', 'Xin', 'Fu'),
    ('mh', 'Muhammad', 'Hassan'),
    ('vh', 'Vladimir', 'Herdt'),
    ('yb', 'Yongxiang', 'Bao'),
    ('qz', 'Qi', 'Zhu'),
    ('tw', 'Tongquan', 'Wei'),
    ('fm', 'Frederic', 'Mallet'),
    ('gp', 'Geguang', 'Pu'),
    ('my', 'Min', 'Yin'),
    ('jz', 'Junlong', 'Zhou'),
    ('zl', 'Zhifang', 'Li'),
    ('kc', 'Kun', 'Cao'),
    ('jy', 'Jianmin', 'Yan'),
    ('sx', 'Siyuan', 'Xu'),
    ('hz', 'Han', 'Zhuang'),
    ('sh', 'Saijie', 'Huang'),
    ('jh', 'Jifeng', 'He'),
    ('xl', 'Xiao', 'Liu'),
    ('ky', 'Kaige', 'Yan'),
    ('pl', 'Peng', 'Lu'),
    ('ym', 'Yue', 'Ma'),
    ('sh', 'Sharon', 'Hu'),
    ('xz', 'Xiqian', 'Zhang'),
    ('pm', 'Prabhat', 'Mishra'),
    ('xq', 'Xiaoke', 'Qin'),
    ('zw', 'Zheng', 'Wang'),
    ('jl', 'Jianwen', 'Li'),
    ('yc', 'Yuxiang', 'Chen'),
    ('yz', 'Yongxin', 'Zhao'),
    ('yz2', 'Ying', 'Zhang'),
    ('bg', 'Bin', 'Gu'),
    ('dk', 'Dhrubajyoti', 'Kalita'),
    ('wx', 'Wei', 'Xu'),
    ('lw', 'Linzhang', 'Wang'),
    ('xs', 'X', 'Sharon'),
    ('jc', 'Jianfei', 'Chen'),
    ('sx', 'Siyuan', 'Xu'),
    ('wm', 'Weikai', 'Miao'),
    ('tk', 'Thomas', 'Kunz'),
    ('yw', 'Yuanyang', 'Wang'),
    ('xc', 'Xiaohong', 'Chen'),
    ('hs', 'Haiying', 'Sun'),
    ('mz', 'Min', 'Zhang'),
    ('fg', 'Fan', 'Gu'),
    ('dd', 'Dehui', 'Du'),
    ('dy', 'Daian', 'Yue'),
    ('ys', 'Yan', 'Shen'),
    ('jl', 'Jianwen', 'Li'),
    ('ts', 'Ting', 'Su'),
    ('bf', 'Bin', 'Fang'),
    ('wl', 'Wanwei', 'Liu'),
    ('al', 'Ang', 'Li'),
    ('zq', 'Zishan', 'Qin'),
    ('lz', 'Lei', 'Zhou'),
    ('zs', 'Zhucheng', 'Shao'),
    ('zd', 'Zuohua', 'Ding'),
    ('nj', 'Ningkang', 'Jiang'),
    ('zw', 'Zhike', 'Wu'),
    ('jk', 'Jeeyoung', 'Kim'),
    ('yd', 'Yi', 'Du'),
    ('ah', 'Ahmed', 'Helmy'),
    ('xq', 'Xiaokang', 'Qiu'),
    ('xl', 'Xuandong', 'Li'),

    # zhongwen

    ('cms', '陈铭松', ''),
    ('byx', '鲍勇翔', ''),
    ('shy', '孙海英', ''),
    ('mwk', '缪炜恺', ''),
    ('cxh', '陈小红', ''),
    ('ztl', '周庭梁', ''),
    ('gf', '顾璠', ''),
    ('xsy', '徐思远', ''),
    ('qzs', '覃子姗', ''),
    ('qxk', '秦晓科', ''),
    ('hsj', '黄赛杰', ''),
    ('la', '李昂', ''),
    ('zjh', '赵建华', ''),
    ('lxd', '李宣东', ''),
    ('zgl', '郑国梁', ''),
    ('qxk', '邱晓康', ''),
    ('wlz', '王林章', ''),

]

# (作者，会议，年，论文名，页，网址)
confpapers_data = [
    (['mc', 'xq', 'xl', 'ah'], 'ast', 2006,
     'Automatic Test Case Generation for UML Activity Diagrams',
     '2--8',
     'https://doi.org/10.1145/1138929.1138931',
     'http://faculty.ecnu.edu.cn/picture/article/223/ba/43/8ee536044cdcb84b6880d2523a87/f5667a8a-7938-450b-beef-94dd36a71778.rar'),

    (['jk', 'yd', 'mc', 'ah'], 'crwadad', 2007,
     'Comparing Mobility and Predictability of VoIP and WLAN Traces',
     'XXXX',
     'http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.121.8570&rep=rep1&type=pdf','','http://faculty.ecnu.edu.cn/picture/article/223/ba/43/8ee536044cdcb84b6880d2523a87/61efeb27-a145-4328-9cdc-97287d1b4bb9.ppt'),

    (['mc', 'pm'], 'hldvt', 2007,
     'Coverage-driven Automatic Test Generation for UML Activity Diagrams',
     'XXXX',
     'https://doi.org/10.1109/HLDVT.2007.4392793'),

    (['mc', 'pm'], 'glsvlsi', 2008,
     'Coverage-driven Automatic Test Generation for UML Activity Diagrams',
     'XXXX',
     'https://doi.org/10.1145/1366110.1366145','','http://url.cn/PI3pcA'),

    (['pm', 'mc'], 'vlsid', 2010,
     'Efficient Techniques for Directed Test Generation using Incremental Satisfiability',
     'XXXX',
     'https://doi.org/10.1109/VLSI.Design.2009.72','','http://faculty.ecnu.edu.cn/picture/article/223/ba/43/8ee536044cdcb84b6880d2523a87/ecdaaa73-e073-4a50-965b-5143b0f665a8.pdf','Nominated for best paper award'),

    (['mc', 'xq', 'pm'], 'date', 2010,
     'Efficient Decision Ordering Techniques for SAT-based Test Generation',
     '490--495',
     'http://ieeexplore.ieee.org/document/5457156/','','http://faculty.ecnu.edu.cn/picture/article/223/0f/fc/cd8d371743b59b0f34e9224771fa/3404b9b2-ac5c-449e-9060-676da5c97687.pdf'),

    (['mc'], 'dac', 2010,
     'Efficient Approaches For Functional Validation of SOC Designs Using High-Level Specifications',
     'XXXX',
     'esl.cise.ufl.edu/Publications/chenThesis.pdf'),

    (['mc', 'pm'], 'date', 2011,
     'Decision Ordering Based Property Decomposition for  Functional Test Generation',
     'XXXX',
     'https://doi.org/10.1109/DATE.2011.5763037','','http://faculty.ecnu.edu.cn/picture/article/223/ba/43/8ee536044cdcb84b6880d2523a87/5a05a639-4caf-437e-b982-a92777d20b7c.pdf'),

    (['zw', 'jl', 'xc', 'mc'], 'apsi', 2012,
     'An approach to communicating process modeling of MARTE',
     'XXXX',
     'https://doi.org/10.1145/2430475.2430481'),

    (['xc', 'mc'], 'isorc', 2012,
     'Extending the Four-Variable Model forCyber-Physical Systems',
     '31--36',
     'https://doi.org/10.1109/ISORCW.2012.16'),

    (['al', 'mc'], 'codes', 2012,
     'Efficient Self-learning Techniques for SAT-based Test Generation',
     'XXXX',
     'dl.acm.org/ft_gateway.cfm?id=2380480','','http://faculty.ecnu.edu.cn/picture/article/223/ba/43/8ee536044cdcb84b6880d2523a87/4b241d03-97aa-45b0-9499-3f9788948c92.pdf'),

    (['mc', 'pm'], 'vlsid', 2013,
     'Assertion-Based Functional Consistency Checking between TLM and RTL Models',
     'XXXX',
     'https://doi.org/10.1109/VLSID.2013.208','','http://faculty.ecnu.edu.cn/picture/article/223/ba/43/8ee536044cdcb84b6880d2523a87/036e0ba2-e29d-4b84-9bec-9d6f7f6a5535.pdf','Nominated for best paper award'),

    (['mc', 'sh', 'gp', 'pm'], 'isvlsi', 2013,
     'Branch-and-Bound Style Resource Constrained Scheduling using Efficient Structure-Aware Pruning',
     'XXXX',
     'https://doi.org/10.1109/ISVLSI.2013.6654637','','http://faculty.ecnu.edu.cn/picture/article/223/ba/43/8ee536044cdcb84b6880d2523a87/53211603-e3c2-43f2-ae01-7b72bb29d810.pdf'),

    (['mc', 'lz', 'gp', 'jh'], 'codes', 2013,
     'Bound-Oriented Parallel Pruning Approaches for Efficient Resource Constrained Scheduling of High-Level Synthesis',
     'XXXX',
     'https://doi.org/10.1109/CODES-ISSS.2013.6659001','','http://faculty.ecnu.edu.cn/picture/article/223/ba/43/8ee536044cdcb84b6880d2523a87/51f4b12b-ebb5-4e49-a8c3-55f44139a5cb.pdf'),

    (['zs', 'jl', 'zd', 'mc', 'nj'], 'iceccs', 2013,
     'Spatio-temporal Properties Analysis for Cyber-physical Systems',
     'XXXX',
     'https://doi.org/10.1109/ICECCS.2013.23'),

    (['mc', 'fg', 'lz', 'gp', 'xl'], 'vlsid', 2014,
     'Efficient Two-Phase Approaches for Branch-and-Bound Style Resource Constrained Scheduling Efficient',
     'XXXX',
     '','','http://faculty.ecnu.edu.cn/picture/article/223/ba/43/8ee536044cdcb84b6880d2523a87/9c280848-3e9a-40d9-8ba5-66f1ddf6cbef.pdf'),

    (['dd', 'mc', 'xl', 'yy2', 'xc'], 'icse', 2014,
     'A Novel Quantitative Evaluation Approach for Software Project Schedules using Statistical Model Checking',
     'XXXX',
     'http://dl.acm.org/citation.cfm?id=2591132'),

    (['al', 'zq', 'mc', 'jl', 'xc'], 'sere', 2014,
     'ADAutomation: An Activity Diagram Based Automated GUI Testing Framework for Smartphone Applications',
     'XXXX',
     'https://doi.org/10.1109/SERE.2014.20','','http://faculty.ecnu.edu.cn/picture/article/223/f4/3a/b11e4543409491a99e97f90be516/31cd2d8b-ce80-48cd-9e37-839b565ba904.pdf'),

    (['sh', 'mc', 'xl', 'dd', 'xc'], 'bdcloud', 2014,
     'Variation-Aware Resource Allocation Evaluation for Cloud Workflows using Statistical Model Checking',
     'XXXX',
     'https://doi.org/10.1109/BDCloud.2014.48','','http://faculty.ecnu.edu.cn/picture/article/223/17/51/7bca511b46d1ab73ceade591c329/b8fa9311-a2bb-4b4f-83de-02c6c12f95fe.pdf'),

    (['ys', 'jl', 'zw', 'ts', 'bf', 'gp', 'wl', 'mc'], 'apsec', 2014,
     'Runtime Verification by Convergent Formula Progression',
     '255--262',
     'https://doi.org/10.1109/APSEC.2014.47'),

    (['mc', 'dy', 'xq', 'xf', 'pm', 'hs'], 'date', 2015,
     'Variation-Aware Evaluation for MPSoC Task Allocation and Scheduling Strategies using Statistical Model Checking',
     'XXXX',
     'http://ieeexplore.ieee.org/document/7092382/',
     'http://faculty.ecnu.edu.cn/picture/article/223/e4/c6/7cf181a9488dbd16c5f51eae710a/951f8cc1-119d-4f5e-ba9c-d1073d0ae63d.zip','http://faculty.ecnu.edu.cn/picture/article/223/f4/3a/b11e4543409491a99e97f90be516/af0abfa3-24f2-4da7-83c3-7505d8befcf5.pdf'),

    (['xc', 'fg', 'mc', 'dd', 'jl', 'hs'], 'compsac', 2015,
     'Evaluating Energy Consumption for Cyber-Physical Energy System: an Environment Ontology based Approach',
     'XXXX',
     'https://doi.org/10.1109/COMPSAC.2015.114'),

    (['fg', 'xz', 'mc', 'dg', 'rd'], 'date', 2016,
     'Timing Analysis of UML Activity Diagrams Using Statistical Model',
     'XXXX',
     'http://ieeexplore.ieee.org/document/7459412/','','http://faculty.ecnu.edu.cn/picture/article/223/26/09/5707756f4e08bafdae11a0de24d0/38e7366f-0e61-42df-afd1-6d895aa171a2.pdf'),

    (['hs', 'mc', 'mz', 'jl', 'yz2'], 'compsac', 2016,
     'improving Defect Detection Ability of Derived Test Cases Based on Mutated UML Activity Diagrams',
     'XXXX',
     'https://doi.org/10.1109/COMPSAC.2016.136'),

    (['yw', 'xc', 'hs', 'mc'], 'seke', 2016,
     'Choosing the Best Strategy for Energy Aware Building System: an SVM-based Approach',
     'XXXX',
     ''),

    (['sx', 'wm', 'tk', 'tw', 'mc'], 'qrs', 2016,
     'Quantitative Analysis of Variation-Aware Internet of Things Designs using Statistical Model Checking',
     '274--285',
     'https://doi.org/10.1109/QRS.2016.39'),

    (['jz', 'jc', 'kc', 'tw', 'mc'], 'icpads', 2016,
     'Game Theoretic Energy Allocation for Renewable Powered In-Situ Server Systems',
     'XXXX',
     'https://doi.org/10.1109/ISSSR.2016.026'),

    (['kc', 'jz', 'my', 'tw', 'mc'], 'isssr', 2016,
     'Static Thermal-Aware Task Assignment and Scheduling for Makespan Minimization in Heterogeneous Real-time MPSoCs',
     'XXXX',
     'https://doi.org/10.1109/ISSSR.2016.026'),

    (['jz', 'jy', 'tw', 'mc', 'xs'], 'date', 2017,
     'Energy-Adaptive Scheduling of Imprecise Computation Tasks for QoS Optimization in Real-Time MPSoC', 'XXXX',
     'https://www.researchgate.net/publication/310330767_Energy-Adaptive_Scheduling_of_Imprecise_Computation_Tasks_for_QoS_Optimization_in_Real-Time_MPSoC_Systems'),

    (['mh', 'vh', 'hml', 'mc', 'dg', 'rd'], 'date', 2017,
     'Data flow testing for virtual prototypes', 'XXXX',
     'http://dl.acm.org/citation.cfm?id=2818868'),

]

workpapers_data = [
    (['ms', 'rw', 'mk', 'mg', 'rd'], 'mbmv', 2010, 'Verifying UML/OCL models using Boolean satisfiability', '57--66',
     ''),
    (['ms', 'rw', 'rd'], 'rcw', 2010,
     'Hierachical synthesis of reversible circuits using positive and negative Davio decomposition', '55--58', ''),
    (['ms', 'sf', 'rw', 'rd'], 'rcw', 2010, 'RevKit: A toolkit for reversible circuit design', '69-72', ''),
    (['ms', 'uk', 'mf', 'gf', 'rd'], 'mbmv', 2011,
     'Towards automatic property generation for the formal verification of bus bridges', '183--192', ''),
    (['rw', 'ms', 'dg', 'es', 'rd'], 'mbmv', 2011, 'Designing a RISC CPU in reversible logic', '249--258', ''),
    (['ms', 'sf', 'rw', 'rd'], 'rcw', 2011, 'Customized design flows for reversible circuits using RevKit', '91--96',
     ''),
    (['ms', 'rw', 'np', 'ch', 'rd'], 'rcw', 2011,
     'Synthesis of reversible circuits with minimal lines for large functions', '59--70', ''),
    (
        ['ms', 'rw', 'lt', 'dmm', 'rd'], 'iwsbp', 2012, 'Towards embedding of large functions for reversible logic',
        'XXXX',
        ''),
    (['ms', 'hr', 'rw', 'gf', 'rd'], 'mecoes', 2012,
     'Verification of embedded systems using modeling and implementation languages', '67--72', ''),
    (['ms', 'rw', 'ek', 'rd'], 'mbmv', 2013, 'Generierung von OCL-Ausdrücken aus natürlichsprachlichen Beschreibungen',
     '99-103', ''),
    (['ok', 'ms', 'ek', 'rd'], 'naturalise', 2013,
     'lips: An IDE for model driven engineering based on natural language processing', 'XXXX', ''),
    (['rd', 'hml', 'ms', 'rw'], 'sec', 2013, 'Law-based verification of complex swarm systems', 'XXXX', ''),
    (['ms', 'mn', 'rd'], 'mbmv', 2014, 'Formale Methoden für Alle', '213--216', ''),
    (['js', 'mm', 'ms', 'rw', 'rd'], 'duhde', 2014,
     'Towards a multi-dimensional and dynamic visualization for ESL designs', 'XXXX', ''),
    (['ms', 'na', 'rd'], 'iwsbp', 2014, 'A framework for reversible circuit complexity', 'XXXX', ''),
    (['rd', 'js', 'ms'], 'difts', 2014, 'Coverage at the formal specification level', 'XXXX', ''),
    (['ms', 'mkt', 'gwd', 'dmm'], 'rm', 2015, 'Self-inverse functions and palindromic circuits', 'XXXX', ''),
    (['bs', 'ms', 'rd', 'rkb'], 'iwls', 2015, 'Simulation graphs for reverse engineering', 'XXXX', ''),
    (['ac2', 'dg', 'ms', 'rd'], 'mbmv', 2016, 'Symbolic error metric determination for approximate computing', '75--76',
     ''),
    (['ap', 'am', 'ms', 'gdm', 'rkb', 'pi'], 'iwls', 2016,
     'Fast generation of lexicographic satisfiable assignments: enabling canonicity in SAT-based applications', 'XXXX',
     ''),
    (['et', 'ms', 'la', 'peg', 'gdm'], 'iwls', 2016, 'Inversion minimization in majority-inverter graphs', 'XXXX', ''),
    (['ms', 'pr', 'bs', 'ms2'], 'iwls', 2016, 'SAT-based functional dependency computation', 'XXXX', ''),
    (
        ['wh', 'ms', 'la', 'peg', 'gdm'], 'iwls', 2016, 'LUT mapping and optimization for majority-inverter graphs',
        'XXXX',
        ''),
    (['ok', 'ms', 'rd'], 'iwsbp', 2016, 'On the computational complexity of error metrics in approximate computing',
     'XXXX', ''),
    (['ms', 'ik', 'gdm'], 'rm', 2017, 'Boolean function classification with δ-swaps', 'XXXX', '')
]

# (作者，会议，卷，号，年，论文名，页，网址)
article_data = [

    (['cms', 'zjh', 'lxd', 'zgl'], 'jsjkx', 33, "06", 2006,
     '时间自动机可达性分析中的状态空间约减技术综述',
     '1-7',
     'http://www.jsjkx.com/jsjkx/ch/reader/view_abstract.aspx?file_no=22086624'),

    (['qxk', 'cms', 'wlz', 'lxd', 'zgl'], 'jsjkx', 34, "12", 2007,
     '行为图驱动的Java程序运行时验证工具',
     '273-277',
     'http://www.jsjkx.com/jsjkx/ch/reader/view_abstract.aspx?file_no=26159129'),

    (['cms', 'zjh', 'lxd', 'zgl'], 'jsjkx', 34, "01", 2007,
     '一种动态消减时间自动机可达性搜索空间的方法',
     '213-218',
     'http://www.jsjkx.com/jsjkx/ch/reader/view_abstract.aspx?file_no=23655161'),

    (['mc', 'xq', 'wx', 'lw', 'jz', 'xl'], 'tcj', 52, "5", 2009,
     'UML Activity Diagram Based Automatic Test Case Generation for Java Programs',
     '545-556', 'https://doi.org/10.1093/comjnl/bxm057'),

    (['mc', 'pm'], 'tcad', 29, "3", 2010,
     ' Efficient SAT-based Test Generation using Property Clustering',
     '396-404', 'https://doi.org/10.1109/TCAD.2010.2041846'),

    (['mc', 'pm', 'dk'], 'todaes', 14, "2", 2010,
     'Efficient test case generation for validation of UML activity diagrams',
     '852-864', 'https://doi.org/10.1007/s10617-010-9052-4'),

    (['mc', 'pm'], 'tc', 60, "6", 2011,
     'Property Learning Techniques for Efficient Generation of Directed Tests',
     '852-864', 'https://doi.org/10.1109/TC.2011.49'),

    (['mc', 'pm'], 'tecs', 11, "2", 2012,
     'Automaitc RTL Test Generation from SystemC TLM Specifications',
     '38', 'https://doi.org/10.1145/2220336.2220350'),

    (['cms', 'hsj', 'la'], 'zgjsjxhtx', 9, "7", 2013,
     'CPS研究热点概述',
     '8-16',
     'http://faculty.ecnu.edu.cn/picture/article/223/ba/43/8ee536044cdcb84b6880d2523a87/4ca46f15-0367-4385-922e-c60520bb4df1.pdf'),

    (['zw', 'gp', 'jl', 'yc', 'yz', 'mc', 'bg', 'jh'], 'fcsc', 7, "4", 2013,
     'An Approach to Requirement Anaysis for Periodic Control Systems',
     '214-235', 'https://doi.org/10.1007/s11704-013-2008-1'),

    (['qzs', 'gf', 'qxk', 'cms'], 'ceaj', 8, "5", 2014,
     '基于GPU平台的有效字典压缩与解压缩技术',
     '525-536', 'http://fcst.ceaj.org/CN/article/downloadArticleFile.do?attachType=PDF&id=758'),

    (['mc', 'xq', 'pm'], 'jetta', 30, "3", 2014,
     'Efficient Learning-Oriented Property Decomposition  for Automated Generation of Directed Tests',
     '287-306', 'http://dx.doi.org/10.1007/s10836-014-5452-x'),

    (['cms', 'gf', 'xsy', 'cxh', 'ztl'], 'jos', 27, "3", 2016,
     '不确定环境下基于价格时间自动机的智能大厦空调系统调度策略评估',
     '655-669', 'http://www.jos.org.cn/ch/reader/create_pdf.aspx?file_no=4987&journal_id=jos'),

    (['mc', 'xz', 'gp', 'xf', 'pm'], 'tc', 65, "7", 2016,
     'Efficient Resource Constrained Scheduling using Parallel Structure Aware Pruning Techniques',
     '2059-2073', 'https://doi.org/10.1109/TC.2015.2468230',
     'http://faculty.ecnu.edu.cn/picture/article/223/f5/4f/41df00854e5594ce6636ce5b54d1/4a529336-0ff0-4237-a18d-63d9adb9473e.zip','http://faculty.ecnu.edu.cn/picture/article/223/0f/00/8d408c514ec4817d4124d11d27fc/068b8e6b-dcc9-4440-94d1-33d883e31099.zip'),

    (['jt', 'zl', 'mc', 'xf'], 'tpds', 21, "2", 2016,
     'Exploring Soft-Error Robust and Energy-Efficient Register File in GPGPUs using Resistive Memory',
     '34', 'https://doi.org/10.1145/2827697'),

    (['jz', 'tw', 'mc', 'ym', 'sh'], 'tcad', 35, "8", 2016,
     'Thermal-Aware Task Scheduling for Energy Minimization in Heterogeneous Real-Time MPSoC Systems',
     '1269-1282', 'https://doi.org/10.1109/TCAD.2015.2501286'),

    (['jt', 'mc', 'yy', 'xf'], 'tpds', 27, "11", 2016,
     'Mitigating the Impact of Hardware Variability for GPGPUs Register File',
     '3283-3297', 'https://doi.org/10.1109/TPDS.2016.2531668'),

    (['cms', 'byx', 'shy', 'mwk', 'cxh', 'ztl'], 'jos', 28, "5", 2017,
     '基于通信的列车控制系统可信构造：形式化方法研究',
     '1183-1203', ' http://www.jos.org.cn/1000-9825/5217.htm'),

    (['ky', 'pl', 'mc', 'xf'], 'todaes', -1, "", 0,
     ' Exploring Energy-Efficient Cache Design in Emerging Mobile Platforms',
     'XXXX', ''),

    (['mc', 'xf', 'sh', 'xl', 'jh'], 'tcc', -1, "", 0,
     'Statistical Model Checking-Based Evaluation and Optimization forCloud Workflow Resource Allocation',
     'XXXX', 'https://doi.org/10.1109/TCC.2016.2586067'),


    (['sx', 'hz', 'xf', 'zl', 'mc'], 'jcsc', -1, "", 0,
     ' GPU-Based Fluid Motion Estimation using Energy Constrain',
     'XXXX', 'http://dx.doi.org/10.1142/S0218126617500220'),

    (['my', 'jz', 'zl', 'kc', 'jy', 'tw', 'mc', 'xf'], 'jcsc', -1, "", 0,
     'Fault-Tolerant Task Scheduling for Mixed-Criticality Real-TimeSystems',

     'XXXX', 'http://dx.doi.org/10.1142/S0218126617500165'),
    (['cx', 'jt', 'mc', 'yy', 'lp', 'xf'], 'jmm', -1, "", 0,
     'Emerging technology enabled energy-efficient gpgpus register file', 'XXXX',
     'http://doi.org/10.1016/j.micpro.2017.04.002'),

    (['yb', 'mc', 'qz', 'tw', 'fm'], 'tcad', -1, "", 0,
     'Quantitative Performance Evaluation of Uncertainty-Aware Hybrid AADL Designs Using Statistical Model Checking',
     'XXXX', 'https://doi.org/10.1109/TCAD.2017.2681076', 'https://github.com/tony11231/aadl2uppaal'),

    (['mc', 'xf', 'gp', 'tw'], 'tpds', -1, "", 0,
     'Efficient Resource Constrained Scheduling using Parallel Two-Phase Branch-and-Bound Heuristics',
     'XXXX', 'https://doi.org/10.1109/TPDS.2016.2621768',
     'http://faculty.ecnu.edu.cn/picture/article/223/26/c1/e0470b9e49a4898a8f5ac9d1f684/05ae9b2d-c416-4d12-8baf-08233db7d3fc.zip','http://faculty.ecnu.edu.cn/picture/article/223/26/c1/e0470b9e49a4898a8f5ac9d1f684/69187182-6aa0-4cd2-96b8-5cf3079664e6.zip'),

]

preprint_data = [
    (['ms', 'dmm', 'rd'], '1308.2493', 'On quantum circuits employing roots of the Pauli matrices', '7 pages, 1 figure',
     'j3', ['quant-ph', 'cs.ET']),
    (['ms', 'na', 'rd'], '1407.5878', 'A framework for reversible circuit complexity',
     "6 pages, 4 figures, accepted for Int'l Workshop on Boolean Problems 2014", '', ['cs.ET', 'quant-ph']),
    (['ms', 'rw', 'ok', 'dmm', 'rd'], '1408.3586', 'Embedding of large Boolean functions for reversible logic',
     '13 pages, 10 figures', 'j7', ['cs.ET']),
    (['ms', 'lt', 'gwd', 'rd'], '1408.3955',
     'Ancilla-free synthesis of large reversible functions using binary decision diagrams', '25 pages, 15 figures',
     'j8', ['cs.ET', 'quant-ph']),
    (['ms', 'mkt', 'gwd', 'dmm'], '1502.05825', 'Self-inverse functions and palindromic circuits', '6 pages, 3 figures',
     '', ['cs.ET', 'math.GR', 'quant-ph']),
    (['wc', 'jd', 'adv', 'ok', 'ms'], '1503.08579', 'Translating between the roots of identity in quantum circuits',
     '7 pages', '', ['quant-ph', 'math.GR']),
    (['ms', 'mr', 'nw', 'gdm'], '1612.00631', 'Design automation and design space exploration for quantum computers',
     '6 pages, 1 figure', 'c81', ['quant-ph', 'cs.ET'])
]

best_paper_data = [('2016_date_1', 'c'), ('2016_sat', 'c')]

news_data = [
    ('jcsc', -1),
    ('jmm', -1),
    ('tcad', -1),
    ('date', 2017),
    ('tpds', -1),

]

authors = make_dict('key', authors_data, make_author)
conferences = make_dict('key', conferences_data, make_conference)
journals = make_dict('key', journals_data, make_journal)

confpapers = list(map(make_conference_paper, confpapers_data))
workpapers = list(map(make_conference_paper, workpapers_data))
articles = list(map(make_article, article_data))
preprints = list(map(make_preprint, preprint_data))

news = list(map(make_news, news_data))

universities_data = [
    ('birs', 'Banff International Research Station', 'Banff, AL', 'Canada', 'http://www.birs.ca', ''),
    ('epfl', 'EPFL', 'Lausanne', 'Switzerland', 'http://epfl.ch', 'École Polytechnique Fédérale de Lausanne'),
    ('hu', 'Hokkaido University', 'Sapporo', 'Japan', 'https://www.oia.hokudai.ac.jp', '北海道大学'),
    ('rwth', 'RWTH Aachen University', 'Aachen', 'Germany', 'http://www.rwth-aachen.de', 'RWTH Aachen'),
    ('ru', 'Ritsumeikan University', 'Kyoto', 'Japan', 'http://en.ritsumei.ac.jp', '立命館大学'),
    ('sri', 'SRI International', 'Menlo Park, CA', 'USA', 'https://www.sri.com', ''),
    ('su', 'Stanford University', 'Stanford, CA', 'USA', 'http://stanford.edu', ''),
    ('unb', 'University of New Brunswick', 'Fredericton, NB', 'Canada', 'http://www.unb.ca', ''),
    ('msr', 'Microsoft Research', 'Redmond, WA', 'USA', 'https://www.microsoft.com/en-us/research/', ''),
    ('snps', 'Synopsys', 'Sunnyvale, CA', 'USA', 'http://www.synopsys.com/', '')
]

universities = make_dict('key', universities_data, make_university)

invited_data = [
    (2011, 'jan', 'uni', 'hu', 'Prof. Shin-ichi Minato', 'Formal verification of UML-based specifications',
     'http://www-erato.ist.hokudai.ac.jp/wiki/wiki.cgi?page=ERATO-seminar'),
    (2012, 'apr', 'conf', 'cukeup', '', 'BDD for embedded system design',
     'https://skillsmatter.com/skillscasts/3124-bdd-for-embedded-system-design'),
    (2013, 'jan', 'uni', 'hu', 'Prof. Shin-ichi Minato',
     'Synthesis of reversible circuits with minimal lines for large functions', ''),
    (2013, 'apr', 'conf', 'cukeup', '', 'Towards automatic scenario generation based on uncovered code',
     'https://skillsmatter.com/skillscasts/4043-towards-automatic-scenario-generation-based-on-uncovered-code'),
    (2014, 'apr', 'uni', 'su', 'Prof. Subhasish Mitra', 'Formal specification level', ''),
    (2014, '', 'uni', 'rwth', 'Prof. Anupam Chattopadhyay', 'Implementing synthesis flows with RevKit', ''),
    (2014, 'may', 'uni', 'ru', 'Prof. Shigeru Yamashita', 'Formal specification level', ''),
    (2014, 'oct', 'uni', 'unb', 'Prof. Gerhard W. Dueck', 'Formal specification level',
     'http://www.cs.unb.ca/seminarseries/documents/Mathias_Soeken-10.29.14.pdf'),
    (2014, 'dec', 'uni', 'sri', 'Dr. Wenchao Li', 'Reverse engineering', ''),
    (2015, 'may', 'conf', 'rm', '', 'Generalized equivalence checking problems for reverse engineering',
     'http://lyle.smu.edu/RM2015/program.htm'),
    (2015, 'jun', 'uni', 'epfl', 'Prof. Paolo Ienne', 'Reverse engineering with simulation graphs', ''),
    (2016, 'apr', 'uni', 'birs', 'Dr. Martin Roetteler',
     'Ancilla-free reversible logic synthesis using symbolic methods',
     'http://www.birs.ca/events/2016/5-day-workshops/16w5029/videos/watch/201604181552-Soeken.html'),
    (2016, 'may', 'uni', 'hu', 'Prof. Shin-ichi Minato',
     'Ancilla-free reversible logic synthesis using symbolic methods',
     'http://www-erato.ist.hokudai.ac.jp/html/php/seminar.php?day=20160517'),
    (2016, 'sep', 'uni', 'msr', 'Dr. Martin Roetteler and Dr. Nathan Wiebe',
     'Symbolic and hierarchical reversible logic synthesis', ''),
    (2016, 'nov', 'uni', 'snps', 'Dr. Luca Amarù', 'SAT-based logic synthesis', ''),
    (2017, 'feb', 'uni', 'msr', 'Dr. Martin Roetteler and Dr. Nathan Wiebe',
     'LUT-based hierarchical reversible logic synthesis', '')
]

invited = list(map(make_invited, invited_data))


def cmd_publications():
    for key, conf in conferences.items():
        if len(conf['shortname']) > 0:
            print("@STRING{%s = {%s}}" % (conf['shortname'], conf['name']))
    print()

    print("@book{book1,")
    print("  editor    = {Rolf Drechsler and Mathias Soeken and Robert Wille},")
    print("  title     = {Auf dem Weg zum Quantencomputer: Entwurf reversibler Logik (Technische Informatik)},")
    print("  publisher = {Shaker},")
    print("  year      = 2012")
    print("}")
    print()
    print("@book{book2,")
    print("  author    = {Mathias Soeken and Rolf Drechsler},")
    print("  title     = {Formal Specification Level},")
    print("  publisher = {Springer},")
    print("  year      = 2014")
    print("}")
    print()
    print("@incollection{inc1,")
    print("  author    = {Rolf Drechsler and Mathias Soeken and Robert Wille},")
    print("  title     = {Formal specification level},")
    print("  editor    = {Jan Haase},")
    print("  booktitle = {Models, Methods, and Tools for Complex Chip Design: Selected Contributions from FDL 2012},")
    print("  publisher = {Springer},")
    print("  year      = 2014")
    print("}")
    print()
    print("@incollection{inc2,")
    print("  author    = {Mathias Soeken},")
    print("  title     = {Formale {Spezifikationsebene}},")
    print("  editor    = {S. H{\\\"o}lldobler and others},")
    print("  booktitle = {Ausgezeichnete Informatikdissertationen 2013},")
    print("  publisher = {GI},")
    print("  year      = 2014")
    print("}")
    print()
    print("@incollection{inc3,")
    print("  author    = {Mathias Soeken and Nabila Abdessaied and Rolf Drechsler},")
    print("  title     = {A framework for reversible circuit complexity},")
    print("  editor    = {Bernd Steinbach},")
    print("  booktitle = {Problems and New Solutions in the Boolean Domain},")
    print("  publisher = {Cambridge Scholars Publishing},")
    print("  pages     = {327--341},")
    print("  year      = 2016")
    print("}")
    print()

    for a in articles:
        format_bibtex_article(a)
        print()

    for c in confpapers:
        format_bibtex_incollection(c, confpapers, "conference")
        print()

    for w in workpapers:
        format_bibtex_incollection(w, workpapers, "workshop")

    for p in preprints:
        format_bibtex_preprint(p)

    write_publications()


def cmd_haml():
    year = ""
    for index, c in enumerate(reversed(confpapers)):
        if c['year'] != year:
            year = c['year']
            print("%%h4 %s" % year)
        format_haml_incollection(c, len(confpapers) - index)


def cmd_haml_work():
    print(
        "%p These workshop papers are peer-reviewed and have been presented at events, where the proceedings where distributed only among the participants.  If you are interested in one of the listed papers, please send me an eMail and I am happy to share the PDF.")
    year = ""
    for index, c in enumerate(reversed(workpapers)):
        if c['year'] != year:
            year = c['year']
            print("%%h4 %s" % year)
        format_haml_incollection_work(c, len(workpapers) - index)


def cmd_haml_article():
    year = ""
    for index, c in enumerate(reversed(articles)):
        if c['year'] != year:
            year = c['year']
            print("%%h4 %s" % ("In press" if year == 0 else year))
        format_haml_article(c, len(articles) - index)


def cmd_haml_preprint():
    for index, c in enumerate(reversed(preprints)):
        format_haml_preprint(c, len(preprints) - index)


def cmd_haml_news():
    for n in reversed(news):
        format_haml_news(n)


def cmd_haml_invited():
    year = ""
    for n in reversed(invited):
        if n['year'] != year:
            year = n['year']
            print("%%h4 %s" % year)
        format_haml_invited(n)


def cmd_stats():
    num_countries = len(set([p['conf']['venues'][p['year']]['country'] for p in confpapers]))
    print("%d authors, %d conference papers, in %d countries" % (len(authors), len(confpapers), num_countries))


def cmd_pdfs():
    for c in confpapers:
        filename = make_filename(c, confpapers)

        if os.path.exists("papers/%s.pdf" % filename):
            if not os.path.exists("images/thumbs/%s.png" % filename):
                print("[i] creating thumbnail for \"%s\" (%s %d)" % (c['title'], c['conf']['shortname'], c['year']))
                os.system("convert papers/%s.pdf /tmp/%s.png" % (filename, filename))
                os.system("convert -trim -resize x130 /tmp/%s-0.png images/thumbs/%s.png" % (filename, filename))
        else:
            print("[w] no PDF for \"%s\" (%s %d)" % (c['title'], c['conf']['shortname'], c['year']))


def cmd_geo():
    from geopy.geocoders import Nominatim
    locator = Nominatim()
    for k1, d in conferences.items():
        for k2, v in d['venues'].items():
            location = "%s, %s" % (v['city'], v['country'])
            l = locator.geocode(location)
            if l:
                print("  {title: '%s', position: {lat: %s, lng: %s}}," % (location, l.latitude, l.longitude))
            else:
                print("No geocode for %s" % v)


if len(sys.argv) == 2:
    globals()['cmd_%s' % sys.argv[1]]()
