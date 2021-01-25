import re
import itertools


class SPERule:
    def __init__(self, name, alternations, context,
                 vowel_inventory=r'[aeiou]',
                 consonant_inventory=r'[qwrtypsdfghjklzxcvbnm]',
                 optional=False):
        self.name = name
        self.alternations = alternations
        self.alternation_origs = list(list(zip(*alternations))[0])
        self.alternation_news = list(list(zip(*alternations))[1])
        self.context = context
        self.cons_inv = consonant_inventory
        self.vowel_inv = vowel_inventory
        self.optional = optional

    def __str__(self):
        return 'Rule ' + ("(optional) " if self.optional else "") + '"' + self.name + '": ' \
               'alternates ' + str(self.alternations) + ' in context ' + str(self.context)

    def apply(self, word):
        instances = self.find_application_instances(word)
        return list(set(self.apply_to_all(word, instances) if not self.optional else
                        self.apply_combinations(word, instances)))

    def deapply(self, word):
        """
        Deapply this rule from the given word. Note that even mandatory rules will trigger nondeterminism when
        deapplied due to the possibility that the result segment was underlying, not the product of the rule.
        :param word:
        :return:
        """
        rev_optional = self.optional
        rev_alternations = [(new, orig) for orig, new in self.alternations]
        for rev_orig in self.alternation_news:
            rev_alternations.append((rev_orig, rev_orig))  # add a case where nothing changes; may have been as appears

        rev_clone = SPERule(self.name + ' [deapplier]', rev_alternations, self.context,
                            self.vowel_inv, self.cons_inv, rev_optional)
        return rev_clone.apply(word)

    def apply_to_all(self, word, instances):
        final_states = []  # for cases of free variation (multiple morphs for seg)

        while len(instances) > 0:
            seg, idx = instances.pop()
            morphs = self.get_morphs_for_seg(seg)
            if len(morphs) > 1:  # nondeterminism on free variation - spawn clone processes
                for i in range(1, len(morphs)):
                    nd_word = word[:idx] + morphs[i] + word[idx+len(seg):]
                    nd_instances = self.shift_instances(instances.copy(), seg, morphs[i])
                    final_states += self.apply_to_all(nd_word, nd_instances)
            word = word[:idx] + morphs[0] + word[idx+len(seg):]
            instances = self.shift_instances(instances, seg, morphs[0])

        final_states.append(word)

        return final_states

    def get_morphs_for_seg(self, seg):
        return [self.alternation_news[i] for i, orig in enumerate(self.alternation_origs) if orig == seg]

    def shift_instances(self, instances, orig, new):
        """
        Assuming all remaining entries in instances are rightward of a change, shift indices according to
        character length differences from orig to new.
        :param instances: List of tuple pairs (seg, idx); will not be muted
        :param orig: Original segment of recent change
        :param new: New segment of recent change
        :return: New list of instances with adjusted indices
        """
        return [(seg, idx+(len(new)-len(orig))) for seg, idx in instances]

    def apply_combinations(self, word, instances):
        instance_combinations = []

        for i in range(len(instances)+1):
            instance_combinations += list(itertools.combinations(instances, i))

        final_states = []
        for ins in instance_combinations:
            final_states += self.apply_to_all(word, list(ins))

        return final_states

    def find_application_instances(self, word):
        instances = []

        for seg in list(set(self.alternation_origs)):
            regex = self.make_regex(self.context, seg)
            instances += self.match_instances_by_regex(word, seg, regex)

        return instances

    def match_instances_by_regex(self, word, seg, regex):
        instances = []

        if seg != '':
            seg_matches = [m.start() for m in re.finditer(seg, word)]
        else:  # special case for insertion: try all spots
            seg_matches = range(len(word)+1)

        for seg_match in seg_matches:
            try_word = word[:seg_match] + '_' + word[seg_match+len(seg):]
            if re.findall(regex, try_word):
                instances += [(seg, seg_match)]

        return instances

    def make_regex(self, context, seg):
        return self.replace_segmental(self.replace_static(context), seg)

    def replace_static(self, text):
        # handles special characters: {C} (any consonant), {V} (any vowel), {-} (any boundary), {^-} (no boundary)
        return text.replace('{C}', self.cons_inv).replace('{V}', self.cons_inv)\
                   .replace('{-}', r'[%#=\+-]').replace('{^-}', r'[^%#=\+-]')

    def replace_segmental(self, text, seg):
        # handles special characters: {!} (identical segment)
        return text.replace('{!}', seg)

    def set_optional(self, optional):
        self.optional = optional
