from speach import elan
from eaf_parser import *
from ambiguity_removing import *


class SingleEafGlosser:

    def __init__(self, input_eaf_path: str):
        self.input_eaf_path = input_eaf_path
        self.eaf = elan.read_eaf(self.input_eaf_path)    # eaf is an object of type Doc. Doc object consists of Tier objects, which consist of Annotation objects
        self.xml_parser = EAF_Parser(self.eaf)
        self.ge_indexes = self.xml_parser.get_all_ge_indexes()
        self.ge_to_ps = self.xml_parser.get_ge_to_ps_tiers_mapping()
        self.tx_to_fte = self.xml_parser.get_tx_fte_annotations_mapping()
        self.cur_tx_id = 0
        self.is_second_ge = False

    def gloss_file(self, morph_glossing_dict, lex_glossing_dict):
        for ge_idx in self.ge_indexes:
            ps_idx = self.ge_to_ps[ge_idx]
            ge = self.eaf.tiers()[ge_idx]
            ps = self.eaf.tiers()[ps_idx]           # ge and ps are Tier objects
            for i in range(len(ge.annotations)):
                self.update_cur_tx_ann(ge, i)
                self.gloss_single_annotation(ge, ps, i, morph_glossing_dict, lex_glossing_dict)

    def update_cur_tx_ann(self, ge: Tier, cur_index: int):                      # cur_index --> index of cur annotation
        cur_ann = ge.annotations[cur_index]
        next_tx_id = self.eaf.annotation(cur_ann.ref_id).ref_id                 # tx.id -> ref_id(mb) -> ref_id(ref_id(ge))
        if next_tx_id != self.cur_tx_id:
            self.cur_tx_id = next_tx_id
            self.is_second_ge = False

    def gloss_single_annotation(self, ge: Tier, ps: Tier, i: int, morph_glossing_dict, lex_glossing_dict):     # i --> index of cur annotation
        ge_ann = ge.annotations[i]
        ps_ann = ps.annotations[i]
        res = (ge.annotations[i].value, ps.annotations[i].value)
        cur_fte = ""
        if self.cur_tx_id in self.tx_to_fte.keys():
            cur_fte = self.eaf.annotation(self.tx_to_fte[self.cur_tx_id]).value.lower()
        if ge_ann.value == "ge":
            res = decl_vs_pst(self.is_second_ge)
            self.is_second_ge = True
        elif ge_ann.value == "a":
            res = hort_vs_stata(cur_fte)
        elif ge_ann.value == "xa":
            res = xa_postp(cur_fte)
        elif ge_ann.value == "-gu":
            res = pgn_vs_recp(cur_fte)
        elif ge_ann.value == "ti":
            res = poss1_vs_quot_vs_1sg(self.eaf.annotation(self.cur_tx_id).value, cur_fte)
        elif ge_ann.value == "sa":
            res = poss2_vs_2pro_1incl(cur_fte)
        elif ge_ann.value == "sī":
            res = we_vs_arrive(cur_fte)
        elif ge_ann.value in morph_glossing_dict.keys():              # if there is no ambiguity --> search in the morphological glossing table
            res = morph_glossing_dict[ge_ann.value][0], morph_glossing_dict[ps_ann.value][1]
        elif ge_ann.value in lex_glossing_dict.keys():
            res = lex_glossing_dict[ge_ann.value][0], lex_glossing_dict[ps_ann.value][1]
        elif ge_ann.value.lower() in lex_glossing_dict.keys():
            res = lex_glossing_dict[ge_ann.value.lower()][0], lex_glossing_dict[ps_ann.value.lower()][1]

        if "/" in res[0]:
            ge_options = res[0].split("/")
            ps_options = res[1].split("/")
            option_idx = solve_lexical_ambiguity(ge_options, ps_options, cur_fte, self.eaf.annotation(self.cur_tx_id))
            res = ge_options[option_idx], ps_options[option_idx]
        ge_ann.value, ps_ann.value = res[0], res[1]

    def save_file(self, output_path: str):
        self.eaf.save(output_path)
