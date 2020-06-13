from abc import ABC, abstractmethod

import numpy as np

from Thesis.utils.signal_extractor import SignalExtractor


class Preprocessor(ABC):

    @abstractmethod
    def preprocess(self, filename: str) -> np.ndarray:
        pass


class EmptyPreprocessor(Preprocessor):

    def preprocess(self, filename: str) -> np.ndarray:
        if filename.endswith(".fast5"):
            signal_extractor = SignalExtractor(filename)
            signal = signal_extractor.get_signal_continuous()
        else:
            signal = np.load(filename)

        return signal


class TomboPreprocessor(Preprocessor):

    def preprocess(self, filename: str) -> np.ndarray:
        if filename.endswith(".fast5"):
            signal_extractor = SignalExtractor(filename)
            return signal_extractor.get_signal_of_means()

        return None
