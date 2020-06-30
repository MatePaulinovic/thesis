import argparse

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sbn
import pywt

import Erevnitis.utils.signal_extractor as signal_extractor
import Erevnitis.utils.array_util as array_util

def plot_signal(signal):
    # TODO: add documentation
    plt.plot(list(range(len(signal))), signal)
    plt.grid(True)
    plt.show()

def plot_scalogram(coefficients):
    _, ax = plt.subplots()
    ax = sbn.heatmap(coefficients, cmap='jet')
    plt.show()

def __define_parser() -> argparse.ArgumentParser:
    # TODO: add documentation
    parser = argparse.ArgumentParser(description="Wavelet transformation visualizer")

    # Positional arguments
    parser.add_argument('visualization', help='Type of visualization (signal, scalogram, constellations, window)')
    parser.add_argument('file', help='File which contains the signal')

    # Optional arguments
    parser.add_argument('-l', '--length', type=int, help='Signal cut length')
    parser.add_argument('-o', '--offset', type=int, help='Signal offset', default=0)
    parser.add_argument('-w', '--wavelet', help='Wavelet used for cwt (mexh, morl, cmorB-C, gausP, cgauP, shanB-C, fpspM-B-C)')
    parser.add_argument('-s', '--scale', type=int, help='Scale used for cwt', default=65)
    parser.add_argument('-g', '--gui', action='store_true', help='Use interactive GUI')
    parser.add_argument('-ws', '--window_size', type=int, help='Window size', default=700)
    parser.add_argument('-b', '--bands', type=int, help='Number of bands', default=8)

    return parser

def main():
    parser = __define_parser()
    args = parser.parse_args()

    extractor = signal_extractor.SignalExtractor(args.file)
    signal = extractor.get_signal_continuos()
    # TODO: add logging
    # print("Signal read")
    # print("Signal length: {}".format(len(signal)))

    if args.length is not None:
        signal = array_util.cut_np_1D_ndarray(signal, args.offset, args.offset + args.length)
        #signal =  signal[args.offset : min(args.offset + args.length, len(signal))]
        # print("Signal truncated to length: {}".format(len(signal)))

    if args.visualization == 'signal':
        plot_signal(signal)
        return

    coefficients, _ = pywt.cwt(signal, np.arange(1, args.scale), args.wavelet)
    coefficients = abs(coefficients)
    # print("Calculated coefficients")

    if args.visualization == 'scalogram':
        plot_scalogram(coefficients)
        #plt.savefig(args.file + "_" + args.wavelet + "_" + str(args.scales[0]) + "-" + str(args.scales[1]) + ".png")
        return
    """
    lfs = fs.LinearFieldSplitter(args.bands)
    maasg = sg.MaxAboveAverageStarGenerator(lfs)
    cmg = ConstellationMapGenerator(maasg)
    constellation_map = cmg.generate_constellation_map(coefficients)

    if args.visualization == 'constellations':
        plot_constellations(coefficients, constellation_map)
        return

    mwf = wf.MatrixWindowFunction(args.window_size)
    window = mwf.apply_window_function(constellation_map)
    if args.visualization == 'window':
        plot_windowed_constellations(window)
        return

    if args.visualization == "scalogram_constellations":
        plot_scalogram_with_points(coefficients, window)
        plt.show()
        #plt.savefig("/home/mate/Documents/Faks/Diplomski/Kod/diplomski/data/images/" + args.wavelet + "_" + str(args.window_size) + ".png")
        return
    """

if __name__  == "__main__":
    main()