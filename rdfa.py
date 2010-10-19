#!/usr/bin/env python

"""
Converts the MulDiCat rdf/xml file to xhtml/rdfa

  % rdfa.py MulDiCat.rdf > MulDiCat.html

"""

import sys
import urlparse

import rdflib
import lxml.etree as et

from rdfize import muldicat, SKOS, DCT, languages
from rdflib.namespace import RDF

ns = {
    None:       "http://www.w3.org/1999/xhtml", 
    "dcterms":  DCT, 
    "skos":     SKOS
}


def convert(rdfxml):
    graph = rdflib.Graph()
    graph.parse(rdfxml)

    html = et.Element("html", nsmap=ns)
    add_description(graph, html)
    add_tables(graph, html)
    print '<?xml version="1.0" encoding="UTF-8"?>'
    print et.tostring(html, pretty_print=True, encoding=unicode).encode(
            'utf-8')


def add_description(graph, html):
    head = et.SubElement(html, "head")
    title = et.SubElement(head, "title")
    title.text = graph.value(muldicat, DCT.title)
    link = et.SubElement(head, "link", {"rel": "stylesheet", 
                                        "type": "text/css", 
                                        "href": "style.css"})

    body = et.SubElement(html, "body")
    desc = et.SubElement(body, "p", {"id": "concept_scheme", 
                                     "about": muldicat})

    h1 = et.SubElement(desc, "h1", {"property": "dcterms:title"})
    h1.text = graph.value(muldicat, DCT.title)

    d = et.fromstring(graph.value(muldicat, DCT.description))
    d.attrib["property"] = "dcterms:description"
    desc.append(d)

    div = et.SubElement(desc, "div", {"id": "last_modified"})
    div.text = "Last modified: "

    modified = graph.value(muldicat, DCT.modified)
    span = et.SubElement(div, "span", {"property": "dcterms:modified",
                                       "datatype": modified.datatype})
    span.text = modified


def add_tables(g, html):
    body = html.find('body')
    tables = {}
    for lang in languages.values():
        tables[lang] = []

    # bundle up the concepts into language specific lists
    for concept in g.subjects(RDF.type, SKOS.Concept):
        for lang in languages.keys():
            code = languages[lang]
            row = {}
            row['uri'] = concept
            row['id'] = uri_to_id(concept, code)
            row['prefLabel'] = l(g.objects(concept, SKOS.prefLabel), code)
            row['definition'] = l(g.objects(concept, SKOS.definition), code)
            row['altLabel'] = l(g.objects(concept, SKOS.altLabel), code,
                    first=False)

            row['broader'] = []
            for bt in g.objects(concept, SKOS.broader):
                label = l(g.objects(bt, SKOS.prefLabel), code)
                id = uri_to_id(bt, code)
                row['broader'].append({'id': id, 'label': label, 
                                       'uri': bt})

            row['narrower'] = []
            for nt in g.objects(concept, SKOS.narrower):
                label = l(g.objects(nt, SKOS.prefLabel), code)
                id = uri_to_id(nt, code)
                row['narrower'].append({'id': id, 'label': label,
                                        'uri': nt})

            row['related'] = []
            for rt in g.objects(concept, SKOS.related):
                label = l(g.objects(rt, SKOS.prefLabel), code)
                id = uri_to_id(rt, code)
                row['related'].append({'id': id, 'label': label,
                                       'uri': rt})
                    
            tables[code].append(row)

    # add the language specific lists as separate tables to the body
    for lang, muldicat_data in tables.items():
        h2 = et.SubElement(body, "h2")
        h2.text = lang

        table = et.SubElement(body, "table")

        tr = et.SubElement(table, "tr")
        th = et.SubElement(tr, "th", {"class": "concept"})
        th.text = "Concept"
        th = et.SubElement(tr, "th", {"class": "definition"})
        th.text = "Definition"
        th = et.SubElement(tr, "th", {"class": "relations"})
        th.text = "Relations"

        for row in muldicat_data:
            tr = et.SubElement(table, "tr", {"id": row["id"],
                                             "about": row['uri']})
            
            # ignore languages that lack a concept label
            if row["prefLabel"] == None:
                continue

            td = et.SubElement(tr, "td", {"property": "skos:prefLabel"})
            td.text = row["prefLabel"]

            td = et.SubElement(tr, "td", {"property": "skos:definition"})
            td.text = row["definition"]

            td = et.SubElement(tr, "td")

            for label in row["altLabel"]:
                span = et.SubElement(td, "span", 
                        {"property": "skos:altLabel"})
                td.text = "[UF] " + label

            for bt in row["broader"]:
                span = et.SubElement(td, "a",
                        {"rel": "skos:broader",
                         "href": "#" + bt["id"],
                         "resource": bt["uri"]})
                span.text = "[BT] " + bt["label"]
                et.SubElement(td, "br")

            for nt in row["narrower"]:
                span = et.SubElement(td, "a",
                        {"rel": "skos:narrower",
                         "href": "#" + nt["id"],
                         "resource": nt["uri"]})
                span.text = "[NT] " + nt["label"] 
                et.SubElement(td, "br")

            for rt in row["related"]:
                span = et.SubElement(td, "a",
                        {"rel": "skos:related",
                         "href": "#" + rt["id"],
                         "resource": rt["uri"]})
                span.text = "[RT] " + rt["label"] 
                et.SubElement(td, "br")



def l(literals, lang, first=True):
    "helper function to filter literals based on language tag"
    found = []
    for literal in literals:
        if literal.language == lang:
            found.append(literal)
    if not first:
        return found
    elif len(found) > 0:
        return found[0]
    else:
        return None

def uri_to_id(uri, lang):
    return "%s_%s" % (urlparse.urldefrag(uri)[1], lang)


if __name__ == "__main__":
    rdfxml = sys.argv[1]
    convert(rdfxml)

