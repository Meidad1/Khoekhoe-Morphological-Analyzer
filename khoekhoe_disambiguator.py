from lemma import Lemma
import re

FIRST_PERSON_CLITICS = {"=ta", "=khom", "=m", "=ge", "=se", "=da"}
VERBAL_POS = {"v.tr.act", "v.intr.act", "v.ditr.act", "v.tr.st", "v.intr.st"}
FIRST_PERSON_PGNS = {"-khom", "-m", "-ge", "-se", "-da"}
SECOND_PERSON_PGNS = {"-ts", "-s", "-kho", "-ro", "-go", "-so", "-du"}
ENGLISH_AUX_VERBS = {"am", "is", "are", "was", "were"}
NOMINAL_SUFFIXES = {"-b", "-s", "-da", "-di", "-du", "-ge", "-go", "-hâ", "-i", "-in", "-n", "-kha", "-kho",
                    "-khom", "-m", "-ra", "-se", "-so", "-ta", "-ts"}   # -gu is not included because it is also a verbal suffix
VERBAL_SUFFIXES = {"-sen", "-ba", "-he"}
GENDER_SUFFIXES_MAP = {"m": {"-b", "-kha", "-gu"},
                       "f": {"-s", "-ra", "-di"},
                       "c": {"-i", "-ra", "-n"}
                       }


class KhoekhoeDisambiguator:

    @staticmethod
    def decl_vs_pst(is_second_ge: bool):                         # ge
        if is_second_ge:
            return "PST", "ptcl"
        return "DECL", "ptcl"

    @staticmethod
    def firstExcl_vs_femObj(mb_next: str):
        if mb_next:                         # if there is element after "si", it is probably 1EXCL
            return "1EXCL", "pro"
        return "2F.SG.OBJ", "pro"

    @staticmethod
    def hort_vs_stata(cur_ann: str, fte_line: str, next_annotation: str):
        if "let" in fte_line and next_annotation in FIRST_PERSON_CLITICS:
            return "HORT", "ptcl"
        elif cur_ann == "a":
            return "STATa", "ptcl"
        elif cur_ann in {"ǀkhī", "hā"}:
            return "come", "v.intr.act"
        return cur_ann, cur_ann

    @staticmethod
    def xa_postp(fte_line: str):                                 # xa postp          #TODO check the frequency of it, maybe it would be better than looking in the translation
        # look for "by" or "about" in translation
        if "by " in fte_line:
            return "by", "postp"
        return "about", "postp"

    @staticmethod
    def pgn_vs_recp(fte_line: str):                              # -gu
        if "each other" in fte_line:
            return "-RECP", "-vsf"
        return "-3M.PL", "-nsf"

    @staticmethod
    def poss1_vs_quot_vs_1sg(tx_line: str, fte_line: str):       # ti
        if "my " in fte_line or "mine." in fte_line or "mine " in fte_line or "mine, " in fte_line:
            return "1SG.POSS", "pro"                             # TODO find a stronger indication for cases in which both "my" and "I" occur
        elif "i " in fte_line or "ti -ta" in tx_line:            # TODO better to check whether the next annotation is '-ta'
            return "1SG", "pro"
        return "QUOT", "ptcl"

    @staticmethod
    def poss2_vs_2pro_1incl(fte_line: str, mb_next: str):                      # 'sa' morpheme
        if mb_next in FIRST_PERSON_PGNS:
            return "1INCL", "pro"
        elif mb_next in SECOND_PERSON_PGNS:
            return "2", "pro"
        elif "your " in fte_line:
            return "2SG.POSS", "pro"
        else:
            return "sa", "sa"

    @staticmethod
    def yes_vs_interj(fte):
        if "yes" in fte or "yeah" in fte:
            return "yes", "interj"
        return "so_that", "conj"

    @staticmethod
    def conj_o(tx_ann: str, mb_prev: str):
        if tx_ann[0].lower() == "o" or mb_prev == "o":               # if "o" is sentence initial or follows another "o" --> it is "then"
            return "then", "conj"
        return "when", "conj"

    @staticmethod
    def dist_vs_fall(fte: str):
        if "fall" in fte:
            return "fall", "v.intr.act"
        return "DIST", "dem"

    @staticmethod
    def we_vs_arrive(fte_line: str):                             # sī
        if "we " in fte_line:
            return "1EXCL", "pro"
        return "arrive", "vitr"

    @staticmethod
    def particle_ha(ge_prev, fte: str):
        if ge_prev == "tama":
            return "NEG.AUX", "ptcl"
        elif ge_prev == "ǃnâ" or \
                "there is" in fte or \
                "there are" in fte or \
                "is there" in fte or \
                "are there" in fte:
            return "COP.LOC", "cop"
        return "PFV", "ptcl"

    @staticmethod
    def axase_cop(ge_next):
        if ge_next == "=se":
            return "STATaxa", "ptcl"
        return "child", "n"

    @staticmethod
    def manner_se(mb_prev):
        if mb_prev in ["axa", "tama"]:
            return "=MANNER", "=cl"
        return "=se", "=se"

    @staticmethod
    def disambiguate(possible_senses: list[Lemma], fte_line: str, next_mb: str) -> int:
        """
        :param possible_senses: A list of possible senses to gloss as pairs (tuples) of (ge, ps)
        :param fte_line: string of the translation
        :param next_mb: string of the next mb annotation
        :return: The index which indicates the chosen option
        """
        if len(possible_senses) == 1:
            return 0
        is_noun = next_mb in NOMINAL_SUFFIXES
        is_verb = next_mb in VERBAL_SUFFIXES
        if not fte_line:
            if is_noun:
                for i in range(len(possible_senses)):
                    if possible_senses[i].ps == "n":            # if you find a noun, return it
                        return i
            return 0

        for i in range(len(possible_senses)):
            ge = possible_senses[i].ge.replace('_', " ")
            ps = possible_senses[i].ps
            gender = possible_senses[i].gender
            other_trans = possible_senses[i].other_translations
            all_optional_trans = "(" + ge
            for trans in other_trans:
                all_optional_trans += "|" + trans
            all_optional_trans += ")"
            if re.search("\\b" + all_optional_trans + "\\b", fte_line):
                if is_noun and not is_verb and ps == "n":
                    # if next_mb in GENDER_SUFFIXES_MAP[gender]:        # not applicable now, because there is not much data in 'gender' column
                    return i
                elif not is_noun and ps != "n":
                    return i
            elif re.search(all_optional_trans, fte_line):
                if is_noun and not is_verb and ps == "n":
                    # if gender and next_mb in GENDER_SUFFIXES_MAP[gender]:
                    return i
                elif not is_noun and ps != "n":
                    return i
            elif not is_noun and ps in VERBAL_POS and ge[-1] == "e":
                if re.search("\\b" + ge[:-1] + "ing\\b", fte_line):
                    return i
        return 0
