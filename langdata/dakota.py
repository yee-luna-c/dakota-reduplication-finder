"""
Data module for essential information about Santee Dakota.
"""

from spetools.spe import SPERule

syllable_structures = ['CV', 'CVC', 'V', 'VC', 'CCV', 'CCVC']
vowel_inventory = r'[aeiouAEIOU]'
consonant_inventory = r'[wytdpbszkhgcjnm]'

DakRule = lambda name, alternations, context, optional=False: SPERule(name, alternations, context,
                                                                      vowel_inventory=vowel_inventory,
                                                                      consonant_inventory=consonant_inventory,
                                                                      optional=optional)
phon_rules = [
    DakRule('CCC Simplification', [(cons, '') for cons in consonant_inventory.strip('[]')], r'_\+{C}{C}'),
    DakRule('Coronal Dissimilation', [('t', 'k'), ('c', 'k'), ('j', 'g'), ('d', 'g')], r'_{-}[tdcjsz]'),
    DakRule('Degemination', [(cons, '') for cons in consonant_inventory.strip('[]')], r'_\+{!}'),
    # don't need Deasp/Deglot since we're ignoring diacritics
    DakRule('Voicing Assimilation', [('t', 'd'), ('p', 'b'), ('k', 'g'), ('c', 'j')],
            r'_{-}[wydbzgjnm]'),
    DakRule('Fricative Devoicing', [('z', 's'), ('g', 'h')], r'_\+'),
    DakRule('Velar Palatization', [('k', 'c'), ('g', 'j')], r'i{-}?_'),
    DakRule('Velar Palatization (overapplied)', [('k', 'c'), ('g', 'j')], r'c{^-}*\+_', optional=True)
]