from typing import Tuple, List
from abc import ABC, abstractmethod
import numpy as np
import cv2
from datasketch import MinHash, MinHashLSH
from lsh import MinHashSignature
from collections import defaultdict

import thesis.utils as utils

logger = utils.logging.get_logger(__name__)


def largest_indices(array: np.ndarray, n: int) -> Tuple[np.ndarray, np.ndarray]:
    """Returns the n largest indices from a numpy array."""
    flat = array.flatten()
    indices = np.argpartition(flat, -n)[-n:]
    indices = indices[np.argsort(-flat[indices])]
    return np.unravel_index(indices, array.shape)


class FingerprintGenerator(ABC):

    @abstractmethod
    def generate_fingerprints(self, coefficients: np.ndarray, number_of_points: int):
        pass


class ConstellationMapGenerator(FingerprintGenerator):

    def __init__(self, x_size: int, y_size: int, window_size: int, shift_size: int, top_wavelets: int, target_zone_size: int, chain_length: int) -> None:
        self._x_size = x_size
        self._y_size = y_size
        self._window_size = window_size
        self._shift_size = shift_size
        self._top_wavelets = top_wavelets
        self._target_zone_size = target_zone_size
        self._chain_length = chain_length

    def generate_fingerprints(self, coefficients: np.ndarray, file_id: str) -> dict:
        constellation_map = set()

        for i in range(0, coefficients.shape[1] - self._window_size, self._shift_size):
            print("{} / {}".format(i, (coefficients.shape[1] - self._window_size) // self._shift_size), end='\r')
            sub_array = coefficients[:, i: i + self._window_size]
            sub_array = cv2.resize(sub_array, (self._y_size, self._x_size))
            y, x = largest_indices(sub_array, self._top_wavelets)
            x += ((i // self._shift_size) * (self._x_size // (self._window_size // self._shift_size)))
            inds = list(zip(x, y))
            constellation_map.update(inds)

        ordered_stars = list(constellation_map)
        ordered_stars.sort()

        fingerprints = []
        offsets = []
        for i in range(len(ordered_stars)):
            anchor = ordered_stars[i]

            try:
                for j in range(1, self._target_zone_size):
                    fingerprint = (anchor[1], ordered_stars[i+j][1], ordered_stars[i+j][0] - anchor[0])

                    for k in range(1, self._chain_length):
                        fingerprint += (ordered_stars[i+j+k][1], ordered_stars[i+j+k][0] - ordered_stars[i+j+k-1][0],)

                    fingerprints.append(fingerprint)
                    offsets.append(anchor[0])
            except IndexError:
                pass

        fingerprint_dict = defaultdict(lambda: [])
        for idx, fingerprint in enumerate(fingerprints):
            fingerprint_dict[fingerprint].append((offsets[idx], file_id))
        fingerprint_dict = dict(fingerprint_dict)

        return fingerprint_dict


class MinHashLSHGenerator(FingerprintGenerator):

    def __init__(self, x_size: int, y_size: int, window_size: int, shift_size: int, top_wavelets: int,  signature_size: int = 128) -> None:
        self._x_size = x_size
        self._y_size = y_size
        self._window_size = window_size
        self._shift_size = shift_size
        self._top_wavelets = top_wavelets
        self._signature_size = signature_size

    def generate_fingerprints(self, coefficients: np.ndarray, file_id: str) -> List[Tuple[MinHash, str]]:
        results = []

        for i in range(0, coefficients.shape[1] - self._window_size, self._shift_size):
            print("{} / {}".format(i, (coefficients.shape[1] - self._window_size) // self._shift_size), end='\r')
            sub_array = coefficients[:, i: i + self._window_size]
            sub_array = cv2.resize(sub_array, (self._y_size, self._x_size))
            y, x = largest_indices(sub_array, self._top_wavelets)
            inds = list(zip(x, y))

            m = MinHash(num_perm=self._signature_size)
            for star in inds:
                m.update(str(star).encode())

            results.append((m, "{}:{}".format(file_id, str(i // self._shift_size))))

        return results
