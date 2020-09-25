#!/usr/bin/env python3

from setuptools import setup, find_packages
from somaticseq._version import  __version__ as version

print(version)

setup(
    name='SomaticSeq',
    version=version,
    description='SomaticSeq: An ensemble approach to accurately detect somatic mutations using SomaticSeq',
    author='Li Tai Fang',
    author_email='li_tai.fang@roche.com',
    url='https://github.com/bioinform/somaticseq',
    packages=find_packages(),
    package_data={'': ['*.R']},
    install_requires=['pysam', 'numpy', 'scipy', 'pandas', 'xgboost'],
    scripts=['somaticseq/somaticseq_parallel.py',
             'somaticseq/run_somaticseq.py',
             'somaticseq/single_sample_vcf2tsv.py',
             'somaticseq/somatic_vcf2tsv.py',
             'somaticseq/somatic_xgboost.py',
             'somaticseq/SSeq_tsv2vcf.py',
             'utilities/linguistic_sequence_complexity.py',
             'utilities/lociCounterWithLabels.py',
             'utilities/remove_callers_from_somaticseq_tsv.py',
             'utilities/split_Bed_into_equal_regions.py',
             'utilities/tally_variants_from_multiple_vcfs.py',
             'utilities/variant_annotation.py',
             'utilities/vcfsorter.pl',
             'utilities/dockered_pipelines/makeAlignmentScripts.py',
             'utilities/dockered_pipelines/makeSomaticScripts.py',
             'utilities/dockered_pipelines/run_workflows.py',
             'genomicFileHandler/concat.py',
             'r_scripts/ada_model_builder_ntChange.R',
             'r_scripts/ada_model_predictor.R',
             ]
)
