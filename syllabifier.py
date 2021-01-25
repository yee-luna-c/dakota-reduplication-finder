import re

"""
Syllabifies words from a language given syllable structures (of a CV skeleton) and vowel and consonant inventories.
"""
class Syllabifier:

    """
    Params:
    
    syllable_structure: list of strings of C and V
    vowel_inventory: regex string matching any single vowel
    consonant_inventory: regex string matching any single consonant
    ignore_diacritics: whether to ignore non-ascii characters; defaults to False
    """
    def __init__(self, syllable_structures, vowel_inventory, consonant_inventory):
        self.syll_structs = syllable_structures
        self.vowel_inv = vowel_inventory
        self.cons_inv = consonant_inventory

    def syllabify(self, word):
        syllabs = []
        partitions = [self.match_syll(word, struct) for struct in self.syll_structs]
        for this_syll, remainder in partitions:
            print(this_syll, remainder)
            if this_syll is None: continue # match_struct did not find a matching syllable
            if len(remainder) == 0: syllabs += [this_syll] # syllable is end of word
            else: syllabs += [(this_syll + '-' + syllab) for syllab in self.syllabify(remainder)]

        return syllabs

    def match_syll(self, text, struct):
        syll = ''
        remainder = text

        for seg_type in struct:
            if seg_type == 'C':
                cons, remainder = self.match_cons(remainder)
                if cons is None: return None, None # return value of second element is irrelevant
                syll += cons
            elif seg_type == 'V':
                vowel, remainder = self.match_vowel(remainder)
                if vowel is None: return None, None  # return value of second element is irrelevant
                syll += vowel
            else:
                raise Exception(f'Unexpected (non-CV) character in struct: {struct}')

        return syll, remainder

    def match_cons(self, text):
        return self.match_seg(text, self.cons_inv)

    def match_vowel(self, text):
        return self.match_seg(text, self.vowel_inv)

    def match_seg(self, text, inv):
        seg = re.match(inv, text)

        seg = seg.group(0) if seg else None # TODO: assumes no overlap in symbols in inv; i.e. no 'c' AND 'ch'
        return seg, None if seg is None else text[len(seg):] # return value of second element is irrelevant
