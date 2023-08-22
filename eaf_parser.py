import xml.etree.ElementTree as ET
import xml.dom.minidom
from speach.elan import *
import re


class EAF_Parser:

    def __init__(self, eaf: Doc):
        self.eaf = eaf
        self.xml = self.eaf.to_xml_str()
        self.tree = ET.ElementTree(ET.fromstring(self.xml))
        self.root = self.tree.getroot()
        tiers_indexes = self.find_tiers_indexes()
        self.tx_indexes, self.fte_indexes, self.orig_indexes, self.ge_indexes, self.ps_indexes, self.mb_indexes = \
            tiers_indexes[0], tiers_indexes[1], tiers_indexes[2], tiers_indexes[3], tiers_indexes[4], tiers_indexes[5]
        self.cur_available_ann_id = None
        self.prev_mb_id = None

    def tokenize_all_tx_tiers(self):
        """
        Tokenizes all tx tiers into mb and copies mb to ge and ps tiers.
        :return: None
        """
        self.cur_available_ann_id = 'a' + str(self.find_max_ann_id() + 1)
        for elem in self.root.iter():
            if elem.tag == "TIER" and elem.attrib["LINGUISTIC_TYPE_REF"] == "tx":
                self.tokenize_single_tx_tier(elem)

    def find_max_ann_id(self):
        """
        Finds the annotation id with the highest numeric value.
        :return: integer of the max id
        """
        max_id = 0
        for elem in self.tree.iter():
            if 'ANNOTATION_ID' in elem.attrib.keys():
                cur_id = elem.attrib['ANNOTATION_ID']
                cur_id = int(re.sub(r"\D", "", cur_id))  # removing all non-numeric chars and converting into int
                if cur_id > max_id:
                    max_id = cur_id
        return max_id

    def increment_available_id(self):
        cur_id = int(self.cur_available_ann_id[1:])
        self.cur_available_ann_id = 'a' + str(cur_id + 1)

    def tokenize_single_tx_tier(self, tx_tier: ET.Element):
        """
        Performs the ELAN feature "Tier>Tokenize Tier..." on \tx tier, and writes the results in \mb, \ge and \ps.
        :return: None
        """
        tier_elements = self.get_equivalent_tier_elements(tx_tier)
        mb_tier, ge_tier, ps_tier = tier_elements[0], tier_elements[1], tier_elements[2]
        self.prev_mb_id = None
        for ann in tx_tier:
            alignable_ann = ann[0]
            cur_tx_ann_id = alignable_ann.attrib['ANNOTATION_ID']
            tx_value = ""
            if alignable_ann[0] is not None:
                tx_value = alignable_ann[0].text
            if tx_value and "<English>" not in tx_value:
                self.tokenize_single_tx_ann(tx_value, cur_tx_ann_id, mb_tier, ge_tier, ps_tier)
                self.prev_mb_id = None

    def get_equivalent_tier_elements(self, tx_tier: ET.Element):
        """
        Given a tx_tier Element, this method searched in the ET the mb, ge and ps tiers.
        :param tx_tier: Element of tx tier
        :return: A tuple of mb, ge and ps tier Elements
        """
        tx_tier_id = tx_tier.attrib['TIER_ID']
        mb_tier_id = "mb@" + tx_tier_id[-1]
        ge_tier_id = "ge@" + tx_tier_id[-1]
        ps_tier_id = "ps@" + tx_tier_id[-1]
        mb_tier = None
        ge_tier = None
        ps_tier = None
        for elem in self.root.iter():
            if elem.tag == "TIER":
                if elem.attrib["TIER_ID"] == mb_tier_id:
                    mb_tier = elem
                elif elem.attrib["TIER_ID"] == ge_tier_id:
                    ge_tier = elem
                elif elem.attrib["TIER_ID"] == ps_tier_id:
                    ps_tier = elem
        if mb_tier is None or ge_tier is None or ps_tier is None:
            raise Exception("One of the tiers is missing. Make sure that all files are in the correct form.")

        return mb_tier, ge_tier, ps_tier

    def tokenize_single_tx_ann(self, tx_value: str, tx_ann_id: str,
                               mb_tier: ET.Element, ge_tier: ET.Element, ps_tier: ET.Element):
        tokens = tx_value.split()
        for token in tokens:
            new_mb_ann = self.create_new_ann(tx_ann_id, token, self.prev_mb_id)
            mb_id = new_mb_ann[0].attrib['ANNOTATION_ID']
            self.prev_mb_id = mb_id
            new_ge_ann = self.create_new_ann(mb_id, token)
            new_ps_ann = self.create_new_ann(mb_id, token)
            mb_tier.append(new_mb_ann)
            ge_tier.append(new_ge_ann)
            ps_tier.append(new_ps_ann)

    def create_new_ann(self, ann_ref_id, value, prev_ann_id=None):
        new_ann = ET.Element("ANNOTATION")
        new_ref_ann = ET.Element("REF_ANNOTATION",
                                 {"ANNOTATION_ID": self.cur_available_ann_id, "ANNOTATION_REF": ann_ref_id})
        if prev_ann_id is not None:
            new_ref_ann.attrib["PREVIOUS_ANNOTATION"] = prev_ann_id
        self.increment_available_id()
        new_value = ET.Element("ANNOTATION_VALUE")
        new_value.text = value
        new_ref_ann.append(new_value)
        new_ann.append(new_ref_ann)
        return new_ann

    def get_tx_fte_annotations_mapping(self):
        tx_to_fte = {}
        for fte_idx in self.fte_indexes:
            cur_fte_tier = self.eaf.tiers()[fte_idx]
            for fte_annotation in cur_fte_tier:
                tx_to_fte[fte_annotation.ref_id] = fte_annotation.ID
        return tx_to_fte

    def get_tx_to_orig_tiers_mapping(self):  # mapping between indexes of tx tiers to their corresponding orig tier indexes
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

    def get_mb_idx_according_to_ge(self, ge_idx: int):
        for mb_idx in self.mb_indexes:
            if self.eaf.tiers()[mb_idx].name == self.eaf.tiers()[ge_idx].parent_ref:
                return mb_idx

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
        mb_index = []

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
            elif cur_tier.linguistic_type.ID == "mb":
                mb_index.append(i)
        return tx_indexes, fte_indexes, orig_indexes, ge_indexes, ps_indexes, mb_index

    def get_tx_indexes(self):
        return self.tx_indexes

    def get_fte_indexes(self):
        return self.fte_indexes

    def get_ge_indexes(self):
        return self.ge_indexes

    def get_ps_indexes(self):
        return self.ps_indexes

    def get_mb_indexes(self):
        return self.mb_indexes

    def get_orig_indexes(self):
        return self.orig_indexes

    def save_file(self, output_path: str):
        new_xml_str = (ET.tostring(self.root, method='xml')).decode('utf8')
        doc = xml.dom.minidom.parseString(new_xml_str)
        formatted_xml = doc.toprettyxml(indent="  ", newl='')
        with open(output_path, 'w', encoding='utf8') as output_file:
            output_file.write(formatted_xml)
