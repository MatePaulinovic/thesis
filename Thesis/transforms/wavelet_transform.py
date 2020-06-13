from typing import List
import argparse
import os

import numpy as np
import pywt

from Thesis.utils import logging
from Thesis.utils import array_util
from Thesis.utils import constants
from Thesis.utils import signal_extractor

logger = logging.get_logger(__name__)


def cwt(signal: np.ndarray, wavelet: str, scale: int, absolute: bool = True) -> np.ndarray:
    """Transforms given signal using the continuous wavelet transform.

    The signal is transformed using the continuous wavelet transform using the given wavelet, for
    scales in range [1, scale>.

    Args:
        signal (np.ndarray): Signal to be transformed.
        wavelet (str): wavelet to be used for the transform
        scale (int): The upper scale limit for the transform.
        absolute (bool, optional): Indicates if the coefficients should be returned . Defaults to
            True.

    Returns:
        np.ndarray: 2D array of transform coefficients.
    """
    coefficients, _ = pywt.cwt(signal, np.arange(1, scale + 1), wavelet)
    if absolute:
        return abs(coefficients)
    return coefficients


def dwt(signal: np.ndarray, wavelet: str, level: int) -> List[np.ndarray]:
    # TODO add documentation
    if level > 1:
        c_a, c_d = pywt.dwt(signal, wavelet)
        return [c_a, c_d]
    return pywt.wavedec(signal, wavelet, level=level)


def save_cwt(coefficients: np.ndarray,
             filename: str,
             wavelet: str,
             scale: int,
             absolute: bool,
             destination_dir: str = "./"
             ) -> None:
    # TODO add documentation
    _, name = os.path.split(filename)
    array_util.save_np_ndarray(constants.CWT_SAVE_STRING_FORMAT,
                               [name, wavelet, str(scale), absolute],
                               destination_dir,
                               coefficients)


def save_dwt(coefficients: List[np.ndarray],
             filename: str,
             wavelet: str,
             level: int,
             destination_dir: str = "./"
             ) -> None:
    # TODO: add documentation
    array_util.save_np_ndarray(constants.DWT_SAVE_STRING_FORMAT,
                               [filename, wavelet, str(level)],
                               destination_dir,
                               coefficients)


class WaveletTransformator():

    __allowed_keys = {"transform", "continuous_wavelet", "discrete_wavelet", "scale", "absolute", "level"}

    def __init__(self, **kwargs: str) -> None:
        self.__dict__.update(("_" + k, v) for k, v in kwargs.items() if k in self.__allowed_keys)

    def transform(self, signal: np.ndarray) -> np.ndarray:
        #pylint: disable=maybe-no-member
        if self._transform == constants.TRANSFORMS_CWT:
            return cwt(signal, self._continuous_wavelet, self._scale, self._absolute)

        if self._transform == constants.TRANSFORMS_DWT_CWT:
            dwt_transform = dwt(signal, self._discrete_wavelet, self._level)
            return cwt(dwt_transform, self._continuous_wavelet, self._scale, self._absolute)


def parse_arguments() -> argparse.PARSER:
    parser = argparse.ArgumentParser(description="Wavelet transformation module")

    parser.add_argument('file', help='File which contains the signal')
    parser.add_argument(
        'wavelet', type=str,
        help='Wavelet used for CWT (mexh, morl, cmorB-C, gausP, cgauP, shanB-C, fpspM-B-C), or DWT')
    parser.add_argument('--length', type=int, help='Signal cut length')
    parser.add_argument('--offset', type=int,
                        help='Signal offset', default=0)
    parser.add_argument('--scale', type=int,
                        help='Scale used for cwt', metavar='BOUND', default=129)
    parser.add_argument('--absolute', type=bool,
                        help='Should cwt coefficients be returned as absolute value', default=True)
    parser.add_argument('--level', type=int,
                        help='Level for the multilevel DWT', default=5)
    parser.add_argument('--destination', type=str,
                        help='Directory where the resulting transformation should be saved', default='./')
    return parser.parse_args()


def main():
    args = parse_arguments()
    fast5 = signal_extractor.SignalExtractor(args.file)
    signal = fast5.get_signal_continuos()

    logger.info("Signal %s read", args.file)
    logger.info("Signal length: %s", len(signal))

    if args.length is not None:
        signal = array_util.cut_np_1D_ndarray(signal, args.offset, args.offset + args.length)
        logger.info("Signal truncated to length: %s", len(signal))

    if args.wavelet in pywt.wavelist(kind='discrete'):
        transformed_signal = dwt(signal, args.wavelet, args.level)
        save_dwt(transformed_signal, args.file, args.wavelet, args.level, args.destination)
    else:
        transformed_signal = cwt(signal, args.wavelet, args.scale, args.absolute)
        save_cwt(transformed_signal, args.file, args.wavelet,
                 args.scale, args.absolute, args.destination)

    logger.info("Signal transformed and saved")


if __name__ == "__main__":
    main()
