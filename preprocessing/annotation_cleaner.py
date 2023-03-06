class AnnotationCleaner:
    PUNCTUATION_MARKS = ['"', "“", "”", "‘", "’", '(', ')']
    FINAL_INITIAL_PUNCTUATION_MARKS = [";", "?", "…", "!", ",", ".", ":"]

    # The following validity list consists of tuples of ("x", "y"), where "y" is the valid encoding of "x".
    COMPLEX_CHARS_VALIDITY_LIST = [("î", "î"), ("Î", "Î"), ("ô", "ô"), ("Ô", "Ô"), ("â", "â"), ("Â", "Â"),
                                   ("ê", "ê"),
                                   ("Ê", "Ê"), ("û", "û"), ("Û", "Û"), ("ā", "ā"), ("Ā", "Ā"), ("ē", "ē"),
                                   ("Ē", "Ē"),
                                   ("ī", "ī"), ("Ī", "Ī"), ("ō", "ō"), ("Ō", "Ō"), ("ū", "ū"), ("Ū", "Ū")]
    CLICK_CHARS_VALIDITY_LIST = [("!", "ǃ"), ("#", "ǂ"), ("||", "ǁ"), ("|", "ǀ"), ("=", "ǂ")]

    def __init__(self):
        self.cur_annotation = None  # cur_annotation is a list of strings

    def set_annotation(self, annotation: str):
        self.cur_annotation = annotation.split()

    def validate_encoding(self):
        """
        Validates the encoding of self.cur_annotation's characters
        :return: The validated string of the annotation
        """
        for i in range(len(self.cur_annotation)):
            self.cur_annotation[i] = self.validate_single_word(self.cur_annotation[i])
        return " ".join(self.cur_annotation)

    def validate_single_word(self, word: str):
        for pair in self.COMPLEX_CHARS_VALIDITY_LIST:
            word = word.replace(pair[0], pair[1])                    # pair[0] is the invalid encoding
        for pair in self.CLICK_CHARS_VALIDITY_LIST:
            prefix_with_valid_clicks = word[:-1].replace(pair[0], pair[1])
            word = prefix_with_valid_clicks + word[-1]
        if not word.startswith("tsītsī") and word.startswith("tsī"):
            word = word.replace("tsī", "tsî")
        return word

    def clean_annotation(self, capitalized_words_set):
        """
        Removes (almost) all punctuation marks in self.cur_annotation and decapitalizes all the words except for proper nouns.
        :param capitalized_words_set: a Set of words that should be kept capitalized
        :return: the clean annotation as string
        """
        if self.cur_annotation is not None and len(self.cur_annotation) > 0:
            self.clean_punctuation()
            self.decapitalize_annotation(capitalized_words_set)
            return " ".join(self.cur_annotation)
        else:
            return ""

    def clean_punctuation(self):
        for i in range(len(self.cur_annotation)):  # iterating over each word in the annotation
            self.cur_annotation[i] = self.clean_punctuation_of_single_word(self.cur_annotation[i])

    def clean_punctuation_of_single_word(self, word):
        """
        Cleans punctuation marks of one word.
        :param word: String
        :return: The clean word
        """
        for mark in self.PUNCTUATION_MARKS:
            word = word.replace(mark, "")
        while len(word) > 0 and word[-1] in self.FINAL_INITIAL_PUNCTUATION_MARKS:
            word = word[:-1]
        while len(word) > 0 and word[0] in self.FINAL_INITIAL_PUNCTUATION_MARKS:  # for example: "...blah blah"
            word = word[1:]
        return word

    def decapitalize_annotation(self, capitalized_words_set):
        if self.cur_annotation[0] not in capitalized_words_set:
            self.cur_annotation[0] = self.cur_annotation[0].lower()
