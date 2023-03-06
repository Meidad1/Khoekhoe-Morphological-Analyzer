class MorphemeBreaker:
    PGN_MORPHEMES = ["ta", "khom", "ge", "da", "ts", "kho", "ro", "go", "so", "du", "b", "s", "kha", "ra", "gu", "di",
                     "n"]             # It is a list because the order matters! For example, "ts" should be checked before "s"
    OBLIQUE_SUFFIXES = {"khoma", "tsa"}
    CONJUNCTIONS = {"î", "o", "osa", "xawe", "xabe", "tsî", "hîa", "amaga", "ǁnā-amaga", "nēti", "ǃnâ"}
    UNSEGMENTED_FORMS = {"mâpa", "mâǁae", "mâtikō", "tare", "tare-i", "tari", "ai", "aiǃâ", "aiǂama", "khaoǃgâ", "khami",
                         "khama", "kōse", "tawa", "ose", "xa", "xu", "xōri", "ǀî", "ǁaegu", "ǁga", "ǀkha", "ǂama", "ǃaroma",
                         "ǃoa", "ǃoa-ai", "ǃoagu", "ǃgao", "ǃnâ", "ǂamai", "ǂamǃnâ", "ǃna", "ǂnamipe", "tsîn", "xabe",
                         "mati", "mâti", "mapa", "ǃnâ-ū", "kose", "nē", "ǁnā", "nau", "tama", "kha", "nēba"
                         "go", "ge", "goro", "gere", "ra", "ga", "ka", "nî", "a", "di", "ti", "sa", "si", "sī",
                         "tī", "sā", "hâ", "kara", "nîra", "tite", "re", "bi", "te",
                         "ǂguro", "ǃnona", "ǃnāsa", "ǃora", "koro"}
    UNSEGMENTED_NOMINALS = {"collage", "college", "gangan", "Kavango", "china", "China", "aio"}
    PERSONAL_PRO_STEMS = {"ti", "sa", "si", "sī", "tī", "sā", "ǁî"}
    FREE_PGN_MARKERS = {"ta", "da", "du", "gu"}
    CLITIC_SEPARATOR = "="
    SUFFIX_SEPARATOR = "-"
    CLICKS_SET = {"ǃ", "ǂ", "ǁ", "ǀ"}

    def __init__(self, tx_annotation: str, fte_annotation: str):
        self.ann_lst = tx_annotation.split()
        self.fte_annotation = fte_annotation
        self.cur_word = None
        self.previous_word = None
        self.next_word = None

    # *** Ambiguities and issues: ***
    # enclitics and regular PGN:
    #   if the morpheme == "ta" or "du" and not written as one word, we ignore it because it clashes with free morphemes as "di" and "ta"
    # What should we do with -s-a and -sa of adjective which we do not segment?
    def break_annotation_to_morphemes(self):
        """
        Performs morpheme segmentation of self.cur_word.
        :return: the result as a String
        """
        for i in range(len(self.ann_lst)):
            if i > 0:
                self.previous_word = self.ann_lst[i-1]
            if (i + 1) < len(self.ann_lst):
                self.next_word = self.ann_lst[i+1]
            self.cur_word = self.ann_lst[i]

            if not self.is_breakable():               # If a word should not be segmented --> continue to the next iteration
                continue
            if self.segment_free_pgn():               # handle free 'ta' 1SG and 'da' 1PL
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
        if self.cur_word in self.UNSEGMENTED_FORMS or self.cur_word in self.UNSEGMENTED_NOMINALS:
            return False
        elif self.cur_word in self.CONJUNCTIONS:
            return False
        elif self.cur_word.endswith("se"):
            return False
        elif self.cur_word.endswith("m") and not self.cur_word.endswith("khom"):
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
            self.cur_word = self.cur_word[:-2] + " " + ends_with      # update cur_word
            return True
        return False

    def segment_free_pgn(self):
        """
        Segments free pgn markers, as 'ta' (1SG),'da' (1PL), 'du', 'gu', 'i' (3C.SG).
        :return: True if a change is done, False otherwise.
        """
        if self.cur_word == "i" or self.cur_word in self.PGN_MORPHEMES:
            if self.previous_word and self.next_word:                               # check whether next and previous are not None
                if self.previous_word == "o" and self.next_word == "ge":            # check the pattern "o PGN ge" --> "o =PGN ge"
                    self.cur_word = self.CLITIC_SEPARATOR + self.cur_word
                    return True
        elif self.cur_word in self.FREE_PGN_MARKERS:
            separator_char = self.SUFFIX_SEPARATOR
            if self.previous_word is not None and self.previous_word not in self.PERSONAL_PRO_STEMS:
                separator_char = self.CLITIC_SEPARATOR
            self.cur_word = separator_char + self.cur_word
            return True

        return False

    def segment_pgn(self, word):
        """
        Segments pgn suffixes and enclitics of a given word.
        :return: If word ends with pgn --> returns the segmented string, otherwise --> returns None
        """
        separator_char = self.SUFFIX_SEPARATOR
        for morpheme in self.PGN_MORPHEMES:
            if word.endswith(morpheme):
                prefix = word[:-len(morpheme)]
                if len(prefix) == 0:
                    continue

                # # DIM suffix
                # if (prefix.endswith("ro")) and (len(prefix) > 2) and (prefix not in self.CONJUNCTIONS) and \
                #         (prefix not in self.UNSEGMENTED_FORMS):
                #     prefix = prefix[:-2] + " -ro"
                # #

                if prefix in self.CONJUNCTIONS or prefix in self.UNSEGMENTED_FORMS:
                    separator_char = self.CLITIC_SEPARATOR
                if prefix in self.PERSONAL_PRO_STEMS:                     # for example: tita, sādu --> ti -ta, sā -du
                    separator_char = self.SUFFIX_SEPARATOR
                return prefix + " " + separator_char + morpheme
        if word.endswith("i") and self.segment_i_pgn(word):               # 3C.SG PGN ('i')
            return word[:-1] + " -i"

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
        if word.endswith("bahe"):                  # APPL + PASS
            return word[:-4] + " -ba" + " -he"
        elif word.endswith("he"):                  # PASS
            return word[:-2] + " -he"
        elif word.endswith("basen"):               # APPL + REFL
            return word[:-5] + " -ba" + " -sen"
        elif word.endswith("sen"):
            if "self" in self.fte_annotation or "selves" in self.fte_annotation:
                return word[:-3] + " -sen"
            else:
                return word
        elif word.endswith("babi") or word.endswith("basi") or word.endswith("bate"):         # APPL + OBJ marker
            return word[:-4] + " -ba " + word[-2:]                                            # OBJ markers should be separated with space
        elif word.endswith("ba") and idx == len(self.ann_lst) - 1:              # APPL in the end of sentences
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
        elif word == "tsîna":
            return "tsîn -a"                            # Might be also "tsî =n -a"
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
