import re
from spetools.spe import SPERule

class RedupVerifier:

    def __init__(self, rules):
        """
        Creates a new RedupVerifier with an ordered set of SPERules. Set generous to force all
        rules to optional.
        :param rules: Ordered iterable of SPERules; rules will apply in the order given
        :param generous: Forces all rules to optional; False by default
        """
        self.ruleset = rules

    def verify(self, syllab, unknown_bounds=True):
        """
        Check if rules allow any two adjacent syllables in syllab to become identical
        :param syllab: The reduplication candidate as a syllabified word
        :return: True if rules allow for two adjacent syllables to become identical; False otherwise
        """
        candidate_syllabs = self.set_redup_bounds(syllab) if unknown_bounds else [syllab]
        for candidate_syllab in candidate_syllabs:
            if self.has_redup_orig_form(candidate_syllab):
                return True

        return False

    def set_redup_bounds(self, syllab):
        """
        Makes a list of possible reduplication syllabifications by setting a reduplication bound ('+') at a single
        generic boundary ('-') for each.
        :param syllab: Base syllabification of a reduplication candidate
        :return: List of 2-tuples (syllabification, R0 syllable 0-index) of all detectable original reduplicated forms
        """
        bound_idxs = [m.start() for m in re.finditer('-', syllab)]

        return [syllab[:idx] + '+' + syllab[idx+1:] for idx in bound_idxs]

    def has_redup_orig_form(self, candidate_syllab):
        """
        Checks whether there exists a rule deapplication from the given rules that restores candidate_syllab
        :param candidate_syllab:
        :return: True if a rule deapplication on candidate_syllab yields any reduplicated forms; False otherwise
        """
        ruleset_outputs = self.deapply_rules(candidate_syllab)

        for ruleset_output in ruleset_outputs:
            if self.has_redup(ruleset_output):
                return True
        return False

    def deapply_rules(self, candidate_syllab):
        """
        Deapplies all rules in the ruleset to the target word. Will iteratively non-deterministically deapply rules.
        :param candidate_syllab: Word to process; must be syllabified if working with boundary-sensitive rules
        :return: List of legal (by rules) forms of word after rule deapplication
        """
        current_outputs = [candidate_syllab]

        for rule in self.ruleset[::-1]:
            new_outputs = []
            for current_output in current_outputs:
                new_outputs += rule.deapply(current_output)
            current_outputs = new_outputs

        return list(set(current_outputs))  # remove dupes

    def has_redup(self, candidate_syllab):
        """
        Checks a candidate syllabification for equality of R0 and R1, assuming one '+' boundary between the two .
        :param candidate_syllab:
        :return: True if R0 == R1; False otherwise
        """
        partition = candidate_syllab.split('+', 1)  # assume only 1 redup boundary, by above methods
        r0 = re.split(r'[-=#%]', partition[0])[-1]
        r1 = re.split(r'[-=#%]', partition[1])[0]

        return r0 == r1
