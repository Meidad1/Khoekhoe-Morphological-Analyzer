import xml.etree.ElementTree as ET
from speach.elan import *


class EAF_Parser:

    def __init__(self, eaf: Doc):
        self.eaf = eaf
        self.xml = self.eaf.to_xml_str()
        self.root = ET.fromstring(self.xml)             # creating an element tree object
        tiers_indexes = self.find_tiers_indexes()
        self.tx_indexes, self.fte_indexes, self.orig_indexes, self.ge_indexes, self.ps_indexes = \
            tiers_indexes[0], tiers_indexes[1], tiers_indexes[2], tiers_indexes[3], tiers_indexes[4]

    def get_tx_fte_annotations_mapping(self):
        tx_to_fte = {}
        for fte_idx in self.fte_indexes:
            cur_fte_tier = self.eaf.tiers()[fte_idx]
            for fte_annotation in cur_fte_tier:
                tx_to_fte[fte_annotation.ref_id] = fte_annotation.ID
        return tx_to_fte

    def get_tx_to_orig_tiers_mapping(self):    # mapping between indexes of tx tiers to their corresponding orig tier indexes
        """
        Finds the mapping between the indexes of tx tiers to the corresponding indexes of orig tiers
        :return: dict in the following format: {tx_tier_idx : orig_tier_idx}
        """
        tx_to_orig = {}
        for orig_idx in self.orig_indexes:
            for tx_idx in self.tx_indexes:
                if self.eaf.tiers()[orig_idx].parent_ref == self.eaf.tiers()[tx_idx].name:
                    tx_to_orig[tx_idx] = orig_idx
                    break
        return tx_to_orig

    def get_ge_to_ps_tiers_mapping(self):
        """
        Finds the mapping between the indexes of ge tiers to the corresponding indexes of ps tiers
        :return: dict in the following format: {ge_tier_idx : ps_tier_idx}
        """
        ge_to_ps = {}
        for ge_idx in self.ge_indexes:
            for ps_idx in self.ps_indexes:
                # ge and ps have the same parent (which is mb tier)
                if self.eaf.tiers()[ge_idx].parent_ref == self.eaf.tiers()[ps_idx].parent_ref:
                    ge_to_ps[ge_idx] = ps_idx
                    break
        return ge_to_ps

    def find_tiers_indexes(self):
        tx_indexes = []
        fte_indexes = []
        orig_indexes = []
        ge_indexes = []
        ps_indexes = []
        for i in range(len(self.eaf.tiers())):
            cur_tier = self.eaf.tiers()[i]
            if cur_tier.linguistic_type.ID == "tx":
                tx_indexes.append(i)
            elif "fte" in cur_tier.name:
                fte_indexes.append(i)
            elif cur_tier.linguistic_type.ID == "orig":
                orig_indexes.append(i)
            elif "ge" in cur_tier.name:
                ge_indexes.append(i)
            elif cur_tier.linguistic_type.ID == "ps":
                ps_indexes.append(i)
        return tx_indexes, fte_indexes, orig_indexes, ge_indexes, ps_indexes

    def get_all_tx_indexes(self):
        return self.tx_indexes

    def get_all_fte_indexes(self):
        return self.fte_indexes

    def get_all_ge_indexes(self):
        return self.ge_indexes

    def get_all_ps_indexes(self):
        return self.ps_indexes
