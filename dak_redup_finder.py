import csv
import unicodedata
import re
import sys
import json

from langdata import dakota
from spetools.syllabifier import Syllabifier
from spetools.reduplicator import RedupVerifier


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
        cases = self.find_redup_cases()
        if self.verbose: print(f'\nFound {len(candidates)} cases of reduplication.')
        self.write_cases_to_outfile(candidates)
        if self.verbose: print(f'Spreadsheet of cases written to "{self.outfile}".')

    def write_cases_to_outfile(self, cases):
        with open(self.outfile, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, list(self.outfields.values()))
            writer.writerows(cases)

    def find_redup_cases(self):
        cases = []
        with open(self.infile, newline='', encoding='utf8') as csvfile:
            reader = csv.DictReader(csvfile)  # TODO: allow inputs without header; have option to read in from vals here
            for row in reader:
                if verbose and self.row_num % 100 == 1:
                    print(f'Processed {self.row_num-1} rows, found {len(cases)} cases so far.')
                row_cases = self.eval_utterance(row[self.infields['utterance']])
                for case in row_cases:
                    if case is not None:
                        case[self.outfields['row']] = self.row_num
                        case[self.outfields['translation']] = row[self.infields['translation']]
                        cases.append(case)

                self.row_num += 1

        return cases

    def eval_utterance(self, utterance):
        ascii_utterance = self.strip_diacritics(utterance).lower()
        words = re.split(r'\W+', ascii_utterance)
        candidates = []
        for word in words:
            candidate = self.eval_word(word)  # we don't need the diacritics for this
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
        except (TypeError, NameError, AttributeError):  # unicode is a default on python 3
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
