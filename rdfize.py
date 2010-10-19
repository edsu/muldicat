#!/usr/bin/env python

"""
Give this script the location of the Multilingual Dictionary of Cataloging
Terms and Concepts as a CSV file, and it will generate the RDF/XML.

This script is intended as a bootstrapping mechanism to get from managing
the thesaurus as a Word document to managing it as SKOS data.
"""

import re
import csv
import sys
import codecs
import datetime

from rdflib.graph import ConjunctiveGraph
from rdflib.term import URIRef, Literal
from rdflib.namespace import Namespace, RDF

languages = {
    'English': 'en',
    'Albanian': 'sq',
    'Arabic': 'ar',
    'Chinese': 'zh',
    'Croatian': 'hr',
    'Czech': 'cs',
    'French': 'fr',
    'German': 'de',
    'Italian': 'it',
    'Japanese': 'ja',
    'Korean': 'ko',
    'Latvian': 'lv',
    'Portuguese': 'pt',
    'Russian': 'ru',
    'Slovak': 'sk',
    'Slovene': 'sl',
    'Spanish': 'es',
    'Swedish': 'sv',
    'Thai': 'th',
    'Vietnamese': 'vi'
}


SKOS = Namespace('http://www.w3.org/2004/02/skos/core#')
DCT = Namespace('http://purl.org/dc/terms/')


def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        yield [unicode(cell, 'utf-8') for cell in row]


def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')


def make_id(label):
    label = re.sub('\(.*\)', '', label)
    label = label.strip()
    camel_case = ''.join([w.capitalize() for w in label.split(' ')])
    return URIRef('http://iflastandards.info/ns/muldicat#%s' % camel_case)


def convert(muldicat_csv):
    g = ConjunctiveGraph()
    g.bind('skos', SKOS)
    g.bind('dct', DCT)

    muldicat = URIRef("http://iflastandards.info/ns/muldicat")
    subject = None
    for row in unicode_csv_reader(codecs.open(muldicat_csv, encoding='utf-8')):
        # strip whitespace from row
        row = [cell.strip() for cell in row]

        # older version of the table had an unused ID column
        if len(row) == 8:
            print "popping"
            row.pop(0)

        if row[0] == 'Language':
            continue
        elif row == [u'', u'', u'', u'', u'', u'', u'', u'']:
            continue
        else:
            lang, label, definition, see, see_also, source, modified  = row
            lang = languages.get(lang, None)
            label = label.strip()
            if not lang or not label:
                continue

            # use the english label to form part of the URI for the concept 
            # hopefully not too controversial?
            if lang == 'en':
                subject = make_id(label)
            
            g.add((subject, RDF.type, SKOS.Concept))
            g.add((subject, SKOS.prefLabel, Literal(label, lang=lang)))
            g.add((subject, SKOS.inScheme, muldicat))

            if definition:
                g.add((subject, SKOS.definition, Literal(definition, lang=lang)))

            if source:
                g.add((subject, DCT.source, Literal(source, lang=lang)))

            if modified:
                date = datetime.datetime.strptime(modified, '%Y%m%d').date()

                # only record the latest last modification date for the concept
                existing_date = g.value(subject, DCT.modified)
                if not existing_date and date:
                    g.add((subject, DCT.modified, Literal(date)))
                elif date and existing_date and date > existing_date.toPython():
                    g.remove((subject, DCT.modified, existing_date))
                    g.add((subject, DCT.modified, Literal(date)))

            for alt_label in see.split(','):
                if not alt_label:
                    continue
                alt_label = alt_label.strip()
                g.add((subject, SKOS.altLabel, Literal(alt_label, lang=lang)))
            
            # link up relations if we have the english label
            if lang == 'en' and see_also:
                for s in see_also.split(','):
                    s = s.strip()
                    match = re.match(r'(.*) \[(.*?)\]', s)
                    if not match:
                        continue
                    label, reltype = match.groups()
                    reltype = reltype.strip('[]') # some are formatted wrong
                    
                    object = make_id(label)

                    if reltype == 'BT':
                        g.add((subject, SKOS.broader, object))
                        g.add((object, SKOS.narrower, subject))
                    elif reltype == 'NT':
                        g.add((subject, SKOS.narrower, object))
                        g.add((object, SKOS.broader, subject))
                    elif reltype == 'RT':
                        g.add((subject, SKOS.related, object))
                        g.add((object, SKOS.related, subject))
                    else:
                        raise RuntimeError(reltype)
    return g


def sanity_check(g):
   for subject in set(graph.subjects()):
        for pref_label in graph.objects(subject, SKOS.prefLabel):
            if pref_label.language == 'en':
                if not pref_label:
                    raise("%s missing skos:prefLabel" % subject)


if __name__ == '__main__':
    muldicat_csv = sys.argv[1]
    graph = convert(muldicat_csv)
    sanity_check(graph)
    graph.serialize(sys.stdout)
 
