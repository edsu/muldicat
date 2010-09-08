#!/usr/bin/env python

"""
Utility to unpack the semantic relations (broader, narrower, related)
in the spreadsheet, and print out some statistics by language.
"""

import re
import csv
import codecs

def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        yield [unicode(cell, 'utf-8') for cell in row]

def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')

rel_types = {}
for row in unicode_csv_reader(codecs.open('docs/MulDiCat.csv', encoding='utf-8')):
    if row[1] == 'Language':
        continue # header
    elif row == [u'', u'', u'', u'', u'', u'', u'', u'']:
        continue # spacing row

    lang, label, definition, see, see_also, source, modified  = row[1:]
    if lang and see_also:
        for rel in re.findall(r'\[(.*?)\]', see_also):
            if not rel_types.has_key(lang):
                rel_types[lang] = {}
            rel_types[lang][rel] = rel_types[lang].get(rel, 0) + 1

for lang in rel_types.keys():
    print "%-15s" % lang, 
    for rel in rel_types[lang].keys():
        print "%s (%s)" % (rel, rel_types[lang][rel]),
    print
