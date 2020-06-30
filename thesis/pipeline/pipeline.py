from typing import Optional, List
import pickle as pp
import argparse

from thesis.utils import logging, constants, ioutil
from thesis.fingerprinting.generators import FingerprintGenerator, ConstellationMapGenerator, MinHashLSHGenerator
from thesis.transforms.wavelet_transform import WaveletTransformator
from thesis.preprocess.preprocessor import Preprocessor, EmptyPreprocessor, TomboPreprocessor

logger = logging.get_logger(__name__)


def parse_arguments() -> argparse.PARSER:
    parser = argparse.ArgumentParser(description="Wavelet transformation module")

    # required arguments
    parser.add_argument('--file', required=True, type=str,
                        help='File which contains the signal. Can be .fast5 or a 1D numpy array (both as .p and .npy))')
    parser.add_argument('--preprocess', type=str,
                        help="Preprocessing to use on the signal before transformation", default=constants.PREPROCESS_TOMBO)
    parser.add_argument('--transform', type=str,
                        help='Transform type (CWT, DWT-CWT)', default=constants.TRANSFORMS_CWT)
    parser.add_argument('--continuous_wavelet', type=str, required=True,
                        help='Wavelet used for CWT (mexh, morl, cmorB-C, gausP, cgauP, shanB-C, fpspM-B-C)')
    parser.add_argument('--fingerprinting', type=str,
                        help='Fingerprinting method to use (constellation, minhash)', default=constants.FINGERPRINTING_CONSTELLATION)

    # optional arguments
    parser.add_argument('--id', type=str, help='ID used for the sequence')
    parser.add_argument('--discrete_wavelet', type=str,
                        help='Wavelet used for DWT')
    parser.add_argument('--destination',
                        type=str,
                        help='Directory where the resulting transformation should be saved',
                        default='./')

    # optional arguments transform
    parser.add_argument('--scale', type=int,
                        help='Scale used for cwt', metavar='BOUND', default=129)
    parser.add_argument('--absolute', type=bool,
                        help='Should cwt coefficients be returned as absolute value', default=True)
    parser.add_argument('--level', type=int,
                        help='Level for the multilevel DWT', default=5)

    # optional arguments fingerprinting
    parser.add_argument('--x_size', type=int,
                        help='Number of compressed points in the time axis of the CWT transform', default=32)
    parser.add_argument('--y_size', type=int,
                        help='Number of compressed points in the scale axis of the CWT transform', default=32)
    parser.add_argument('--window_size', type=int,
                        help='Number of signal points in the time domain for one window', default=8192)
    parser.add_argument('--shift_size', type=int,
                        help='Number of signal points in the time domain for one window to be shifted forward', default=1024)
    parser.add_argument('--top_wavelets', type=int,
                        help='Number of top wavelets to extract from a single window', default=25)
    parser.add_argument('--target_zone_size', type=int,
                        help='Size of the target zone in the constellation which follows each anchor', default=5)
    parser.add_argument('--chain_length', type=int,
                        help='Length of the consecutive chain in each target zone', default=3)
    parser.add_argument('--signature_size', type=int,
                        help='Signature size for the MinHash', default=128)
    return parser.parse_args()


def build_preprocessor(args: argparse.PARSER) -> Preprocessor:
    if args.preprocess.lower() == constants.PREPROCESS_NONE:
        return EmptyPreprocessor()

    elif args.preprocess.lower() == constants.PREPROCESS_TOMBO:
        return TomboPreprocessor()

    else:
        return None


def build_transformator(args: argparse.PARSER) -> Optional[WaveletTransformator]:
    if args.transform.lower() not in {constants.TRANSFORMS_CWT, constants.TRANSFORMS_DWT_CWT}:
        return None

    return WaveletTransformator(**vars(args))


def build_fingerprinter(args: argparse.PARSER) -> Optional[FingerprintGenerator]:
    if args.fingerprinting.lower() == constants.FINGERPRINTING_CONSTELLATION:
        return ConstellationMapGenerator(args.x_size, args.y_size, args.window_size, args.shift_size, args.top_wavelets, args.target_zone_size, args.chain_length)

    elif args.fingerprinting.lower() == constants.FINGERPRINTING_MINHASH:
        return MinHashLSHGenerator(args.x_size, args.y_size, args.window_size, args.shift_size, args.top_wavelets, args.signature_size)

    else:
        return None


def pipeline(filename: str, file_id: str, preprocessor: Preprocessor, transformator: WaveletTransformator, fingerprinter: FingerprintGenerator) -> None:
    preprocess_result = preprocessor.preprocess(filename)
    logger.info("Signal preprocessing completed")
    tranformation_result = transformator.transform(preprocess_result)
    logger.info("Signal transformation completed")
    fingerprinting_result = fingerprinter.generate_fingerprints(tranformation_result, file_id)
    logger.info("Fingerprinting completed")

    return fingerprinting_result


def __generate_pipeline_save_strings(args) -> List[str]:
    # generate file string
    file_string = ioutil.extract_file_name(args.file)
    # # generate preprocess string
    preprocess_string = args.preprocess

    # generate transform string
    if args.transform == constants.TRANSFORMS_CWT:
        transform_string = "cwt_{}_{}_{}".format(args.continuous_wavelet, args.scale, args.absolute)

    elif args.transform == constants.TRANSFORMS_DWT_CWT:
        transform_string = "dwt_cwt_{}_{}_{}_{}_{}".format(
            args.discrete_wavelet, args.level, args.continuous_wavelet, args.scale, args.absolute)

    # generate fingerprinting string
    if args.fingerprinting == constants.FINGERPRINTING_CONSTELLATION:
        fingerprinting_string = "{}_{}_{}_{}_{}_{}_{}_{}".format(
            args.fingerprinting, args.x_size, args.y_size, args.window_size, args.shift_size, args.top_wavelets, args.target_zone_size, args.chain_length)
    elif args.fingerprinting == constants.FINGERPRINTING_MINHASH:
        fingerprinting_string = "{}_{}_{}_{}_{}_{}_{}".format(
            args.fingerprinting, args.x_size, args.y_size, args.window_size, args.shift_size, args.top_wavelets, args.signature_size)
    return [file_string, preprocess_string, transform_string, fingerprinting_string]


def _save_pipeline_result(file_template: str, args: List[str], destination_dir: str, pipeline_result) -> None:
    # TODO: determine pipeline_result type
    pp.dump(pipeline_result, open(destination_dir + file_template.format(*args), "wb"))


def main():
    args = parse_arguments()
    # Construct objects needed to be passed
    preprocessor = build_preprocessor(args)
    if preprocessor is None:
        return
    logger.info("Preprocessor built")

    transformator = build_transformator(args)
    if transformator is None:
        return
    logger.info("Transformator built")

    fingerprinter = build_fingerprinter(args)
    if fingerprinter is None:
        return
    logger.info("Fingerprinter built")

    if args.id is None:
        file_id = ioutil.extract_file_name(args.file)
    else:
        file_id = args.id

    pipeline_result = pipeline(args.file, file_id, preprocessor, transformator, fingerprinter)

    _save_pipeline_result(constants.PIPELINE_RESULT, __generate_pipeline_save_strings(args),
                          args.destination, pipeline_result)


if __name__ == "__main__":
    main()
