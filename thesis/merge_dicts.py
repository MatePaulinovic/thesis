from collections import defaultdict
import pickle as pp
import sys


def merge_dicts(dicts, suffix):
    final_dict = defaultdict(lambda: [])

    for d in dicts:
        for k, v in d.items():
            final_dict[k].extend(v)
    
    final_dict = dict(final_dict)
    pp.dump(final_dict, open("reference_database_"+suffix +".p", "wb"))
    return final_dict

if __name__ == "__main__":
    dicts = []
    for i in range(1, len(sys.argv)-1):
        d = pp.load(open(sys.argv[i], "rb"))
        dicts.append(d)

    merge_dicts(dicts, sys.argv[-1])
