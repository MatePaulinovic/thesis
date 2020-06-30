from collections import defaultdict
import pickle as pp
import sys


def merge_lists(lists, suffix):
    final_list = []

    for d in lists:
        final_list += d
    
    pp.dump(final_list, open("reference_database_"+suffix +".p", "wb"))
    return final_list

if __name__ == "__main__":
    lists = []
    for i in range(1, len(sys.argv)-1):
        d = pp.load(open(sys.argv[i], "rb"))
        lists.append(d)

    merge_lists(lists, sys.argv[-1])
