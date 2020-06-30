import io
import os
from queue import Queue

import numpy as np
import h5py
from Bio import SeqIO       # pylint: disable=import-error

import thesis.proto.signal_pb2 as signal_pb2


class SignalExtractor():
    # TODO: add documentation

    def __init__(self, path_to_file):
        if not os.path.isfile(path_to_file):
            raise FileNotFoundError("The file {} could not be found".format(path_to_file))

        self._path_to_file = path_to_file
        print(path_to_file)
        self._file_handle = h5py.File(path_to_file, 'r')
        self._key_dict_hierarchical = dict()
        self._key_dict_flat = dict()
        self._generate_key_dict()
        self._sequence = None
        self._events = None
        self._nanopolish_events = None
        self._raw_current = None
        self._discrete_signal = None
        self._continous_signal = None
        self._add_conversion_data()

    def get_fasta(self):
        """Returns fasta reads read within the fast5 file.

        Parameters
        ----------

        Returns
        -------
        fasta : SeqRecord list
            List of SeqRecords objects
        """
        return self._extract_file_format('Fasta')

    def get_fastq(self):
        """Returns fastq reads read within the fast5 file.

        Parameters
        ----------

        Returns
        -------
        fastq : SeqRecord list
            List of SeqRecords objects
        """
        return self._extract_file_format('Fastq')

    def get_signal_discrete(self):
        """Returns all discrete signal values associated with the current file.

        Parameters
        ----------

        Returns
        -------
        signal : np.array
            Discrete signal signal values from file
        """
        if self._discrete_signal is not None:
            return self._discrete_signal

        signal = self._key_dict_flat['Signal']

        self._discrete_signal = np.array(signal)

        return self._discrete_signal

    def get_signal_continuous(self):
        """Returns all continuous/raw signal values associated with the current
        file.

        Parameters
        ----------

        Returns
        -------
        signal : np.array
            Continuous/ras signal values from file
        """
        if self._continous_signal is not None:
            return self._continous_signal

        discrete_signal = self.get_signal_discrete()

        info = self.get_channel_info()
        rng = info.range
        digitisation = info.digitisation
        raw_unit = rng / digitisation
        offset = info.offset

        self._continous_signal = np.array(list(map(lambda x: (x + offset) * raw_unit, discrete_signal)))

        return self._continous_signal

    def get_nucleotide_positions(self, nucleotide):
        """Returns all indices of positions where the specified nucleotide has
        been detected.

        Parameters
        ----------
        nucleotide : string
            Nucleotide name

        Returns
        -------
        indices : numpy.array
            Numpy vector containing the indices.
        """

    def _add_conversion_data(self):
        """Reads variables needed for signal conversion (digitisation, offset and range) into instance variables.

        Parameters
        ----------

        Returns
        -------
        """
        attrs = self._key_dict_flat['channel_id'].attrs
        self._digitisation = float(attrs['digitisation'])
        self._offset = float(attrs['offset'])
        self._range = float(attrs['range'])
        self._raw_unit = self._range / self._digitisation
        #self._raw_unit = self._digitisation / self._range

    def _generate_key_dict(self):
        """Generates key dictionary for accessing all groups in fast5 file for easier access in other methods.
        Two dictionaries are generated:
            _key_dict_flat : (key string) -> (HDF5 group object)
            _key_dict_hierarchical : (HDF5 group object) -> ([key string])

        Parameters
        ----------

        Returns
        -------
        """
        queue = Queue()
        queue.put(self._file_handle)

        while not queue.empty():
            tmp = queue.get()
            tmp_keys = []
            try:
                for key in tmp.keys():
                    tmp_keys.append(key)
                    queue.put(tmp[key])
                    self._key_dict_flat[key] = tmp[key]

                self._key_dict_hierarchical[tmp] = tmp_keys

            except AttributeError:
                continue

        """UNCOMMENT TO VIEW DICT ELEMENTS
        print("Hierarchical dict representation")
        for key, value in self._key_dict_hierarchical.items():
            print(key, value)
        print(" ")
        print("Flat dict representation: ")

        for key, value in self._key_dict_flat.items():
            print(key, value)
        """

        return

    def get_signal_of_means(self):
        alignment = self._key_dict_flat['BaseCalled_template']
        events = np.array(alignment.get('Events'))
        signal = self.get_signal_continuous()                            # events is a vector of shape (x, )

        signal_list = []
        for row in events:
            start = row[2]
            length = row[3]
            samples = signal[start:(start+length)]
            signal_list.append(np.mean(samples))

        signal_list = np.array(signal_list)

        return signal_list

    def get_signal_of_norm_means(self):
        alignment = self._key_dict_flat['BaseCalled_template']
        events = np.array(alignment.get('Events'))
        signal = self.get_signal_continuous()                            # events is a vector of shape (x, )

        signal_list = []
        for row in events:
            signal_list.append(row[0])

        signal_list = np.array(signal_list)

        return signal_list

    def _extract_file_format(self, file_format):
        """Extracts the specified file format from fast5 file. If no file with the specified format is found,
        an Error is raised.

        Parameters
        ----------
        file_format : string
            File format as string.

        Returns
        -------
        seq : Bio.Seq.Seq
            Sequence object representation of the specified file format.


        Raises
        ------
        KeyError
            Raised if there is no file with the specified format
        """
        result = None

        try:
            dataset = self._key_dict_flat[file_format]
            string = dataset[()]
            result = list(SeqIO.parse(io.StringIO(string), file_format.lower()))  # for simple conversion
            # we can remove list

        except KeyError:
            print("This fast5 file does not contain a {} file.".format(file_format.lower()))

        return result

    def get_channel_info(self):
        channel_id_attrs = self._key_dict_flat['channel_id'].attrs
        return SignalExtractor._create_channelInfo(channel_id_attrs)

    @staticmethod
    def _create_channelInfo(channel_id_attrs):
        info = signal_pb2.ChannelInfo()

        info.channel_number = channel_id_attrs['channel_number']
        info.digitisation = float(channel_id_attrs['digitisation'])
        info.offset = float(channel_id_attrs['offset'])
        info.range = float(channel_id_attrs['range'])
        info.sampling_rate = float(channel_id_attrs['sampling_rate'])

        return info
