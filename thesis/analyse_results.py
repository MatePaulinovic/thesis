import os
import sys
import argparse
import glob
from collections import defaultdict

import numpy as np


OFFSET = "offset"
REAL_OFFSET = "real_offset"
SIMILARITY = "similarity"
DELTA = "delta"

transformed_prefix = 'tombo/transformed/'
minimap_prefix = 'minimap/'
wavelet = 'cgau5'

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--dir', required=True, type=str,
                        help="Starting directory for analysis")
    parser.add_argument('--fingerprinting', required=True, type=str,
                        help="Type of pipeline result to analyse (constellation, minhash)")
    parser.add_argument('--suffixes', required=True, type=str, nargs='+',
                        help="Suffixes to analyse")

    return parser.parse_args()
    
def extract_read_id(signal_name :str) -> str:
    parts = signal_name.split("_")
    return parts[3]

def extract_start_position(filename: str):
    with open(filename) as h:
        return int(h.readline().split()[7])

def extract_similarity_info(filename: str):

    sim_dict = defaultdict(lambda: dict())

    with open(filename) as h:
        lines = h.read().splitlines()
        
        for i in range(6):
            organism = lines[i*4]
            values = lines[i*4 + 2].split()
            
            sim_dict[organism][OFFSET] = float(values[0])
            if "constellation" in filename:
                sim_dict[organism][REAL_OFFSET] = float(values[0]) * 256
            else:
                sim_dict[organism][REAL_OFFSET] = float(values[0]) * 32
            sim_dict[organism][SIMILARITY] = float(values[2].rstrip('%)').lstrip('('))
            sim_dict[organism][DELTA] = float(values[1])
            
    return sim_dict

def find_positions_of_actual(dicts, ref):
    actual = defaultdict(lambda: 0)
    for d in dicts:
        positions = []
        for ref_id, ref_dict in d.items():
            positions.append((ref_id, ref_dict[SIMILARITY]))

        positions.sort(key=lambda x: x[1], reverse=True)
        #print(positions) 
        
        actual_i = [y[0] for y in positions].index(ref)
        #print(actual_i)

        actual[actual_i] += 1

    return actual

def find_difference_from_first(dicts, ref):
    diffs = []
    relative_diffs = []
    for d in dicts:
        positions = []
        for ref_id, ref_dict in d.items():
            positions.append((ref_id, ref_dict[SIMILARITY]))

        positions.sort(key=lambda x: x[1], reverse=True)
        #print(positions) 
        
        actual_i = [y[0] for y in positions].index(ref)
        #print(actual_i)

        diffs.append(positions[0][1] - positions[actual_i][1])
        relative_diffs.append( (positions[0][1] - positions[actual_i][1]) / positions[0][1]) 
    return diffs, np.mean(diffs), np.std(diffs), relative_diffs, np.mean(relative_diffs), np.std(relative_diffs)

def find_offset_difference(sim_dict, filename,  ref, fingerprinting):
    read_id = extract_read_id(filename)
    real_position = extract_start_position(minimap_prefix + read_id + ".fastq_aln.paf")
    if fingerprinting == "constellation":
        return sim_dict[ref][OFFSET] - (real_position // 256) 
    elif fingerprinting == "minhash":
        return sim_dict[ref][OFFSET] - (real_position // 1024)

def find_subsequent_difference(dicts, ref):
    sub_diffs = []
    for d in dicts:
        positions = []
        for ref_id, ref_dict in d.items():
            positions.append((ref_id, ref_dict[SIMILARITY]))

        positions.sort(key=lambda x: x[1], reverse=True)
        
        if positions[0][0] == ref:
            sub_diffs.append(positions[0][1] - positions[1][1])

    return sub_diffs

def main():
    args = parse_args()
        
    if args.fingerprinting not in {"constellation", "minhash"}:
        raise Exception("invalid fingerprinting scheme")

    os.chdir(args.dir) # enter size dir
    

    global_actual = defaultdict(lambda: defaultdict(lambda: 0))
    global_offsets = defaultdict(lambda: [])
    global_diffs = defaultdict(lambda: [])
    global_rdiffs = defaultdict(lambda: [])
    for directory in os.listdir("./"):
        if not os.path.isdir(os.path.join("./", directory)):
            continue
        
        print(directory)
        os.chdir(directory)  # enter organism dir

            
        for suffix in args.suffixes:
            dicts = []
            offsets = []
            for g in glob.glob(transformed_prefix + '*' + wavelet + '*' + args.fingerprinting + '*' + suffix + '_sim.txt'):
                print(g)
                d = extract_similarity_info(g)
                dicts.append(d)
                o = find_offset_difference(d, g, directory, args.fingerprinting)
                offsets.append(o)
            
            actual = find_positions_of_actual(dicts, directory)
            #print(actual)
            diffs = find_difference_from_first(dicts, directory)
            #print(diffs)
            #print(offsets)
            print(directory, suffix)
            sd = find_subsequent_difference(dicts, directory)
            print(sd)
            print(np.mean(sd))
            print(np.std(sd))

        """     
            for k,v in actual.items():
                global_actual[suffix][k] += v
            global_offsets[suffix] += offsets
            global_diffs[suffix] += diffs[0]
            global_rdiffs[suffix] += diffs[3]

            with open("-".join([directory, wavelet, args.fingerprinting, suffix, "sim.txt"]), "w") as f:
                f.write("#actual position distribution\n")
                f.write(str(actual) + "\n")
                
                f.write("#difference from first\n")
                f.write(str(diffs[0]) + "\n")
                f.write("# mean and std\n")
                f.write(str(diffs[1]) + "\n")
                f.write(str(diffs[2]) + "\n")
                
                f.write("#relative diffs\n")
                f.write(str(diffs[3]) + "\n")
                f.write("# mean and std\n")
                f.write(str(diffs[4]) + "\n")
                f.write(str(diffs[5]) + "\n")
                
                f.write("#offsets\n")
                f.write(str(offsets) + "\n") 
                f.write(str(np.mean(offsets)) + "\n")
                f.write(str(np.std(offsets)) + "\n")


        os.chdir("..") # leave organism dir

    for suffix in args.suffixes:
        with open("-".join([ wavelet, args.fingerprinting, suffix, "sim.txt"]), "w") as f:
            f.write("#actual position distribution\n")
            f.write("{")
            for k, v in global_actual[suffix].items():
                f.write("({},{}) ".format(k,v))
            f.write("}\n")
                
            f.write("#difference from first\n")
            f.write(str(global_diffs[suffix]) + "\n")
            f.write("# mean and std\n")
            f.write(str(np.mean(global_diffs[suffix])) + "\n")
            f.write(str(np.std(global_diffs[suffix])) + "\n")
                
            f.write("#relative diffs\n")
            f.write(str(global_rdiffs[suffix]) + "\n")
            f.write("# mean and std\n")
            f.write(str(np.mean(global_rdiffs[suffix])) + "\n")
            f.write(str(np.std(global_rdiffs[suffix])) + "\n")
                
            f.write("#offsets\n")
            f.write(str(global_offsets[suffix]) + "\n") 
            f.write(str(np.mean(global_offsets[suffix])) + "\n")
            f.write(str(np.std(global_offsets[suffix])) + "\n")

            f.write("{:.5f} & {:.5f} & {:.5f} & {:.5f} \\\\\n".format(np.mean(global_diffs[suffix]), np.std(global_diffs[suffix]), np.mean(global_offsets[suffix]), np.std(global_offsets[suffix])))

        """

if __name__ == "__main__":
    main()

