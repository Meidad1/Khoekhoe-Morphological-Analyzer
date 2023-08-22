import re


class MorphemeBreaker:
    PGN_MORPHEMES = ["ta", "khom", "ge", "da", "ts", "kho", "ro", "go", "so", "du", "b", "s", "kha", "ra", "gu", "di", "n"]
                    # PGN_MORPHEMES is a list because the order matters! For example, "ts" should be checked before "s"
    OBLIQUE_SUFFIXES = {"khoma", "tsa"}
    CONJUNCTIONS = {"î", "o", "osa", "xawe", "tsî", "hîa", "amaga", "ǁnā-amaga", "ǃnâ", "so", "tamas_ka_i_o",
                    "tsîna", "tare-i_ǃaroma", "tamas_kara_i_o", "maar", "want", "xuige", "xui-ao", "îa", "hîna"}
    PERSONAL_PRO_STEMS = {"ti", "sa", "si", "sī", "tī", "sā", "ǁî"}
    DEMONSTRATIVES = {"ǁnā", "nē", "nau"}
    FREE_PGN_MARKERS = {"ta", "da", "du", "gu"}
    DIMINUTIZED_FORMS = {"axaro", "ǀgôaro", "ǂauro"}
    ADVERBIAL_CLAUSES = ["axase", "tamase"]
    HORTATIVE_PARTICLES = {"a", "ǀkhī", "ā", "hā"}
    FIRST_PERSON_PGNS = {"ta", "khom", "m", "ge", "se", "da"}
    THIRD_PERSON_PGNS = {"b", "s", "i", "kha", "ra", "gu", "di", "n"}
    CLITIC_SEPARATOR = "="
    SUFFIX_SEPARATOR = "-"
    CLICKS_SET = {"ǃ", "ǂ", "ǁ", "ǀ"}

    def __init__(self, tx_annotation: str, fte_annotation: str, forms_not_to_segment: set,
                 nominals_not_to_segment: set, paralinguistic_items: dict, adverbs: set):
        self.forms_not_to_segment = forms_not_to_segment
        self.nominals_not_to_segment = nominals_not_to_segment
        self.ann_lst = tx_annotation.split()
        self.fte_annotation = fte_annotation
        self.cur_word = None
        self.previous_word = None
        self.next_word = None
        self.skip_next = False
        self.back_channels = set(paralinguistic_items["BackChannels"])
        self.fillers = set(paralinguistic_items["Fillers"])
        self.adverbs = adverbs

    def break_annotation_to_morphemes(self):
        """
        Performs morpheme segmentation of self.cur_word.
        :return: the result as a String
        """
        self.skip_next = False
        for i in range(len(self.ann_lst)):
            if i > 0:
                self.previous_word = self.ann_lst[i-1]
            if (i + 1) < len(self.ann_lst):
                self.next_word = self.ann_lst[i+1]
            else:
                self.next_word = None
            self.cur_word = self.ann_lst[i]
            if self.skip_next:
                self.skip_next = False
                continue
            # The following condition must appear here, before calling "is_breakable" method
            if self.cur_word in self.back_channels or self.cur_word in self.fillers:
                self.ann_lst[i] = "[" + self.ann_lst[i] + "]"
                continue

            if self.segment_hortatives():
                self.ann_lst[i] = self.cur_word
                if self.next_word:
                    self.ann_lst[i+1] = self.next_word
                continue

            if self.cur_word.startswith("tsîna"):
                self.ann_lst[i] = self.segment_oblique(self.cur_word)
                continue

            if not self.is_breakable():               # If a word should not be segmented --> continue to the next iteration
                continue

            if self.segment_adv():                    # Segments =se =MANNER from axase and tamase
                self.ann_lst[i] = self.cur_word
                continue
            if self.segment_free_pgn():               # handle free PGNs, as 'ta' (1SG) and 'da' (1PL)
                if i == 0 and self.cur_word[0] in {"-", "="}:
                    self.cur_word = self.cur_word[1:]
                self.ann_lst[i] = self.cur_word
                continue
            if self.segment_hyphened_pgn():
                self.ann_lst[i] = self.cur_word
                continue
            segmented_val_changing = self.segment_valency_changing_operators(self.cur_word, i)
            if segmented_val_changing:
                self.ann_lst[i] = segmented_val_changing
                continue
            pgn_segmented = self.segment_pgn(self.cur_word)
            if pgn_segmented:
                if i == 0 and self.cur_word[0] in {"-", "="}:
                    self.cur_word = self.cur_word[1:]
                self.ann_lst[i] = pgn_segmented
                continue
            segmented_oblique = self.segment_oblique(self.cur_word)
            if segmented_oblique:
                self.ann_lst[i] = segmented_oblique

        return " ".join(self.ann_lst)

    def is_breakable(self):
        """
        Checks whether self.cur_word can be segmented or not.
        :return: True if the given word can be segmented, otherwise False.
        """
        if self.fte_annotation == "[English]":                    # if it's a sentence in English
            return False
        elif self.ann_lst[0] and self.ann_lst[0] == "inaudible":
            return False
        elif self.cur_word in self.forms_not_to_segment.union(self.nominals_not_to_segment):
            return False
        elif self.cur_word in self.CONJUNCTIONS.union(self.adverbs):
            return False
        elif self.cur_word.endswith("se") and self.cur_word not in self.ADVERBIAL_CLAUSES:
            return False
        elif self.cur_word.endswith("ma") and not self.cur_word.endswith("khoma"):
            return False
        elif self.cur_word.endswith("ǁgoa"):
            return False
        return True

    def segment_hyphened_pgn(self):
        """
        Segments cases in which there is hyphen ("-") separating a morpheme.
        :return: True if a change is done, False otherwise.
        """
        ends_with = ""
        if self.cur_word.endswith("-i"):
            ends_with = "-i"
        elif self.cur_word.endswith("-e"):                              # -i (PGN) + OBL
            ends_with = "-i -a"
        if len(ends_with) > 0:
            self.cur_word = self.cur_word[:-2] + " " + ends_with        # update cur_word
            return True
        return False

    def segment_free_pgn(self):
        """
        Segments free pgn markers, as 'ta' (1SG),'da' (1PL), 'du', 'gu', 'i' (3C.SG).
        :return: True if a change is done, False otherwise.
        """
        if self.cur_word == "i" or self.cur_word in self.PGN_MORPHEMES:

            # check the pattern "conj PGN" --> "conj =PGN"
            if self.previous_word and self.previous_word in self.CONJUNCTIONS:
                self.cur_word = self.CLITIC_SEPARATOR + self.cur_word
                return True
        if self.cur_word in self.FREE_PGN_MARKERS:
            separator_type = self.SUFFIX_SEPARATOR
            if self.previous_word and self.previous_word not in self.PERSONAL_PRO_STEMS:
                if self.previous_word in self.DEMONSTRATIVES and self.cur_word == "gu":
                    separator_type = self.SUFFIX_SEPARATOR
                else:
                    separator_type = self.CLITIC_SEPARATOR
            self.cur_word = separator_type + self.cur_word
            return True

        return False

    def segment_pgn(self, word):
        """
        Segments pgn suffixes and enclitics of a given word.
        :return: If word ends with pgn --> returns the segmented string, otherwise --> returns None
        """
        for morpheme in self.PGN_MORPHEMES:
            if word.endswith(morpheme):
                prefix = word[:-len(morpheme)]
                if len(prefix) == 0 or prefix[-1] in self.CLICKS_SET:
                    continue
                if prefix in self.DIMINUTIZED_FORMS:                                        # -DIM suffix
                    prefix = prefix[:-2] + " -ro"
                if prefix in self.CONJUNCTIONS.union(self.forms_not_to_segment).union(self.adverbs):
                    if prefix == "ai" and morpheme == "s" and self.next_word == "ai":       # if it is: "ais ai"
                        separator_type = self.SUFFIX_SEPARATOR
                    elif prefix in self.PERSONAL_PRO_STEMS:                                 # for example: tita, sādu --> ti -ta, sā -du
                        separator_type = self.SUFFIX_SEPARATOR
                    else:
                        separator_type = self.CLITIC_SEPARATOR
                else:
                    separator_type = self.SUFFIX_SEPARATOR
                return prefix + " " + separator_type + morpheme
        if word.endswith("i") and self.segment_i_pgn(word):               # 3C.SG PGN ('i')
            return word[:-1] + " -i"
        if word.endswith("m") and word[:-1] in self.CONJUNCTIONS.union(self.adverbs):
            return word[:-1] + " " + self.CLITIC_SEPARATOR + "m"          # Cases like: 'xawem', 'tsî'

        return None

    def segment_i_pgn(self, word):
        """
        Determines whether final i should be segmented or not
        :return: True if i should be segmented, False otherwise
        """
        if len(word) > 2 and word[-3:-1] in ["mm", "nn"]:                 # xammi, sisenni
            return True
        elif len(word) > 1 and word[-2] in ['m', 'l', 'r']:               # for example: "xami" (lion), "skoli", "misteri"
            return True
        return False

    def segment_valency_changing_operators(self, word, idx):
        if word.endswith("bahe"):                                         # APPL + PASS
            return word[:-4] + " -ba" + " -he"
        elif word.endswith("he") and len(word) > 2:                       # PASS
            return word[:-2] + " -he"
        elif word.endswith("basen"):                                      # APPL + REFL
            return word[:-5] + " -ba" + " -sen"
        elif word.endswith("sen"):
            if "self" in self.fte_annotation or "selves" in self.fte_annotation:
                return word[:-3] + " -sen"
            else:
                return word
        elif word.endswith("babi") or word.endswith("basi") or word.endswith("bate"):         # APPL + OBJ marker
            return word[:-4] + " -ba " + word[-2:]                                            # OBJ markers should be separated with space
        elif word.endswith("ba") and idx == len(self.ann_lst) - 1:                            # APPL in the end of sentences
            return word[:-2] + " -ba"
        return None

    def segment_oblique(self, word):
        if word.endswith("ga"):
            if word[-3] not in self.CLICKS_SET:
                pgn_segmented = self.segment_pgn(word[:-2] + "gu")
                if pgn_segmented:
                    return pgn_segmented + " -a"
            else:
                return None                             # if a word ends with "click + ga" we don't segment
        elif word.startswith("tsîna"):
            match = re.match("^tsîna([a-z]{1,4})?$", word)
            optional_clitic = match.group(1)
            if optional_clitic:
                return "tsîn -a =" + optional_clitic
            return "tsîn -a"
        elif word.endswith("de"):
            pgn_segmented = self.segment_pgn(word[:-2] + "di")
            if pgn_segmented:
                return pgn_segmented + " -a"
        elif word.endswith("a"):
            pgn_segmented = self.segment_pgn(word[:-1])
            if pgn_segmented:
                return pgn_segmented + " -a"
        elif word.endswith("e"):                        # xamme > xamm -i -a
            if self.segment_i_pgn(word[:-1] + "i"):
                return word[:-1] + " -i" + " -a"
        else:
            return None

    def segment_adv(self):
        if self.cur_word in self.ADVERBIAL_CLAUSES:
            self.cur_word = self.cur_word[:-2] + " " + "=se"
            return True
        return False

    def segment_hortatives(self):
        if self.cur_word in self.HORTATIVE_PARTICLES:
            if self.next_word and self.next_word in self.FIRST_PERSON_PGNS:     # if the PGN is separated from the hortative particle by space
                self.next_word = self.CLITIC_SEPARATOR + self.next_word
                self.skip_next = True
                return True
        else:
            for hortative in self.HORTATIVE_PARTICLES:
                if self.cur_word.startswith(hortative):                         # if the clitic is attached to the hortative particle
                    rest_of_word = self.cur_word[len(hortative):]
                    if rest_of_word in self.FIRST_PERSON_PGNS:
                        self.cur_word = hortative + " " + self.CLITIC_SEPARATOR + rest_of_word
                        return True
            return False
