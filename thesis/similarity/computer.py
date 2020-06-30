
from collections import defaultdict, Mapping
from typing import List, Tuple

import numpy as np
from datasketch import MinHash, MinHashLSH

import thesis.utils.logging as logging

#logger = logging.get_logger(__name__)


class SimilarityResult(Mapping):

    def __init__(self, dictionary: dict, num_fngp: int) -> None:
        self._dict = dictionary
        self._num_fngp = num_fngp

    def __len__(self) -> int:
        return len(self._dict)

    def __iter__(self):
        yield self._dict

    def __contains__(self, key) -> bool:
        return key in self._dict

    def __getitem__(self, key):
        return self._dict[key]

    def __str__(self) -> str:
        parts = []
        for idx, detections in self._dict.items():
            parts.append(idx)
            parts.append(25*"=")
            for offset, points in detections:
                parts.append("{:5} {:5} ({:3.5}%)\n".format(offset, points, 100 * points / self._num_fngp))

        return "\n".join(parts)

    def get(self, key, default=None):
        return self._dict.get(key, default)

    def keys(self):
        return self._dict.keys()

    def values(self):
        return self._dict.values()

    def items(self):
        return self._dict.items()

    def number_of_fingerprints(self):
        return self._num_fngp


class ConstellationSimilarityComputer():

    def __init__(self, database: dict, top_results: int = 1) -> None:
        self._database = database
        self._top_results = top_results

    def compute_similarity(self,  read: dict) -> SimilarityResult:
        coherency_counter = defaultdict(lambda: defaultdict(lambda: 0))
        fngp_count = len(read)

        # fingerprint is tuple of form:  (f_a, f_p_1, t_p_1 - t_a, ...)
        # value is a list of tuples of form: [(anchor_absolute_offset, id)]
        fngp_solved = 0
        for fingerprint, values in read.items():
            # ignore parameters of transformation
            if fingerprint == "params":
                continue

            # proceed if the fingerprint can be found in the database
            if fingerprint in self._database:
                # list of (offset, id) pairs
                candidates = self._database[fingerprint]

                # candidate = (offset, id)
                for candidate in candidates:
                    # value = (offset, id)
                    for value in values:
                        coherency_counter[candidate[1]][candidate[0] - value[0]] += 1

            fngp_solved += 1
            if fngp_solved % 100 == 0:
                print("{}/{}".format(fngp_solved, fngp_count), end="\r")

        print("{}/{}".format(fngp_solved, fngp_solved))

        top_results = dict()
        for key, value in coherency_counter.items():
            results = sorted(value.items(), key=lambda x: x[1], reverse=True)[:self._top_results]

            top_results[key] = results

        return SimilarityResult(top_results, fngp_count)


class LSHSimilarityComputer():

    def __init__(self, minhashes: List[Tuple[MinHash, str]], num_tables: int = 8, threshold: float = 0.5, required_votes: int = 3,
                 top_results: int = 1):
        self._num_tables = num_tables
        self._threshold = threshold
        self._required_votes = required_votes
        self._top_results = top_results
        if len(minhashes[0][0].digest()) % num_tables != 0:
            raise Exception("Minhash signature not compatible with number of tables")

        self._database = [MinHashLSH(threshold=self._threshold, num_perm=len(minhashes[0][0]) // num_tables)
                          for i in range(num_tables)]

        for minhash, idx in minhashes:
            digests = self._separate_digest(minhash.digest(), self._num_tables)

            for i, digest in enumerate(digests):
                m = MinHash(hashvalues=digest)
                self._database[i].insert(idx, m)

    def _separate_digest(self, digest: np.ndarray, num_parts: int) -> List[np.ndarray]:
        return np.array_split(digest, num_parts)

    def _extract_id_offset(self, label: str) -> Tuple[str, int]:
        parts = label.split(":")
        return parts[0], int(parts[1])

    def compute_similarity(self, read: List[Tuple[MinHash, str]]) -> SimilarityResult:
        coherency_counter = defaultdict(lambda: defaultdict(lambda: 0))

        for minhash, idx in read:
            _, read_offset = self._extract_id_offset(idx)
            #print("read_offset", read_offset)

            digests = self._separate_digest(minhash.digest(), len(self._database))
            #print("digests", digests)

            candidates = defaultdict(lambda: 0)
            for i, digest in enumerate(digests):
                query_minhash = MinHash(hashvalues=digest)
                votes = self._database[i].query(query_minhash)
                #print("votes", votes)
                for v in votes:
                    candidates[v] += 1

            for i, v in filter(lambda x: x[1] >= self._required_votes, candidates.items()):
                vote_id, vote_offset = self._extract_id_offset(i)
                coherency_counter[vote_id][vote_offset - read_offset] += 1

        #print("Coherency counter", coherency_counter)
        top_results = dict()
        for key, value in coherency_counter.items():
            results = sorted(value.items(), key=lambda x: x[1], reverse=True)[:self._top_results]

            top_results[key] = results

        return SimilarityResult(top_results, len(read))
