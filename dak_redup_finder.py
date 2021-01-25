import csv
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
        if self.verbose:
            print(f'\nFound {len(cases)} cases of reduplication.')
        self.write_cases_to_outfile(cases)
        if self.verbose:
            print(f'Spreadsheet of cases written to "{self.outfile}".')

    def write_cases_to_outfile(self, cases):
        with open(self.outfile, 'w', newline='', encoding='utf8') as csvfile:
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
        ascii_utterance = dakota.convert_to_ascii(utterance)
        words = re.split(r'\W+', ascii_utterance)
        cases = []
        for word in words:
            if word == "":
                continue
            case = self.eval_word(word)
            if case is None:
                continue
            case[self.outfields['utterance']] = utterance
            case[self.outfields['word']] = dakota.convert_to_unicode(word)

            cases.append(case)

        return cases

    def eval_word(self, word):
        syllabs = self.syllab_word(word)
        if syllabs is None:
            return None

        for syllab in syllabs:
            is_case = self.contains_redup(syllab)
            if is_case:
                return {self.outfields['syllab']: syllab}  # only return one valid syllab for each word

        return None

    def contains_redup(self, syllab):
        return self.redup_verifier.verify(syllab)

    def syllab_word(self, word):
        syllabs = self.syllabifier.syllabify(word)
        if len(syllabs) == 0:
            if self.verbose:
                print(f'Unable to syllabify "{word}" from row {self.row_num}, skipping...')
            return None
        return syllabs


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f'Expected 1 or 2 arguments, got {len(sys.argv)-1}.')
        print('Usage: python dak_redup_finder config_file (verbose)')
        exit(1)

    verbose = sys.argv[2] if len(sys.argv) >= 3 else False
    drf = DakRedupFinder(sys.argv[1], verbose)
    drf.run()
