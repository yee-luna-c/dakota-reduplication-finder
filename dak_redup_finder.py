import csv
import unicodedata
import re
import sys
import json

from langdata import dakota
from spetools.syllabifier import Syllabifier
from redup_verifier import RedupVerifier


class DakRedupFinder:
    
    def __init__(self, config, verbose=False):
        with open(config) as jsonfile:
            cfg = json.load(jsonfile)
        self.infile = cfg['input_file']
        self.outfile = cfg['output_file']
        self.infields = cfg['input_field_mapping']
        self.outfields = cfg['output_field_mapping']
        self.row_num = 2 if cfg['input_has_header'] else 1  # 1-indexed for readability

        self.syllabifier = Syllabifier(dakota.syllable_structures,
                                       dakota.vowel_inventory,
                                       dakota.consonant_inventory)
        self.redup_verifier = RedupVerifier(dakota.phon_rules)
        self.verbose = verbose

    def run(self):
        candidates = self.find_redup_candidates()
        if self.verbose: print(f'\nFound {len(candidates)} reduplication candidates.')
        self.write_candidates_to_outfile(candidates)
        if self.verbose: print(f'Spreadsheet of candidates written to "{self.outfile}".')

    def write_candidates_to_outfile(self, candidates):
        with open(self.outfile, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, list(self.outfields.values()))
            writer.writerows(candidates)

    def find_redup_candidates(self):
        candidates = []
        with open(self.infile, newline='') as csvfile:
            reader = csv.DictReader(csvfile)  # TODO: allow inputs without header; have option to read in from vals here
            for row in reader:
                row_candidates = self.eval_utterance(row[self.infields['utterance']])
                for candidate in row_candidates:
                    if candidate is not None:
                        candidate[self.outfields['row']] = self.row_num
                        candidate[self.outfields['translation']] = row[self.infields['translation']]
                        candidates.append(candidate)

                self.row_num += 1

        return candidates

    def eval_utterance(self, utterance):
        words = re.split(r'\W+', utterance)
        candidates = []
        for word in words:
            candidate = self.eval_word(self.strip_diacritics(word).lower())  # we don't need the diacritics for this
            if candidate is None: continue
            candidate[self.outfields['utterance']] = utterance
            candidate[self.outfields['word']] = word

            candidates.append(candidate)

        return candidates

    def eval_word(self, word):
        syllabs = self.syllab_word(word)
        if syllabs is None: return None

        for syllab in syllabs:
            is_candidate = self.contains_redup(syllab)
            if is_candidate: return {self.outfields['syllab']: syllab}  # only return one valid syllab for each word

        return None

    def contains_redup(self, syllab):
        return self.redup_verifier.verify(syllab)

    def syllab_word(self, word):
        syllabs = self.syllabifier.syllabify(word)
        if len(syllabs) == 0:
            if self.verbose: print(f'Unable to syllabify "{word}" from row {self.row_num}, skipping...')
            return None
        return syllabs

    def strip_diacritics(self, text):
        """
        :author: hexaJer @ https://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-normalize-in-a-python-unicode-string

        Strip non-ascii items from input String.

        :param text: The input string.
        :returns: The processed String.
        """
        try:
            text = text.decode('utf-8')
        except (TypeError, NameError):  # unicode is a default on python 3
            pass
        text = unicodedata.normalize('NFD', text)
        text = text.encode('ascii', 'ignore')
        text = text.decode("utf-8")
        return str(text)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f'Expected 1 or 2 arguments, got {len(sys.argv)-1}.')
        print('Usage: python dak_redup_finder config_file (verbose)')
        exit(1)

    verbose = sys.argv[2] if len(sys.argv) >= 3 else False
    drf = DakRedupFinder(sys.argv[1], verbose)
    drf.run()
