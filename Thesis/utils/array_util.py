
from typing import List

import numpy as np

def save_np_ndarray(string_format: str,
                    string_args: List[str],
                    destination_dir: str,
                    array: np.ndarray
                    ) -> None:
    """Saves numpy arrays with the specified format name to the output dir.

    Args:
        string_format (str): filename format the file should have
        string_args (List[str]): list of parameters to be inserted to the format
        destination_dir (str): directory where the file should be saved
        array (np.ndarray): the array that should be saved
    """
    np.save((destination_dir + string_format).format(*string_args), array)

def cut_np_2D_ndarray(array: np.ndarray,
                      start_offset: int,
                      end_offset: int
                      ) -> np.ndarray:
    #TODO: add documentation
    return array[:, max(0, start_offset) : min(end_offset, array.shape[1])]

def cut_np_1D_ndarray(array: np.ndarray,
                   start_offset: int,
                   end_offset: int
                   ) -> np.ndarray:
    #TODO: add documentation
    return array[max(0, start_offset) : min(end_offset, len(array))]