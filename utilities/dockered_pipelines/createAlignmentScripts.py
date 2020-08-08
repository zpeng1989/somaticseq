#!/usr/bin/env python3

import sys, argparse, os, re
import logging
from copy import copy
from shutil import move
from datetime import datetime

FORMAT = '%(levelname)s %(asctime)-15s %(name)-20s %(message)s'
logger = logging.getLogger('Make Somatic Workflow Scripts')

logger.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.INFO, format=FORMAT)


def run():
    
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # INPUT FILES and Global Options
    parser.add_argument('-outdir', '--output-directory',       type=str, default=os.getcwd())
    parser.add_argument('-inbam',  '--in-bam',                 type=str, help='input bam path if already aligned')
    parser.add_argument('-outbam', '--out-bam',                type=str, help='output bam file name', required=True)
    parser.add_argument('-nt',     '--threads',                type=int, default=1)
    parser.add_argument('-ref',    '--genome-reference',       type=str, default=1)
    parser.add_argument('-extras', '--extra-picard-arguments', type=str, default='')
    parser.add_argument('-tech',   '--container-tech',         type=str, choices=('docker', 'singularity'), default='docker')
    
    parser.add_argument('-trim',   '--run-trimming',       action='store_true')
    parser.add_argument('-fq1',    '--in-fastq1',          type=str, help='input forward fastq path')
    parser.add_argument('-fq2',    '--in-fastq2',          type=str, help='input reverse fastq path of paired end')
    parser.add_argument('-fout1',  '--out-fastq1-name',    type=str, required=True)
    parser.add_argument('-fout2',  '--out-fastq2-name',    type=str, )
    parser.add_argument('--trim-software',                 type=str, choices=('alientrimmer', 'trimmomatic'), default='alientrimmer')
    parser.add_argument('--extra-trim-arguments',          type=str, default='')

    parser.add_argument('-align',   '--run-alignment', action='store_true')
    parser.add_argument('-header', '--bam-header',     type=str, default='@RG\tID:ID00\tLB:LB0\tPL:illumina\tSM:Sample')
    parser.add_argument('--extra-bwa-arguments',       type=str, default='')
    
    parser.add_argument('-markdup',  '--run-mark-duplicates',   action='store_true')
    parser.add_argument('--extra-markdup-arguments',    type=str, default='')
    parser.add_argument('--parallelize-markdup',  action='store_true', help='parallelize by splitting input bam files and work on each independently, and then merge.')


    args = parser.parse_args()
    
    input_parameters = vars(args)

    return args, input_parameters




if __name__ == '__main__':
    
    args, input_parameters = run()
    
    workflow_tasks = {'trim_jobs':[], 'alignment_jobs': [], 'markdup_jobs': [], 'merging_jobs': [] }
    
    if args.run_trimming:
        import utilities.dockered_pipelines.alignments.trim as trim
        
        if args.trim_software == 'trimmomatic':
            trimming_script = trim.trimmomatic(input_parameters, args.container_tech)
        elif args.trim_software == 'alientrimmer':
            trimming_script = trim.alienTrimmer(input_parameters, args.container_tech)

        workflow_tasks['trim_jobs'].append(trimming_script)
        
        # If this step is undertaken, replace in_fastqs as out_fastqs for the next step:
        input_parameters['in_fastq1'] = os.path.join( input_parameters['output_directory'], input_parameters['out_fastq1_name'] )
        
        if input_parameters['in_fastq2']:
            input_parameters['in_fastq2'] = os.path.join( input_parameters['output_directory'], input_parameters['out_fastq2_name'] )


    if args.run_alignment:
        import utilities.dockered_pipelines.alignments.align as align
        alignment_script = align.bwa(input_parameters, args.container_tech)

        workflow_tasks['alignment_jobs'].append(alignment_script)

    if args.run_mark_duplicates:
        import utilities.dockered_pipelines.alignments.markdup as markdup
        
        if args.parallelize_markdup:
            fractional_markdup_scripts, merge_markdup_script = markdup.picard_parallel(input_parameters, args.container_tech)
        else:
            markdup_script = markdup.picard(input_parameters, args.container_tech)
