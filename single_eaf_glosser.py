from speach import elan
from eaf_parser import *
from khoekhoe_disambiguator import KhoekhoeDisambiguator as kkd
import preprocessing.annotation_cleaner as annotation_cleaner


class SingleEafGlosser:
    HORTATIVE_PARTICLES = {"a", "ǀkhī", "ā"}

    def __init__(self, input_eaf_path: str, capitalized_words: set, paralinguistic_items: dict):
        self.eaf = elan.read_eaf(input_eaf_path)            # eaf is an object of type Doc. Doc object consists of Tier objects, which consist of Annotation objects
        self.eaf_parser = EAF_Parser(self.eaf)
        self.ge_indexes = self.eaf_parser.get_ge_indexes()
        self.tx_indexes = self.eaf_parser.get_tx_indexes()
        self.ge_to_ps = self.eaf_parser.get_ge_to_ps_tiers_mapping()
        self.tx_to_fte = self.eaf_parser.get_tx_fte_annotations_mapping()
        self.tx_to_orig_idx_dict = self.eaf_parser.get_tx_to_orig_tiers_mapping()
        self.cur_tx_id = 0
        self.is_second_ge = False
        self.annotation_cleaner = annotation_cleaner.AnnotationCleaner()
        self.capitalized_words_set = capitalized_words
        self.back_channels = set(paralinguistic_items["BackChannels"])
        self.fillers = set(paralinguistic_items["Fillers"])

    def gloss_file(self, gram_glossing_dict, lex_glossing_dict):
        for ge_idx in self.ge_indexes:
            ps_idx = self.ge_to_ps[ge_idx]
            mb_idx = self.eaf_parser.get_mb_idx_according_to_ge(ge_idx)
            ge = self.eaf.tiers()[ge_idx]                   # ge, ps and mb are Tier objects
            ps = self.eaf.tiers()[ps_idx]
            mb = self.eaf.tiers()[mb_idx]

            for i in range(len(ge.annotations)):            # iterate over all annotations
                self.update_cur_tx_ann(ge, i)
                self.gloss_single_annotation(ge, ps, mb, i, gram_glossing_dict, lex_glossing_dict)

        self.copy_orig_to_tx()
        self.final_tx_cleaning()
        self.add_brackets_to_tx()

    def update_cur_tx_ann(self, ge: Tier, cur_index: int):                      # cur_index --> index of cur annotation
        cur_ge_ann = ge.annotations[cur_index]
        next_tx_id = self.eaf.annotation(cur_ge_ann.ref_id).ref_id                 # tx.id -> ref_id(mb) -> ref_id(ref_id(ge))
        if next_tx_id != self.cur_tx_id:
            self.cur_tx_id = next_tx_id
            self.is_second_ge = False

    def gloss_single_annotation(self, ge: Tier, ps: Tier, mb: Tier, i: int, gram_glossing_dict, lex_glossing_dict):     # i --> index of cur annotation
        tx_ann = self.eaf.annotation(self.cur_tx_id).value
        ge_ann = ge.annotations[i]
        ge_ann_val = ge_ann.value
        ps_ann = ps.annotations[i]
        mb_prev = None
        if i-1 >= 0:
            mb_prev = mb.annotations[i-1].value
        if i+1 < len(ge.annotations):
            mb_next = mb.annotations[i+1].value
        else:
            mb_next = None
        res = (ge.annotations[i].value, ps.annotations[i].value)
        cur_fte = ""
        if self.cur_tx_id in self.tx_to_fte.keys():
            cur_fte = self.eaf.annotation(self.tx_to_fte[self.cur_tx_id]).value.lower()
        if ge_ann_val == "ge":
            res = kkd.decl_vs_pst(self.is_second_ge)
            self.is_second_ge = True
        elif cur_fte in ["[backchannel]", "[laughter]", "[cough]", "[gasp]",                # cur_fte is lowered above!
                         "[nose]", "[throat]", "[moan]", "[groan]"]:
            res = cur_fte.upper(), cur_fte.upper()
        elif ge_ann_val in self.HORTATIVE_PARTICLES:
            res = kkd.hort_vs_stata(ge_ann_val, cur_fte, mb_next)
        elif ge_ann_val == "o":
            res = kkd.conj_o(tx_ann, mb_prev)
        elif ge_ann_val == "axa":
            res = kkd.axase_cop(mb_next)
        elif ge_ann_val == "ai" and mb_next == "-s":
            res = "front", "n"
        elif ge_ann_val == "xa":
            res = kkd.xa_postp(cur_fte)
        elif ge_ann_val == "-gu":
            res = kkd.pgn_vs_recp(cur_fte)
        elif ge_ann_val == "î":
            res = kkd.yes_vs_interj(cur_fte)
        elif ge_ann_val == "ti":
            res = kkd.poss1_vs_quot_vs_1sg(self.eaf.annotation(self.cur_tx_id).value, cur_fte)
        elif ge_ann_val == "sa" or ge_ann_val == "sā":
            res = kkd.poss2_vs_2pro_1incl(cur_fte, mb_next)
        elif ge_ann_val == "sī":
            res = kkd.we_vs_arrive(cur_fte)
        elif ge_ann_val == "si":
            res = kkd.firstExcl_vs_femObj(mb_next)
        elif ge_ann_val == "hâ":
            res = kkd.particle_ha(mb_prev, cur_fte.lower())
        elif ge_ann_val == "ǁnā":
            res = kkd.dist_vs_fall(cur_fte.lower())
        elif ge_ann_val == "=se":
            res = kkd.manner_se(mb_prev)
        elif ge_ann_val in gram_glossing_dict:                      # if there is no ambiguity or a special case --> search in the grammatical glossing dictionary
            possible_senses = gram_glossing_dict[ge_ann_val]        # each sense is an instance of Lemma class
            chosen_idx = kkd.disambiguate(possible_senses, cur_fte, mb_next)
            res = possible_senses[chosen_idx].ge, possible_senses[chosen_idx].ps
        elif ge_ann_val in lex_glossing_dict:                       # otherwise, search in the lexical dictionary
            possible_senses = lex_glossing_dict[ge_ann_val]
            chosen_idx = kkd.disambiguate(possible_senses, cur_fte, mb_next)
            res = possible_senses[chosen_idx].ge, possible_senses[chosen_idx].ps
        elif ge_ann_val.lower() in lex_glossing_dict:
            possible_senses = lex_glossing_dict[ge_ann_val.lower()]
            chosen_idx = kkd.disambiguate(possible_senses, cur_fte, mb_next)
            res = possible_senses[chosen_idx].ge, possible_senses[chosen_idx].ps

        ge_ann.value, ps_ann.value = res[0], res[1]

    def copy_orig_to_tx(self):
        for tx_idx in self.tx_indexes:
            equivalent_orig_idx = self.tx_to_orig_idx_dict[tx_idx]
            for tx_annotation in self.eaf.tiers()[tx_idx]:
                for orig_annotation in self.eaf.tiers()[equivalent_orig_idx]:
                    if orig_annotation.ref_id == tx_annotation.ID:
                        tx_annotation.value = orig_annotation.value
                        break

    def final_tx_cleaning(self):
        for tx_idx in self.tx_indexes:
            for tx_annotation in self.eaf.tiers()[tx_idx]:
                self.annotation_cleaner.set_annotation(tx_annotation.value)
                tx_annotation.value = self.annotation_cleaner.clean_annotation(self.capitalized_words_set)
                tx_annotation.value = self.annotation_cleaner.fix_orthography_in_tx_tier()

    def add_brackets_to_tx(self):
        """
        Adds round brackets with missing consonants in the pronunciation and square brackets to paralinguistic items.
        :return: None
        """
        for tx_idx in self.tx_indexes:
            equivalent_orig_idx = self.tx_to_orig_idx_dict[tx_idx]
            for tx_annotation in self.eaf.tiers()[tx_idx]:
                for orig_annotation in self.eaf.tiers()[equivalent_orig_idx]:
                    if orig_annotation.ref_id == tx_annotation.ID:
                        tx_lst = tx_annotation.value.split()
                        for i in range(len(tx_lst)):
                            if "tare" in tx_lst[i] and "tae" in orig_annotation.value:
                                tx_lst[i] = tx_lst[i].replace("tare", "ta(r)e")
                            elif "tari" in tx_lst[i] and "tai" in orig_annotation.value:
                                tx_lst[i] = tx_lst[i].replace("tari", "ta(r)i")
                            elif tx_lst[i] == "garu" and "gau" in orig_annotation.value:
                                tx_lst[i] = "ga(r)u"
                            elif tx_lst[i] in self.back_channels or tx_lst[i] in self.fillers:
                                tx_lst[i] = "[" + tx_lst[i] + "]"
                        tx_annotation.value = " ".join(tx_lst)

    def save_file(self, output_path: str):
        self.eaf.save(output_path)