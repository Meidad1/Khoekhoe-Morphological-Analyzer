from speach import elan
import eaf_parser
import preprocessing.annotation_cleaner as annotation_cleaner
import preprocessing.morpheme_breaker as morpheme_breaker
import langdetect


class Preprocessor:
    CLICKS_SET = {"ǃ", "ǂ", "ǁ", "ǀ"}
    QUOTE_MARKS = ['"', '“', '”']
    NON_CAPITALIZED_WORDS = {"Skoli", "Skol", "Tsî", "ǁNā", "ǀGui", "ǁÎb", "Ā", "ǂGuro", "ǁAri", "Xawe"}

    def __init__(self, input_eaf_path, output_eaf_path, capitalized_words_path, auto_detect_english: bool,
                 capitalized_words: set, words_not_to_segment: dict, paralinguistic_items: dict, adverbs: set):
        self.adverbs = adverbs
        self.forms_not_to_segment = set(words_not_to_segment["FormsNotToSegment"])
        self.nominals_not_to_segment = set(words_not_to_segment["NominalsNotToSegment"])
        self.input_path = input_eaf_path
        self.output_path = output_eaf_path
        self.eaf = elan.read_eaf(input_eaf_path)            # Doc object
        self.eaf_parser = eaf_parser.EAF_Parser(self.eaf)
        self.tx_indexes = self.eaf_parser.get_tx_indexes()
        self.speakers_num = len(self.tx_indexes)
        self.tx_to_fte = self.eaf_parser.get_tx_fte_annotations_mapping()
        self.tx_to_orig_idx_dict = self.eaf_parser.get_tx_to_orig_tiers_mapping()      # mapping between indexes of tx tiers to their corresponding orig tier indexes
        self.annotation_cleaner = annotation_cleaner.AnnotationCleaner()
        self.capitalized_words_set = capitalized_words
        self.paralinguistic_items = paralinguistic_items
        new_capitalized_words = self.find_capitalized_words()                       # find and add new capitalized words to capitalized_words_set
        write_new_capitalized(new_capitalized_words, capitalized_words_path)        # write the new capitalized words to the file
        self.automatically_detect_English = auto_detect_english

    def preprocess_file(self):
        """
        Handles the whole preprocessing of an Elan file, including the following operations for each tx annotation:
        1. Validation of encoding
        2. Copying tx to orig tier
        3. Language detection - marking <English> on annotations of parts in English
        4. Fixing misspellings in tx tier
        5. Cleaning - removing punctuation and decapitalizing
        6. Morphological segmentation
        7. Saving as a new output file
        """
        if len(self.tx_indexes) != len(self.eaf_parser.orig_indexes) or \
                len(self.tx_indexes) != len(self.eaf_parser.fte_indexes):
            print("There is a problem with the tiers format of input file " + self.input_path)
            return

        for tx_idx in self.tx_indexes:
            dst_orig_idx = self.tx_to_orig_idx_dict[tx_idx]
            for tx_annotation in self.eaf.tiers()[tx_idx]:
                self.annotation_cleaner.set_annotation(tx_annotation.value)
                tx_annotation.value = self.annotation_cleaner.validate_encoding()            # validation of encoding must be done before copying to original tier
                self.copy_tx_to_orig(dst_orig_idx, tx_annotation)

                cur_fte_annotation = ""  # Sometimes there is no translation available, so we first initiate this value to be an empty string
                if tx_annotation.ID in self.tx_to_fte.keys():
                    cur_fte_annotation = self.eaf.annotation(self.tx_to_fte[tx_annotation.ID]).value  # the corresponding translation/fte annotation (String)
                    cur_fte_annotation = self.annotation_cleaner.validate_fte_backchannel(cur_fte_annotation)
                    cur_fte_annotation = self.annotation_cleaner.handle_lexical_backchannel(cur_fte_annotation)
                    self.eaf.annotation(self.tx_to_fte[tx_annotation.ID]).value = cur_fte_annotation

                if (self.automatically_detect_English and langdetect.detect(tx_annotation.value) == "en") or \
                        ("[english]" in cur_fte_annotation.lower()):                                 # English detection
                    tx_annotation.value = "<English> " + tx_annotation.value
                    continue

                tx_annotation.value = self.annotation_cleaner.clean_annotation(self.capitalized_words_set)          # clean annotation
                tx_annotation.value = self.annotation_cleaner.fix_orthography_in_tx_tier()
                cur_morpheme_breaker = morpheme_breaker.MorphemeBreaker(tx_annotation.value,
                                                                        cur_fte_annotation,
                                                                        self.forms_not_to_segment,
                                                                        self.nominals_not_to_segment,
                                                                        self.paralinguistic_items,
                                                                        self.adverbs)
                tx_annotation.value = cur_morpheme_breaker.break_annotation_to_morphemes()                          # break/segment annotation to morphemes

                self.annotation_cleaner.set_annotation(tx_annotation.value)
                tx_annotation.value = self.annotation_cleaner.fix_orthography_in_tx_tier()

        self.eaf.save(self.output_path)                 # save and export to a new output eaf file

    def copy_tx_to_orig(self, dst_orig_idx, tx_annotation):
        for orig_annotation in self.eaf.tiers()[dst_orig_idx]:
            if orig_annotation.ref_id == tx_annotation.ID:                  # if there is already an existing annotation in orig
                orig_annotation.value = tx_annotation.value                     # update the value
                return
        # if there is no existing orig annotation, we will create a new one:
        self.eaf.tiers()[dst_orig_idx].new_annotation(tx_annotation.value, ann_ref_id=tx_annotation.ID)          # copy to orig

    def find_capitalized_words(self):
        """
        Finds all capitalized words (i.e., words that should be left capitalized) in the text before preprocessing the file.
        :return: A set of new capitalized words added to the general set (given by the txt file).
        """
        new_capitalized_words = set()
        for tx_idx in self.tx_indexes:
            cur_tx = self.eaf.tiers()[tx_idx]
            for tx_annotation in cur_tx:
                annot_word_list = tx_annotation.value.split()
                for i in range(1, len(annot_word_list)):                   # iterating over all non-initial words in the tier
                    prev_word = annot_word_list[i-1]
                    cur_word = annot_word_list[i]
                    if len(prev_word) > 0 and prev_word[-1] in (['!', ":", "?", "ǃ", "\n"] + self.QUOTE_MARKS):     # It looks like usually the following word after these marks is capitalized
                        continue
                    elif annot_word_list[i][0] in self.QUOTE_MARKS:
                        continue

                    cur_word = self.annotation_cleaner.validate_single_word(cur_word)     # validating and cleaning cur_word
                    cur_word = self.annotation_cleaner.clean_punctuation_of_single_word(cur_word)

                    if cur_word in self.NON_CAPITALIZED_WORDS:
                        continue

                    if len(cur_word) > 0:
                        char_to_check = cur_word[0]
                        if cur_word[0] in self.CLICKS_SET:                         # if the first letter is a click
                            if len(cur_word) > 1:
                                char_to_check = cur_word[1]
                        if char_to_check.isupper():
                            if cur_word not in self.capitalized_words_set.union(morpheme_breaker.MorphemeBreaker.CONJUNCTIONS,
                                                                                self.forms_not_to_segment):
                                new_capitalized_words.add(cur_word)
                                self.capitalized_words_set.add(cur_word)
        return new_capitalized_words


def write_new_capitalized(new_capitalized_words, capitalized_words_path):
    with open(capitalized_words_path, "a", encoding='utf-8') as file:
        for word in new_capitalized_words:
            file.write(word + "\n")
