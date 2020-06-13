from Thesis.utils.ioutil import save_similarity_result
from Thesis.similarity.computer import ConstellationSimilarityComputer, LSHSimilarityComputer
from Thesis.utils import constants
import pickle as pp
import numpy as np
import sys
import argparse

__name__ == "__main__"
# TODO: change database to fixed path


def parse_arguments() -> argparse.PARSER:
    parser = argparse.ArgumentParser(description="Wavelet transformation module")

    # required arguments
    parser.add_argument('--ref', required=True, type=str,
                        help='File which contains the reference pipeline result.')
    parser.add_argument('--read', required=True, type=str,
                        help='File which contains the read pipeline result.')
    parser.add_argument('--similarity', required=True, type=str,
                        help='Similarity type to use for comparison (constellation, lsh)')
    parser.add_argument('--num_tables', type=int,
                        help='Number of tables to be used for similarity in LSH', default=8)
    parser.add_argument('--threshold', type=float, help='Threshold for similarity of minhash singature', default=0.5)
    parser.add_argument('--required_votes', type=int,
                        help='Number of required votes by the table to vet a vote', default=3)
    return parser.parse_args()


def main():
    args = parse_arguments()
    reference = pp.load(open(args.ref, 'rb'))
    read = pp.load(open(args.read, 'rb'))

    similarity_computer = None
    if args.similarity == constants.SIMILARITY_CONSTELLATION:
        similarity_computer = ConstellationSimilarityComputer(reference)
    elif args.similarity == constants.SIMILARITY_LSH:
        similarity_computer = LSHSimilarityComputer(reference, args.num_tables, args.threshold, args.required_votes)
    else:
        raise Exception("INVALID")

    similarity_result = similarity_computer.compute_similarity(read)

    print(similarity_result)
    save_similarity_result(args.read + '_sim.txt', similarity_result)


if __name__ == "__main__":
    main()
