import os

from Thesis.similarity.computer import SimilarityResult


def save_similarity_result(filename: str, result: SimilarityResult) -> None:
    with open(filename, "w") as h:
        h.write(str(result))


def extract_file_name(filename: str) -> str:
    return os.path.splitext(os.path.basename(filename))[0]
