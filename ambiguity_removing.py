def decl_vs_pst(is_second_ge: bool):                         # ge
    if is_second_ge:
        return "PST", "ptcl"
    return "DECL", "ptcl"


def hort_vs_stata(fte_line: str):                            # a
    if "let" in fte_line:
        return "HORT", "ptcl"
    return "STATa", "ptcl"


def xa_postp(fte_line: str):                                 # xa postp          #TODO check the frequency of it, maybe it would be better than looking in the translation
    # look for "by" or "about" in translation
    if "by " in fte_line:
        return "by", "postp"
    return "about", "postp"


def pgn_vs_recp(fte_line: str):                              # -gu
    if "each other" in fte_line:
        return "-RECP", "-vsf"
    return "-3M.PL", "-nsf"


def poss1_vs_quot_vs_1sg(tx_line: str, fte_line: str):       # ti
    if "my " in fte_line or "mine." in fte_line or "mine " in fte_line or "mine, " in fte_line:
        return "1SG.POSS", "pro"                             # TODO find a stronger indication for cases in which both "my" and "I" occur
    elif "i " in fte_line or "ti -ta" in tx_line:            # TODO better to check whether the next annotation is '-ta'
        return "1SG", "pro"
    return "QUOT", "ptcl"


def poss2_vs_2pro_1incl(fte_line: str):                      # sa
    if "your " in fte_line in fte_line:
        return "2SG.POSS", "pro"
    elif "we " in fte_line:
        return "1INCL", "pro"
    return "2", "pro"


def we_vs_arrive(fte_line: str):                             # sī
    if "we " in fte_line:
        return "1EXCL", "pro"
    return "arrive", "vitr"


def solve_lexical_ambiguity(possible_ge_values: list, possible_ps_values: list, fte_line: str, tx_line: str):
    """
    :param possible_ge_values: A list of several options to gloss (ge)
    :param possible_ps_values: A list of several options to gloss (ps)
    :param fte_line: string of the translation
    :param tx_line: string of the tx annotation
    :return: The index (of possible_ge_values list) which indicates the chosen option
    """
    fte_line.replace("/", " ")
    fte_line.replace(".", " ")
    fte_list = fte_line.split()
    if not fte_list:
        return 0
    possible_indexes = []
    for i in range(len(possible_ge_values)):
        cur_option = possible_ge_values[i]
        for j in range(len(fte_list)):
            if cur_option == fte_list[j]:
                if cur_option.endswith("ing") and (j == len(fte_list) - 1 or fte_list[j-1] in {"am", "is", "are", "was", "were"}):
                    for k in range(len(possible_ps_values)):
                        if possible_ps_values[k] in {"vtr", "vitr", "vdtr"}:
                            return k
                return i
            elif cur_option in fte_list[j]:
                possible_indexes.append(i)
    max_option_idx = 0
    for i in possible_indexes:
        if len(possible_ge_values[i]) >= len(possible_ge_values[max_option_idx]):
            max_option_idx = i
    return max_option_idx
