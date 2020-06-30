from __future__ import print_function
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import io
import codecs
import os
import sys

from thesis import Thesis

here = os.path.abspath(os.path.dirname(__file__))

def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

def read_requirements(path):
    install_requires = []
    with open(path, 'r') as handle:
        lines = handle.readlines()
        return lines
        #for line in lines:
        #   install_requires.append("'" + line + "'")

    return install_requires

long_description = read('README.md')

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)



setup(
    name='thesis',
    version=Thesis.__version__,
    url='http://github.com/MatePaulinovic/thesis/',
    license='MIT License',
    author='Mate Paulinovic',
    tests_require=['pytest'],
    #install_requires=read_requirements("/home/mate/Documents/Faks/Diplomski/Kod/EREVNITIS/Erevnitis/requirements.txt"),
    cmdclass={'test': PyTest},
    author_email='mate.paulinovic@fer.hr',
    description='Fast pathogen detection system based on next generation nucleotide sequencing',
    long_description=long_description,
    packages=['thesis'], #find_packages('thesis'), #['Erevnitis'],
    include_package_data=True,
    platforms='any',
    test_suite='thesis.test.test_thesis',
    classifiers = [
        'Programming Language :: Python',
        'Development Status :: 1 - Planning',
        'Natural Language :: English',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        ],
    extras_require={
        'testing': ['pytest'],
    }
)
