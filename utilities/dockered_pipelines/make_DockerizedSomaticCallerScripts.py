#!/usr/bin/env python3

import sys, argparse, os, re
from copy import copy
from datetime import datetime
from shutil import move

MY_DIR = os.path.dirname(os.path.realpath(__file__))
RepoROOT = os.path.join(MY_DIR, os.pardir, os.pardir)

sys.path.append( MY_DIR )
sys.path.append( os.path.join(MY_DIR, os.pardir) ) # utilities dir for Bed splitting
sys.path.append( RepoROOT + os.sep + 'somaticseq' )

import split_Bed_into_equal_regions as split_bed

with open(RepoROOT + os.sep + 'VERSION') as fn:
    line_i = fn.readline().rstrip()
    VERSION = line_i.split('=')[1].lstrip('v')


ts = datetime.now().isoformat().replace(':', '.')



def run():

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Variant Call Type, i.e., snp or indel
    parser.add_argument('-outdir',     '--output-directory',     type=str,   help='Absolute path for output directory', default=os.getcwd())
    parser.add_argument('-somaticDir', '--somaticseq-directory', type=str,   help='SomaticSeq directory output name', default='SomaticSeq')
    parser.add_argument('-tbam',       '--tumor-bam',            type=str,   help='tumor bam file', required=True)
    parser.add_argument('-nbam',       '--normal-bam',           type=str,   help='normal bam file', required=True)
    parser.add_argument('-tname',      '--tumor-sample-name',    type=str,   help='tumor sample name', default='TUMOR')
    parser.add_argument('-nname',      '--normal-sample-name',   type=str,   help='normal sample name', default='NORMAL')
    parser.add_argument('-ref',        '--genome-reference',     type=str,   help='reference fasta file', required=True)
    parser.add_argument('-include',    '--inclusion-region',     type=str,   help='inclusion bed file', default=None)
    parser.add_argument('-exclude',    '--exclusion-region',     type=str,   help='exclusion bed file', )
    parser.add_argument('-dbsnp',      '--dbsnp-vcf',            type=str,   help='dbSNP vcf file, also requires .idx, .gz, and .gz.tbi files', required=True)
    parser.add_argument('-cosmic',     '--cosmic-vcf',           type=str,   help='cosmic vcf file', )
    parser.add_argument('-minVAF',     '--minimum-VAF',          type=float, help='minimum VAF to look for',)
    parser.add_argument('-action',     '--action',               type=str,   help='action for each mutation caller\' run script', default='echo')
    parser.add_argument('-somaticAct', '--somaticseq-action',    type=str,   help='action for each somaticseq.cmd', default='echo')

    parser.add_argument('-mutect',     '--run-mutect',        action='store_true', help='Run MuTect and Indelocator')
    parser.add_argument('-mutect2',    '--run-mutect2',       action='store_true', help='Run MuTect2')
    parser.add_argument('-varscan2',   '--run-varscan2',      action='store_true', help='Run VarScan2')
    parser.add_argument('-jsm',        '--run-jointsnvmix2',  action='store_true', help='Run JointSNVMix2')
    parser.add_argument('-sniper',     '--run-somaticsniper', action='store_true', help='Run SomaticSniper')
    parser.add_argument('-vardict',    '--run-vardict',       action='store_true', help='Run VarDict')
    parser.add_argument('-muse',       '--run-muse',          action='store_true', help='Run MuSE')
    parser.add_argument('-lofreq',     '--run-lofreq',        action='store_true', help='Run LoFreq')
    parser.add_argument('-scalpel',    '--run-scalpel',       action='store_true', help='Run Scalpel')
    parser.add_argument('-strelka2',   '--run-strelka2',      action='store_true', help='Run Strelka2')
    parser.add_argument('-somaticseq', '--run-somaticseq',    action='store_true', help='Run SomaticSeq')
    parser.add_argument('-train',      '--train-somaticseq',  action='store_true', help='SomaticSeq training mode for classifiers')

    parser.add_argument('-snvClassifier',   '--snv-classifier',    type=str, help='action for each .cmd',)
    parser.add_argument('-indelClassifier', '--indel-classifier',  type=str, help='action for each somaticseq.cmd',)
    parser.add_argument('-trueSnv',         '--truth-snv',         type=str, help='VCF of true hits')
    parser.add_argument('-trueIndel',       '--truth-indel',       type=str, help='VCF of true hits')

    parser.add_argument('--mutect2-arguments',            type=str, help='extra parameters for Mutect2',                   default='')
    parser.add_argument('--mutect2-filter-arguments',     type=str, help='extra parameters for FilterMutectCalls step',    default='')
    parser.add_argument('--varscan-arguments',            type=str, help='extra parameters for VarScan2',                  default='')
    parser.add_argument('--varscan-pileup-arguments',     type=str, help='extra parameters for mpileup used for VarScan2', default='')
    parser.add_argument('--jsm-train-arguments',          type=str, help='extra parameters for JointSNVMix2 train',        default='')
    parser.add_argument('--jsm-classify-arguments',       type=str, help='extra parameters for JointSNVMix2 classify',     default='')
    parser.add_argument('--somaticsniper-arguments',      type=str, help='extra parameters for SomaticSniper',             default='')
    parser.add_argument('--vardict-arguments',            type=str, help='extra parameters for VarDict',                   default='')
    parser.add_argument('--muse-arguments',               type=str, help='extra parameters',                               default='')
    parser.add_argument('--lofreq-arguments',             type=str, help='extra parameters for LoFreq',                    default='')
    parser.add_argument('--scalpel-discovery-arguments',  type=str, help='extra parameters for Scalpel discovery',         default='')
    parser.add_argument('--scalpel-export-arguments',     type=str, help='extra parameters for Scalpel export',            default='')
    parser.add_argument('--strelka-config-arguments',     type=str, help='extra parameters for Strelka2 config',           default='')
    parser.add_argument('--strelka-run-arguments',        type=str, help='extra parameters for Strelka2 run',              default='')
    parser.add_argument('--somaticseq-arguments',         type=str, help='extra parameters for SomaticSeq',                default='')
    
    parser.add_argument('--scalpel-two-pass',         action='store_true', help='Invokes two-pass setting in scalpel')
    parser.add_argument('-exome', '--exome-setting',  action='store_true', help='Invokes exome setting in Strelka2 and MuSE')

    parser.add_argument('-nt',        '--threads',        type=int, help='Split the input regions into this many threads', default=12)

    # Parse the arguments:
    args = parser.parse_args()
    workflowArguments = vars(args)

    return workflowArguments




def run_MuTect2(input_parameters, mem=4, nt=4, outvcf='MuTect2.vcf'):
    
    logdir         = input_parameters['output_directory'] + os.sep + 'logs'
    outfile        = logdir + os.sep + 'mutect2.{}.cmd'.format(ts)

    with open(outfile, 'w') as out:

        out.write( "#!/bin/bash\n\n" )
        
        out.write( '#$ -o {LOGDIR}\n'.format(LOGDIR=logdir) )
        out.write( '#$ -e {LOGDIR}\n'.format(LOGDIR=logdir) )
        out.write( '#$ -S /bin/bash\n' )
        out.write( '#$ -l h_vmem={}G\n'.format(mem) )
        out.write( 'set -e\n\n' )
        
        out.write( 'echo -e "Start at `date +"%Y/%m/%d %H:%M:%S"`" 1>&2\n\n' )

        out.write( 'tumor_name=`docker run --rm -v /:/mnt -u $UID --memory 1g lethalfang/samtools:1.7 samtools view -H /mnt/{TBAM} | egrep -w \'^@RG\' | grep -Po \'SM:[^\\t$]+\' | sed \'s/SM://\' | uniq | sed -e \'s/[[:space:]]*$//\'`\n'.format(TBAM=input_parameters['tumor_bam']) )
        out.write( 'normal_name=`docker run --rm -v /:/mnt -u $UID --memory 1g lethalfang/samtools:1.7 samtools view -H /mnt/{NBAM} | egrep -w \'^@RG\' | grep -Po \'SM:[^\\t$]+\' | sed \'s/SM://\' | uniq | sed -e \'s/[[:space:]]*$//\'`\n'.format(NBAM=input_parameters['normal_bam']) )

        out.write( '\n' )
        
        out.write( 'docker run --rm -v /:/mnt -u $UID broadinstitute/gatk:4.1.0.0 \\\n' )
        out.write( 'java -Xmx{MEM}g -jar /gatk/gatk.jar Mutect2 \\\n'.format( MEM=mem) )
        out.write( '--reference /mnt/{HUMAN_REFERENCE} \\\n'.format(HUMAN_REFERENCE=input_parameters['genome_reference']) )
        out.write( '{SELECTOR_ARG}\n'.format(SELECTOR_ARG='--intervals /mnt/{}'.format( input_parameters['inclusion_region']) if input_parameters['inclusion_region'] else '' ) )
        out.write( '-input /mnt/{NBAM} \\\n'.format(NBAM=input_parameters['normal_bam']) )
        out.write( '-input /mnt/{TBAM} \\\n'.format(TBAM=input_parameters['tumor_bam']) )
        out.write( '--normal-sample ${normal_name} \\\n' )
        out.write( '--tumor-sample ${tumor_name} \\\n' )
        out.write( '--native-pair-hmm-threads {threads} \\\n'.format(threads=nt) )
        out.write( '{EXTRA_ARGUMENTS} \\\n'.format(EXTRA_ARGUMENTS=input_parameters['mutect2_arguments']) )
        out.write( '--output /mnt/{OUTDIR}/unfiltered.{OUTVCF}.vcf\n'.format(OUTDIR=input_parameters['output_directory'], OUTVCF=outvcf) )

        out.write( '\n' )

        out.write( 'docker run --rm -v /:/mnt -u $UID broadinstitute/gatk:4.1.0.0 \\\n' )
        out.write( 'java -Xmx{MEM}g -jar /gatk/gatk.jar FilterMutectCalls \\\n'.format( MEM=mem ) )
        out.write( '--variant /mnt/{OUTDIR}/unfiltered.{OUTVCF} \\\n'.format(OUTDIR=input_parameters['output_directory'], OUTVCF=outvcf) )
        out.write( '{EXTRA_ARGUMENTS} \\\n'.format(EXTRA_ARGUMENTS=input_parameters['mutect2_filter_arguments']) )
        out.write( '--output /mnt/{OUTDIR}/{OUTVCF}\n'.format(OUTDIR=input_parameters['output_directory'], OUTVCF=outvcf) )

        out.write( '\necho -e "Done at `date +"%Y/%m/%d %H:%M:%S"`" 1>&2\n' )
        
    returnCode = os.system('{} {}'.format(input_parameters['action'], outfile) )

    return returnCode



def run_VarScan2(input_parameters, mem=4, minVAF=0.10, minMQ=25, minBQ=20, outvcf='VarScan2.vcf'):
    
    logdir         = input_parameters['output_directory'] + os.sep + 'logs'
    outfile        = logdir + os.sep + 'varscan2.{}.cmd'.format(ts)
    outname        = re.sub(r'\.[a-zA-Z]+$', '', outvcf )

    if input_parameters['minimum_VAF']:
        minVAF = input_parameters['minimum_VAF']

    selector_text  = '-l /mnt/{}'.format(input_parameters['inclusion_region']) if input_parameters['inclusion_region'] else ''

    with open(outfile, 'w') as out:
        
        out.write( "#!/bin/bash\n" )
        out.write( '\n' )
        
        out.write( '#$ -o {LOGDIR}\n'.format(LOGDIR=logdir) )
        out.write( '#$ -e {LOGDIR}\n'.format(LOGDIR=logdir) )
        out.write( '#$ -S /bin/bash\n' )
        out.write( '#$ -l h_vmem={}G\n'.format(mem) )
        out.write( 'set -e\n\n' )
        
        out.write( 'echo -e "Start at `date +"%Y/%m/%d %H:%M:%S"`" 1>&2\n\n' )

        out.write( 'docker run --rm -u $UID -v /:/mnt --memory {MEM}G lethalfang/samtools:1.7 bash -c \\\n'.format(MEM=mem) )
        out.write( '"samtools mpileup \\\n' )
        out.write( '-B -q {minMQ} -Q {minBQ} {extra_pileup_arguments} {selector_text} -f \\\n'.format(minMQ=minMQ, minBQ=minBQ, extra_pileup_arguments=input_parameters['varscan_pileup_arguments'], selector_text=selector_text) )
        out.write( '/mnt/{HUMAN_REFERENCE} \\\n'.format(HUMAN_REFERENCE=input_parameters['genome_reference']) )
        out.write( '/mnt/{NBAM} \\\n'.format(NBAM=input_parameters['normal_bam']) )
        out.write( '> /mnt/{OUTDIR}/normal.pileup"\n\n'.format(OUTDIR=input_parameters['output_directory']) )

        out.write( 'docker run --rm -u $UID -v /:/mnt --memory {MEM}G lethalfang/samtools:1.7 bash -c \\\n'.format(MEM=mem) )
        out.write( '"samtools mpileup \\\n' )
        out.write( '-B -q {minMQ} -Q {minBQ} {extra_pileup_arguments} {selector_text} -f \\\n'.format(minMQ=minMQ, minBQ=minBQ, extra_pileup_arguments=input_parameters['varscan_pileup_arguments'], selector_text=selector_text) )
        out.write( '/mnt/{HUMAN_REFERENCE} \\\n'.format(HUMAN_REFERENCE=input_parameters['genome_reference']) )
        out.write( '/mnt/{TBAM} \\\n'.format(TBAM=input_parameters['tumor_bam']) )
        out.write( '> /mnt/{OUTDIR}/tumor.pileup"\n\n'.format(OUTDIR=input_parameters['output_directory']) )
        
        out.write( 'docker run --rm -u $UID -v /:/mnt djordjeklisic/sbg-varscan2:v1 \\\n' )
        out.write( 'java -Xmx{MEM}g -jar /VarScan2.3.7.jar somatic \\\n'.format(MEM=mem) )
        out.write( '/mnt/{OUTDIR}/normal.pileup \\\n'.format(OUTDIR=input_parameters['output_directory']) )
        out.write( '/mnt/{OUTDIR}/tumor.pileup \\\n'.format(OUTDIR=input_parameters['output_directory']) )
        out.write( '/mnt/{OUTDIR}/{OUTNAME} {EXTRA_ARGS} --output-vcf 1 --min-var-freq {VAF}\n'.format(OUTDIR=input_parameters['output_directory'], OUTNAME=outname, VAF=minVAF, EXTRA_ARGS=input_parameters['varscan_arguments'] ) )
        
        out.write( '\n' )
        
        out.write( 'docker run --rm -u $UID -v /:/mnt djordjeklisic/sbg-varscan2:v1 \\\n' )
        out.write( 'java -Xmx${MEM}g -jar /VarScan2.3.7.jar processSomatic \\\n'.format(MEM=mem) )
        out.write( '/mnt/{OUTDIR}/{OUTNAME}.snp.vcf\n'.format(OUTDIR=input_parameters['output_directory'], OUTNAME=outname) )
        
        out.write( '\n' )
        
        out.write( 'docker run --rm -u $UID -v /:/mnt djordjeklisic/sbg-varscan2:v1 \\\n' )
        out.write( 'java -Xmx{MEM}g -jar /VarScan2.3.7.jar somaticFilter \\\n'.format(MEM=mem) )
        out.write( '/mnt/{OUTDIR}/{OUTNAME}.snp.Somatic.hc.vcf \\\n'.format(OUTDIR=input_parameters['output_directory'], OUTNAME=outname) )
        out.write( '-indel-file /mnt/{OUTDIR}/{OUTNAME}.indel.vcf \\\n'.format(OUTDIR=input_parameters['output_directory'], OUTNAME=outname) )
        out.write( '-output-file /mnt/{OUTDIR}/{OUTNAME}.snp.Somatic.hc.filter.vcf\n'.format(OUTDIR=input_parameters['output_directory'], OUTNAME=outname) )
        
        out.write( '\n' )
        
        out.write( 'rm {OUTDIR}/normal.pileup\n'.format(OUTDIR=input_parameters['output_directory']) )
        out.write( 'rm {OUTDIR}/tumor.pileup\n'.format(OUTDIR=input_parameters['output_directory']) )
        out.write( '\n' )
        
        
    
        out.write( '\necho -e "Done at `date +"%Y/%m/%d %H:%M:%S"`" 1>&2\n' )
    
        
    returnCode = os.system('{} {}'.format(input_parameters['action'], outfile) )

    return returnCode



def run_JointSNVMix2(input_parameters, mem=8, skip_size=10000, converge_threshold=0.01, outvcf='JointSNVMix2.vcf'):
    
    logdir         = input_parameters['output_directory'] + os.sep + 'logs'
    outfile        = logdir + os.sep + 'jointsnvmix2.{}.cmd'.format(ts)
    reference_dict = re.sub(r'\.[a-zA-Z]+$', '', input_parameters['genome_reference'] ) + '.dict'
    
    with open(outfile, 'w') as out:
        
        out.write( "#!/bin/bash\n" )
        out.write( '\n' )
        
        out.write( '#$ -o {LOGDIR}\n'.format(LOGDIR=logdir) )
        out.write( '#$ -e {LOGDIR}\n'.format(LOGDIR=logdir) )
        out.write( '#$ -S /bin/bash\n' )
        out.write( '#$ -l h_vmem={}G\n'.format(mem) )
        out.write( 'set -e\n' )
        out.write( '\n' )
        
        out.write( 'echo -e "Start at `date +"%Y/%m/%d %H:%M:%S"`" 1>&2\n' )
        out.write( '\n' )
        
        out.write( 'docker run --rm -v /:/mnt --memory {MEM}G -u $UID lethalfang/jointsnvmix2:0.7.5 \\\n'.format(MEM=mem) )
        out.write( '/opt/JointSNVMix-0.7.5/build/scripts-2.7/jsm.py train joint_snv_mix_two \\\n' )
        out.write( '--convergence_threshold {} \\\n'.format(converge_threshold) )
        out.write( '--skip_size {SKIP_SIZE} \\\n'.format(SKIP_SIZE=skip_size) )
        out.write( '{EXTRA_TRAIN_ARGUMENT} \\\n'.format(EXTRA_TRAIN_ARGUMENT=input_parameters['jsm_train_arguments']) )
        out.write( '/mnt/{HUMAN_REFERENCE} \\\n'.format(HUMAN_REFERENCE=input_parameters['genome_reference']) )
        out.write( '/mnt/{NORMAL_BAM} \\\n'.format(NORMAL_BAM=input_parameters['normal_bam']) )
        out.write( '/mnt/{TUMOR_NAM} \\\n'.format(TUMOR_NAM=input_parameters['tumor_bam']) )
        out.write( '/opt/JointSNVMix-0.7.5/config/joint_priors.cfg \\\n' )
        out.write( '/opt/JointSNVMix-0.7.5/config/joint_params.cfg \\\n' )
        out.write( '/mnt/{OUTDIR}/jsm.parameter.cfg\n'.format(OUTDIR=input_parameters['output_directory']) )
        out.write( '\n' )
        
        out.write( 'echo -e \'##fileformat=VCFv4.1\' > {OUTDIR}/{OUTVCF}\n'.format(OUTDIR=input_parameters['output_directory'], OUTVCF=outvcf) )
        out.write( 'echo -e \'##INFO=<ID=AAAB,Number=1,Type=Float,Description="Probability of Joint Genotype AA in Normal and AB in Tumor">\' >> {OUTDIR}/{OUTVCF}\n'.format(OUTDIR=input_parameters['output_directory'], OUTVCF=outvcf) )
        out.write( 'echo -e \'##INFO=<ID=AABB,Number=1,Type=Float,Description="Probability of Joint Genotype AA in Normal and BB in Tumor">\' >> {OUTDIR}/{OUTVCF}\n'.format(OUTDIR=input_parameters['output_directory'], OUTVCF=outvcf) )
        out.write( 'echo -e \'##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\' >> {OUTDIR}/{OUTVCF}\n'.format(OUTDIR=input_parameters['output_directory'], OUTVCF=outvcf) )
        out.write( 'echo -e \'##FORMAT=<ID=RD,Number=1,Type=Integer,Description="Depth of reference-supporting bases (reads1)">\' >> {OUTDIR}/{OUTVCF}\n'.format(OUTDIR=input_parameters['output_directory'], OUTVCF=outvcf) )
        out.write( 'echo -e \'##FORMAT=<ID=AD,Number=1,Type=Integer,Description="Depth of variant-supporting bases (reads2)">\' >> {OUTDIR}/{OUTVCF}\n'.format(OUTDIR=input_parameters['output_directory'], OUTVCF=outvcf) )
        out.write( 'echo -e \'#CHROM\\tPOS\\tID\\tREF\\tALT\\tQUAL\\tFILTER\\tINFO\\tFORMAT\\tNORMAL\\tTUMOR\' >> {OUTDIR}/{OUTVCF}\n'.format(OUTDIR=input_parameters['output_directory'], OUTVCF=outvcf) )
        out.write( '\n' )
        
        out.write( 'docker run --rm -v /:/mnt --memory {}G -u $UID lethalfang/jointsnvmix2:0.7.5 bash -c \\\n'.format( mem ) )
        out.write( '"/opt/JointSNVMix-0.7.5/build/scripts-2.7/jsm.py classify joint_snv_mix_two \\\n' )
        out.write( '{EXTRA_CLASSIFY_ARGUMENTS} \\\n'.format(EXTRA_CLASSIFY_ARGUMENTS=input_parameters['jsm_classify_arguments']) )
        out.write( '/mnt/{HUMAN_REFERENCE} \\\n'.format(HUMAN_REFERENCE=input_parameters['genome_reference']) )
        out.write( '/mnt/{NORMAL_BAM} \\\n'.format(NORMAL_BAM=input_parameters['normal_bam']) )
        out.write( '/mnt/{TUMOR_NAM} \\\n'.format(TUMOR_NAM=input_parameters['tumor_bam']) )
        out.write( "/mnt/{OUTDIR}/jsm.parameter.cfg \\\n".format(OUTDIR=input_parameters['output_directory']) )
        out.write( '/dev/stdout | awk -F \'\\t\' \'NR!=1 && \\$4!=\\"N\\" && \\$10+\\$11>=0.95\' | \\\n' )
        out.write( 'awk -F \'\\t\' \'{print \\$1 \\"\\t\\" \\$2 \\"\\t.\\t\\" \\$3 \\"\\t\\" \\$4 \\"\\t.\\t.\\tAAAB=\\" \\$10 \\";AABB=\\" \\$11 \\"\\tRD:AD\\t\\" \\$5 \\":\\" \\$6 \\"\\t\\" \\$7 \\":\\" \\$8}\' \\\n' )
        out.write( '| /opt/vcfsorter.pl /mnt/{GRCh_DICT} - >> /mnt/{OUTDIR}/{OUTVCF}"\n'.format(GRCh_DICT=reference_dict, OUTDIR=input_parameters['output_directory'], OUTVCF=outvcf) )
        out.write( '\n' )
        
        if input_parameters['threads'] > 1:
            out.write( '\n\ni=1\n' )
            out.write( 'while [[ $i -le {} ]]\n'.format(input_parameters['threads']) )
            out.write( 'do\n' )
            out.write( '    docker run --rm -v /:/mnt -u $UID lethalfang/bedtools:2.26.0 bash -c "bedtools intersect -a /mnt/{OUTDIR}/{OUTVCF} -b /mnt/{OUTDIR}/${{i}}/${{i}}.bed -header | uniq > /mnt/{OUTDIR}/${{i}}/{OUTVCF}"\n'.format(OUTDIR=input_parameters['output_directory'], OUTVCF=outvcf,) )
            out.write( '    i=$(( $i + 1 ))\n' )
            out.write( 'done\n' )
        
        out.write( '\n' )
        out.write( 'echo -e "Done at `date +"%Y/%m/%d %H:%M:%S"`" 1>&2\n' )
        
    returnCode = os.system('{} {}'.format(input_parameters['action'], outfile) )

    return returnCode



def run_SomaticSniper(input_parameters, MQ=1, somaticQuality=15, prior=0.00001, mem=4, outvcf='SomaticSniper.vcf'):

    logdir         = input_parameters['output_directory'] + os.sep + 'logs'
    outfile        = logdir + os.sep + 'somaticsniper.{}.cmd'.format(ts)

    with open(outfile, 'w') as out:
        
        out.write( "#!/bin/bash\n" )
        out.write( '\n' )
        
        out.write( '#$ -o {LOGDIR}\n'.format(LOGDIR=logdir) )
        out.write( '#$ -e {LOGDIR}\n'.format(LOGDIR=logdir) )
        out.write( '#$ -S /bin/bash\n' )
        out.write( '#$ -l h_vmem={}G\n'.format(mem) )
        out.write( 'set -e\n\n' )
        
        out.write( 'echo -e "Start at `date +"%Y/%m/%d %H:%M:%S"`" 1>&2\n\n' )
        
        out.write( 'docker run --rm -v /:/mnt -u $UID --memory {MEM}G lethalfang/somaticsniper:1.0.5.0-2 \\\n'.format(MEM=mem) )
        out.write( '/opt/somatic-sniper/build/bin/bam-somaticsniper \\\n' )
        out.write( '-q {MQ} -Q {SQ} -s {PRIOR} -F vcf {EXTRA_ARGS} \\\n'.format(MQ=MQ, SQ=somaticQuality, PRIOR=prior, EXTRA_ARGS=input_parameters['somaticsniper_arguments']) )
        out.write( '-f /mnt/{HUMAN_REFERENCE} \\\n'.format(HUMAN_REFERENCE=input_parameters['genome_reference']) )
        out.write( '/mnt/{TBAM} \\\n'.format(TBAM=input_parameters['tumor_bam']) )
        out.write( '/mnt/{NBAM} \\\n'.format(NBAM=input_parameters['normal_bam']) )
        out.write( '/mnt/{OUTDIR}/{OUTVCF}\n'.format(OUTDIR=input_parameters['output_directory'], OUTVCF=outvcf) )

        if input_parameters['threads'] > 1:
            out.write( '\n\ni=1\n' )
            out.write( 'while [[ $i -le {} ]]\n'.format(input_parameters['threads']) )
            out.write( 'do\n' )
            out.write( '    docker run --rm -v /:/mnt -u $UID lethalfang/bedtools:2.26.0 bash -c "bedtools intersect -a /mnt/{OUTDIR}/{OUTVCF} -b /mnt/{OUTDIR}/${{i}}/${{i}}.bed -header | uniq > /mnt/{OUTDIR}/${{i}}/{OUTVCF}"\n'.format(OUTDIR=input_parameters['output_directory'], OUTVCF=outvcf,) )
            out.write( '    i=$(( $i + 1 ))\n' )
            out.write( 'done\n' )
        
        out.write( '\n' )
        out.write( 'echo -e "Done at `date +"%Y/%m/%d %H:%M:%S"`" 1>&2\n' )



    returnCode = os.system('{} {}'.format(input_parameters['action'], outfile) )

    return returnCode



def run_VarDict(input_parameters, mem=14, minVAF=0.05, outvcf='VarDict.vcf'):
    
    logdir         = input_parameters['output_directory'] + os.sep + 'logs'
    outfile        = logdir + os.sep + 'vardict.{}.cmd'.format(ts)
    
    if input_parameters['minimum_VAF']:
        minVAF = input_parameters['minimum_VAF']

    total_bases = 0
    num_lines   = 0

    if input_parameters['inclusion_region']:
        bed_file = input_parameters['inclusion_region']
        
        with open(bed_file) as bed:
            line_i = bed.readline().rstrip()
            while line_i.startswith('track'):
                line_i = bed.readline().rstrip()
            while line_i:
                item = line_i.rstrip().split('\t')
                total_bases = total_bases + int(item[2]) - int(item[1])
                num_lines += 1
                line_i = bed.readline().rstrip()
    else:
        fai_file = input_parameters['genome_reference'] + '.fai'
        bed_file = '{}/{}'.format(input_parameters['output_directory'], 'genome.bed')
        
        with open(fai_file) as fai, open(bed_file, 'w') as wgs_bed:
            for line_i in fai:
                
                item = line_i.split('\t')
                
                total_bases += int( item[1] )
                num_lines   += 1
                
                wgs_bed.write( '{}\t{}\t{}\n'.format(item[0], '0', item[1]) )
    
    with open(outfile, 'w') as out:

        out.write( "#!/bin/bash\n\n" )
        
        out.write( '#$ -o {LOGDIR}\n'.format(LOGDIR=logdir) )
        out.write( '#$ -e {LOGDIR}\n'.format(LOGDIR=logdir) )
        out.write( '#$ -S /bin/bash\n' )
        out.write( '#$ -l h_vmem={}G\n'.format(mem) )
        out.write( 'set -e\n\n' )
        
        out.write( 'echo -e "Start at `date +"%Y/%m/%d %H:%M:%S"`" 1>&2\n\n' )

        # Decide if Bed file needs to be "split" such that each line has a small enough region
        if total_bases/num_lines > 50000:
            out.write( 'docker run --rm -v /:/mnt -u $UID --memory {MEM}G lethalfang/somaticseq:{VERSION} \\\n'.format(MEM=mem, VERSION=VERSION) )
            out.write( '/opt/somaticseq/utilities/split_mergedBed.py \\\n' )
            out.write( '-infile /mnt/{SELECTOR} -outfile /mnt/{OUTDIR}/split_regions.bed\n\n'.format(SELECTOR=bed_file, OUTDIR=input_parameters['output_directory']) )

            bed_file = '{OUTDIR}/split_regions.bed'.format( OUTDIR=input_parameters['output_directory'] )

        out.write( 'docker run --rm -v /:/mnt -u $UID --memory {MEM}G lethalfang/vardictjava:1.5.2 bash -c \\\n'.format(MEM=mem) )
        out.write( '"/opt/VarDict-1.5.2/bin/VarDict \\\n' )
        out.write( '{EXTRA_ARG} \\\n'.format(EXTRA_ARG=input_parameters['vardict_arguments']) )
        out.write( '-G /mnt/{HUMAN_REFERENCE} \\\n'.format(HUMAN_REFERENCE=input_parameters['genome_reference']) )
        out.write( '-f {VAF} -h \\\n'.format(VAF=minVAF) )
        out.write( '-b \'/mnt/{TBAM}|/mnt/{NBAM}\' \\\n'.format(TBAM=input_parameters['tumor_bam'], NBAM=input_parameters['normal_bam']) )
        out.write( '-Q 1 -c 1 -S 2 -E 3 -g 4 /mnt/{INTPUT_BED} \\\n'.format(INTPUT_BED=bed_file) )
        out.write( '> /mnt/{OUTDIR}/vardict.var"\n\n'.format(OUTDIR=input_parameters['output_directory']) )
        
        out.write( 'docker run --rm -v /:/mnt -u $UID --memory {MEM}G lethalfang/vardictjava:1.5.2 \\\n'.format(MEM=mem) )
        out.write( 'bash -c "cat /mnt/{OUTDIR}/vardict.var | awk \'NR!=1\' | /opt/VarDict/testsomatic.R | /opt/VarDict/var2vcf_paired.pl -N \'TUMOR|NORMAL\' -f {VAF} \\\n'.format(OUTDIR=input_parameters['output_directory'], VAF=minVAF ) )
        out.write( '> /mnt/{OUTDIR}/{OUTVCF}"\n\n'.format(OUTDIR=input_parameters['output_directory'], OUTVCF=outvcf) )

        out.write( '\necho -e "Done at `date +"%Y/%m/%d %H:%M:%S"`" 1>&2\n' )
        
    returnCode = os.system('{} {}'.format(input_parameters['action'], outfile) )

    return returnCode



def run_MuSE(input_parameters, mem=8, outvcf='MuSE.vcf'):

    logdir         = input_parameters['output_directory'] + os.sep + 'logs'
    outfile        = logdir + os.sep + 'muse.{}.cmd'.format(ts)

    statFlag = '-E' if input_parameters['exome_setting'] else '-G'
    
    with open(outfile, 'w') as out:

        out.write( "#!/bin/bash\n\n" )
        
        out.write( '#$ -o {LOGDIR}\n'.format(LOGDIR=logdir) )
        out.write( '#$ -e {LOGDIR}\n'.format(LOGDIR=logdir) )
        out.write( '#$ -S /bin/bash\n' )
        out.write( '#$ -l h_vmem={}G\n'.format(mem) )
        out.write( 'set -e\n\n' )
        
        out.write( 'echo -e "Start at `date +"%Y/%m/%d %H:%M:%S"`" 1>&2\n\n' )

        out.write( 'cat {SELECTOR} | awk -F "\\t" \'{{print $1 "\\t" $2 "\\t" $3}}\' > {OUTDIR}/bed_3columns.bed\n\n'.format(SELECTOR=input_parameters['inclusion_region'], OUTDIR=input_parameters['output_directory'] ) )
        
        out.write( 'docker run --rm -v /:/mnt -u $UID --memory {}G marghoob/muse:1.0rc_c \\\n'.format(mem) )
        out.write( 'MuSEv1.0rc_submission_c039ffa call \\\n' )
        out.write( '-O /mnt/{OUTDIR}/MuSE \\\n'.format(OUTDIR=input_parameters['output_directory']) )
        out.write( '-l /mnt/{OUTDIR}/bed_3columns.bed \\\n'.format(OUTDIR=input_parameters['output_directory']) )
        out.write( '-f /mnt/{HUMAN_REFERENCE} \\\n'.format(HUMAN_REFERENCE=input_parameters['genome_reference']) )
        out.write( '/mnt/{TBAM} \\\n'.format(TBAM=input_parameters['tumor_bam']) )
        out.write( '/mnt/{NBAM}\n\n'.format(NBAM=input_parameters['normal_bam']) )
        
        out.write( 'docker run --rm -v /:/mnt -u $UID --memory {}G marghoob/muse:1.0rc_c \\\n'.format(mem) )
        out.write( 'MuSEv1.0rc_submission_c039ffa sump \\\n' )
        out.write( '-I /mnt/{OUTDIR}/MuSE.MuSE.txt \\\n'.format(OUTDIR=input_parameters['output_directory']) )
        out.write( '{statFlag} {EXTRA_ARGS} -O /mnt/{OUTDIR}/{OUTVCF} \\\n'.format(statFlag=statFlag, EXTRA_ARGS=input_parameters['muse_arguments'], OUTDIR=input_parameters['output_directory'], OUTVCF=outvcf) )
        out.write( '-D /mnt/{DBSNP}.gz\n'.format(DBSNP=input_parameters['dbsnp_vcf']) )
    
        out.write( '\necho -e "Done at `date +"%Y/%m/%d %H:%M:%S"`" 1>&2\n' )
        
    returnCode = os.system('{} {}'.format(input_parameters['action'], outfile) )

    return returnCode



def run_Strelka2(input_parameters, mem=4, outdirname='Strelka'):

    logdir         = input_parameters['output_directory'] + os.sep + 'logs'
    outfile        = logdir + os.sep + 'strelka.{}.cmd'.format(ts)
    
    exomeFlag = '--exome' if input_parameters['exome_setting'] else ''
    bed_gz = os.path.basename(input_parameters['inclusion_region']) + '.gz'
    
    with open(outfile, 'w') as out:

        out.write( "#!/bin/bash\n\n" )
        
        out.write( '#$ -o {LOGDIR}\n'.format(LOGDIR=logdir) )
        out.write( '#$ -e {LOGDIR}\n'.format(LOGDIR=logdir) )
        out.write( '#$ -S /bin/bash\n' )
        out.write( '#$ -l h_vmem={}G\n'.format(mem) )
        out.write( 'set -e\n\n' )
        
        out.write( 'echo -e "Start at `date +"%Y/%m/%d %H:%M:%S"`" 1>&2\n\n' )

        out.write( 'docker run -v /:/mnt -u $UID --rm --memory {MEM}G lethalfang/tabix:1.7 bash -c "cat /mnt/{SELECTOR} | bgzip > /mnt/{OUTDIR}/{BEDGZ}\"\n'.format(MEM=mem, SELECTOR=input_parameters['inclusion_region'], OUTDIR=input_parameters['output_directory'], BEDGZ=bed_gz ) )
        out.write( 'docker run -v /:/mnt -u $UID --rm --memory {MEM}G lethalfang/tabix:1.7 tabix -f /mnt/{OUTDIR}/{BEDGZ}\n\n'.format(MEM=mem, OUTDIR=input_parameters['output_directory'], BEDGZ=bed_gz ) )

        out.write( 'docker run --rm -v /:/mnt -u $UID --memory {MEM}G lethalfang/strelka:2.9.5 \\\n'.format(MEM=mem) )
        out.write( '/opt/strelka/bin/configureStrelkaSomaticWorkflow.py \\\n' )
        out.write( '--tumorBam=/mnt/{TBAM} \\\n'.format( TBAM=input_parameters['tumor_bam'] ) )
        out.write( '--normalBam=/mnt/{NBAM} \\\n'.format( NBAM=input_parameters['normal_bam'] ) )
        out.write( '--referenceFasta=/mnt/{HUMAN_REFERENCE} \\\n'.format( HUMAN_REFERENCE=input_parameters['genome_reference'] ) )
        out.write( '--callMemMb={MEM} \\\n'.format(MEM=mem*1024) )
        out.write( '--callRegions=/mnt/{BEDGZ} \\\n'.format(BEDGZ=bed_gz) )
        out.write( '{EXOMEFLAG} {EXTRA_ARGS} \\\n'.format(EXOMEFLAG=exomeFlag, EXTRA_ARGS=input_parameters['strelka_config_arguments']) )
        out.write( '--runDir=/mnt/{OUTDIR}/{DIRNAME}\n\n'.format(OUTDIR=input_parameters['output_directory'], DIRNAME=outdirname) )        
        
        out.write( 'docker run --rm -v /:/mnt -u $UID --memory {MEM}G lethalfang/strelka:2.9.5 \\\n'.format(MEM=mem) )
        out.write( '/mnt/{OUTDIR}/{DIRNAME}/runWorkflow.py -m local -j 1 {EXTRA_ARGS}\n'.format(OUTDIR=input_parameters['output_directory'], DIRNAME=outdirname, EXTRA_ARGS=input_parameters['strelka_run_arguments']) )

        out.write( '\necho -e "Done at `date +"%Y/%m/%d %H:%M:%S"`" 1>&2\n' )
        
    returnCode = os.system('{} {}'.format(input_parameters['action'], outfile) )

    return returnCode








##########################################################

if __name__ == '__main__':
    
    workflowArguments = run()
    
    if workflowArguments['inclusion_region']:
        bed_file = workflowArguments['inclusion_region']
        
    else:
        split_bed.fai2bed(workflowArguments['genome_reference'] + '.fai', workflowArguments['output_directory'] + os.sep + 'genome.bed')
        bed_file = workflowArguments['output_directory'] + os.sep + 'genome.bed'
    
    split_bed.split(bed_file, workflowArguments['output_directory'] + os.sep + 'bed', workflowArguments['threads'])

    os.makedirs(workflowArguments['output_directory'] + os.sep + 'logs', exist_ok=True)

    # Unparallelizables
    if workflowArguments['run_jointsnvmix2']:
        run_JointSNVMix2(workflowArguments)

    if workflowArguments['run_somaticsniper']:
        run_SomaticSniper(workflowArguments)
    
        
    for thread_i in range(1, workflowArguments['threads']+1):
        
        if workflowArguments['threads'] > 1:
            
            perThreadParameter = copy(workflowArguments)
            
            # Add OUTDIR/thread_i for each thread
            perThreadParameter['output_directory'] = workflowArguments['output_directory'] + os.sep + str(thread_i)
            perThreadParameter['inclusion_region'] = '{}/{}.bed'.format( perThreadParameter['output_directory'], str(thread_i) )
            
            os.makedirs(perThreadParameter['output_directory'] + os.sep + 'logs', exist_ok=True)
            
            # Move 1.bed, 2.bed, ..., n.bed to each thread's subdirectory
            move(workflowArguments['output_directory'] + os.sep + str(thread_i) + '.bed', perThreadParameter['output_directory'])
        
        else:
            perThreadParameter = copy(workflowArguments)
            perThreadParameter['inclusion_region'] = bed_file
        
        # Invoke parallelizable callers one by one:
        if workflowArguments['run_mutect2']:
            run_MuTect2( perThreadParameter )
            
        if workflowArguments['run_varscan2']:
            run_VarScan2( perThreadParameter )
            
        if workflowArguments['run_vardict']:
            run_VarDict( perThreadParameter )

        if workflowArguments['run_muse']:
            run_MuSE( perThreadParameter )

        if workflowArguments['run_strelka2']:
            run_Strelka2( perThreadParameter )
