import csv
import unicodedata
import re
import sys

from langdata import dakota
from spetools.syllabifier import Syllabifier
from redup_verifier import RedupVerifier


class DakRedupFinder:
    input_fieldnames = {

    }
    output_fieldnames = {
        'row': 'Row',
        'word': 'Dakota word',
        'syllab': 'Syllabification',
        'gloss': 'English gloss',
        'utterance': 'Dakota utterance',
        'translation': 'English translation'
    }

    def __init__(self, source_file, output_file, verbose=False):
        self.source_file = source_file
        self.output_file = output_file
        self.verbose = verbose
        self.syllabifier = Syllabifier(dakota.syllable_structures,
                                       dakota.vowel_inventory,
                                       dakota.consonant_inventory)
        self.redup_verifier = RedupVerifier(dakota.phon_rules)
        self.row_num = 1

    def run(self):
        candidates = self.find_redup_candidates()
        if self.verbose: print(f'\nFound {len(candidates)} reduplication candidates.')
        self.write_candidates_to_outfile(candidates)
        if self.verbose: print(f'Spreadsheet of candidates written to {self.output_file}.')

    def write_candidates_to_outfile(self, candidates):
        with open(self.output_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, list(DakRedupFinder.output_fieldnames.values()))
            writer.writerows(candidates)

    def find_redup_candidates(self):
        self.row_num = 2  # TODO: assume we start at the second line (first is headers)
        candidates = []
        with open(self.source_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                row_candidates = self.eval_utterance(row['Dakota'])
                for candidate in row_candidates:
                    if candidate is not None:
                        candidate[DakRedupFinder.rule_name('row')] = self.row_num
                        candidate['English translation'] = row['English']
                        candidates.append(candidate)

                self.row_num += 1

        return candidates

    def eval_utterance(self, utterance):
        words = re.split(r'\W+', utterance)
        candidates = []
        for word in words:
            candidate = self.eval_word(self.strip_diacritics(word).lower()) # we don't need the diacritics for this
            if candidate is None: continue
            candidate['Dakota utterance'] = utterance
            candidate['Dakota word'] = word

            candidates.append(candidate)

        return candidates

    def eval_word(self, word):
        syllabs = self.syllab_word(word)
        if syllabs is None: return None

        for syllab in syllabs:
            is_candidate = self.contains_redup(syllab)
            if is_candidate: return {'Syllabification': syllab}  # only return one valid syllab for each word

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
        :type text: String

        :returns: The processed String.
        :rtype: String
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
    if len(sys.argv) < 3:
        print(f'Expected 2 or 3 arguments, got {len(sys.argv)-1}.')
        print('Usage: python dak_redup_finder source_file output_file (verbose)')
        exit(1)

    verbose = sys.argv[3] if len(sys.argv) >= 4 else False
    drf = DakRedupFinder(sys.argv[1], sys.argv[2], verbose)
    drf.run()
