"""
Data module for essential information about Santee Dakota.
"""

import unicodedata
from spetools.spe import SPERule

syllable_structures = ['CV', 'CVC', 'V', 'CCV', 'CCVC']
vowel_inventory = r'[aAeEiIoOuU]'
consonant_inventory = r'[wytdTpbPkgKszSjHGhcCnm]'

DakRule = lambda name, alternations, context, optional=False: SPERule(name, alternations, context,
                                                                      vowel_inventory=vowel_inventory,
                                                                      consonant_inventory=consonant_inventory,
                                                                      optional=optional)
phon_rules = [
    DakRule('CCC Simplification', [(cons, '') for cons in consonant_inventory.strip('[]')], r'_\+{C}{C}'),
    DakRule('Deglottalization', [('T', 't'), ('C', 'c'), ('P', 'p'), ('K', 'k')], r'_[tdTpbPkgK]'),
    DakRule('Coronal Dissimilation', [('t', 'k'), ('c', 'k'), ('c', 'g'), ('d', 'g')], r'_{-}[tdTcszSj]'),  # free var?
    DakRule('Stop Voicing', [('t', 'd'), ('k', 'g'), ('p', 'b')], r'_\+'),  # second alter?
    DakRule('Degemination', [(cons, '') for cons in consonant_inventory.strip('[]')], r'_\+{!}'),
    DakRule('Voicing Assimilation', [('t', 'd'), ('p', 'b'), ('k', 'g')], r'_{-}[wydbzgGjnm]'),
    DakRule('Fricative Devoicing', [('z', 's'), ('G', 'H')], r'_\+'),
    DakRule('Velar Palatization', [('k', 'c'), ('g', 'c')], r'i{-}?_'),  # second alter?
    DakRule('Velar Palatization (overapplied)', [('k', 'c'), ('g', 'c')], r'c{^-}*\+_', optional=True),  # second alter?
    DakRule('Ablaut', [('a', 'e'), ('A', 'E')], r'_[-=#%]', optional=True)
]

unicode_to_ascii_mapping = {
    # nasals
    'aƞ': 'A', 'eƞ': 'E', 'iƞ': 'I', 'oƞ': 'O', 'uƞ': 'U',
    # ejectives
    'ṭ': 'T', 'p̣': 'P', 'ḳ': 'K', 'c̣': 'C',
    # fricatives
    'ṡ': 'S', 'ḣ': 'H', 'ġ': 'G'
}


def convert_to_ascii(unicode_text):
    """
    Strips diacritics from input string, converting nasals, ejectives, and special fricatives to respective uppers
    when found to retain contrast. Output should match inventories above, assuming good input.

    :param unicode_text: The unicode input string
    :returns: The corresponding ascii string
    """
    text = unicodedata.normalize('NFD', unicode_text.lower())

    text = map_special_segs(text, unicode_to_ascii_mapping)

    text = text.encode('ascii', 'ignore')
    text = text.decode("utf-8")
    return str(text)


def convert_to_unicode(ascii_text):
    # Python strings are utf-8-encoded by default, so no funny business in this one
    return map_special_segs(ascii_text, {val: key for key, val in unicode_to_ascii_mapping.items()})


def map_special_segs(text, mapping):
    """
    Converts special segments in text to new representations based on the provided mapping.
    :param text:
    :param mapping:
    :return:
    """
    for m in mapping.items():
        text = text.replace(unicodedata.normalize('NFD', m[0]), unicodedata.normalize('NFD', m[1]))

    return text
