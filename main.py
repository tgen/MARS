#!/usr/bin/env python3

# Primary Developer: Bertrand Odinet

# Additional Developers: Dr. Jonathan J. Keats, Dr. Christophe Legendre, Bryce Turner, Daniel Enriquez

import argparse
import pandas as pd
import os
import sys
import scipy
from gtfparse import read_gtf
from subprocess import call
from scipy import stats

# shell=True is so you can handle redirects
call("echo 'Running'", shell=True)

# Argument parser to facilitate calling from the command line

parser = argparse.ArgumentParser(description='Check purity of multiple myeloma tumor samples.')
# Add input argument for BAM file from patient/sample. This is required for the program.
parser.add_argument('-i', '--input_bam',
                    required=True,
                    help='BAM file for tumor sample')
# Add input argument for GTF file containing regions to isolate.
parser.add_argument('-g', '--input_gtf',
                    help='GTF to be used in processing')
parser.add_argument('-t', '--threads',
                    default=1,
                    type=int,
                    help='Number of threads to use. User must make threads available')
# Add input argument for GTF file containing regions to isolate.
parser.add_argument('-f', '--reference_fasta',
                    default=None,
                    help='Reference genome fasta to be used in processing')
# Add input argument for output path. If no argument or only a -o is provided, program defaults
# to current working directory.
parser.add_argument('-o', '--output_path',
                    nargs='?',
                    const=str(os.getcwd()),
                    default=str(os.getcwd()),
                    help='Output path to write files. Defaults to current working directory')
# Add input argument for option to build files. If not provided, program defaults to the user specified GTF, or
# to the default GTF if no -g input is provided. Stored as true for use in decision tree later on.
parser.add_argument('-b', '--build_files',
                    action='store_true',
                    help='Include -b if you would like to build files, otherwise typing -b is unnecessary')
# Add input argument for option to keep temporary files. Stored as true for use in decision tree later on.
parser.add_argument('-k', '--keep_temp',
                    action='store_true',
                    help='Include -k if you would like to keep the temporary files. Ignore to remove temporary files '
                         'once the program is finished')
# Add input argument for sample name. If none is provided, the name of the BAM file will be used.
parser.add_argument('-n', '--sample_name',
                    help='Desired name for the sample and associated files. Defaults to the same of the BAM file')
# Add input argument for resource directory, the directory to pull files used to build the GTF and interpret the
# featureCounts output. Also defaults to current working directory if not specified.
parser.add_argument('-d', '--resource_directory',
                    nargs='?',
                    const=str(os.getcwd()),
                    default=str(os.getcwd()),
                    help='Include -d /path/to/resource/files to specify a directory to pull resource files from.'
                         'Defaults to current directory.')
parser.add_argument('-build_only', '--build_only',
                    action='store_true',
                    help='Invoke -build_only to stop the program after the new GTF is built.')

# Generate accessible arguments by calling parse_args
args = parser.parse_args()

# Rename each input to something shorter and more intuitive for later use in the code.
out_path = args.output_path
in_gtf = args.input_gtf
input_aln = args.input_bam
build = args.build_files
threads = args.threads
keep_temp = args.keep_temp
samplename = args.sample_name
resource_directory = args.resource_directory
ref_fasta = args.reference_fasta
build_only = args.build_only

# This statement sets the sample name to the name of the BAM if no name is provided, using os.basename to extract the
# file name from the input path and os.splitext to split the name into ('filename', 'extension'),
# e.g. ('example', '.txt). The [0] accesses the first string in that output (the file name w/o extension).
if samplename is None:
    samplename = os.path.splitext(os.path.basename(input_aln))[0]

# ----------------------------------------- #
#  DEFAULTS
# ----------------------------------------- #
# This section reads in several user-definable defaults for the program. They are the name of the default GTF,
# chromosomes to search, IG components to consider, and path to featureCounts respectively. They can be changed by
# editing the USER_DEFAULTS.txt file in the resource directory.
DEFAULT_FILE = open(r'%s/USER_DEFAULTS.txt' % resource_directory, 'r')
default_parameters = DEFAULT_FILE.read().splitlines()
default_gtf = default_parameters[2]
default_chromosome_list = default_parameters[4].split()
default_component_list = default_parameters[6].split()
featurecounts_path = default_parameters[8]


# ------------------------------------------------------------------------------------------------------------------- #
# FUNCTIONS THAT SUPPORT CODE AT BOTTOM
# ------------------------------------------------------------------------------------------------------------------- #

def read_aln_file(filename, threads, out_path, reference_genome_fasta=None):
    """
    read the alignment file whether it is a SAM, BAM or CRAM file and returns the bam file handle
    :return: aln read file handle (bamh or alnh)
    """

    extension = os.path.splitext(filename)[1]
    basepath = os.path.splitext(filename)[0]
    basename = os.path.splitext(os.path.basename(filename))[0]
    try:
        if extension == ".cram":
            if reference_genome_fasta is None:
                raise FileNotFoundError(
                    "ERROR: reading CRAM file requires a Reference Genome Fasta File To be Provided with its FAI index.")
            print('Conversion to BAM required: running samtools')
            call("samtools view --threads %s -bh %s -o %s/%s.bam -T %s" % (threads, filename, out_path, basename,
                                                                        reference_genome_fasta), shell=True)
            print('Indexing new BAM file')
            call("samtools index -@ %s -b %s/%s.bam" % (threads, out_path, basename), shell=True)
            print('Conversion successful')
            return '%s/%s.bam' % (out_path, basename)
        elif extension == ".bam":
            return filename
        elif extension == ".sam":
            return filename
        else:
            print('ERROR: HALTING PROGRAM AND RETURNING VARIABLES FOR DEBUGGING')
            print('FILENAME:' + filename)
            print('REFERENCE FASTA:' + reference_genome_fasta)
            print('THREADS:' + threads)
            print('EXTENSION:' + extension)
            print('BASE PATH:' + basepath)
            print('BASE NAME:' + basename)

            sys.exit("EXPECTED EXTENSION for ALIGNMENT FILE NOT FOUND; must be either .cram, .bam or .sam")

    except FileNotFoundError as fnf:
        sys.exit(fnf)

    except Exception as e:
        sys.exit(e)


def isolate_ig(dataframe, contaminant_list, loci, chromosome_list=default_chromosome_list,
               component_list=default_component_list):
    """
	This function takes an input dataframe (typically one generated by using the read_gtf function on a GTF of a
	reference organism's genome) and isolates all genes known to encode for IGs and contaminants based on the the
	desired immunoglobulin components and chromosomes specified by the user. It excludes pseudogenes
	and only includes exons.

	:param dataframe: An input dataframe of an organism's genome.
	:param chromosome_list: An input list of chromosomes on which immunoglobulin loci are expected to be found.
	Typically 2, 14, and 22 in humans, but may vary between organisms. List can be expanded or condensed at
	the discretion of the user.
	:param contaminant_list: An input list of known contaminant genes to be incorporated into the output dataframe.
	:param loci: An input dataframe of the overarching immunoglobulin loci on chromosomes 2, 14, and 22
	:param component_list: An input list of immunoglobulin components to search for (e.g. variable, constant, joining).
	The values in the list must match at least part of the string encoded under the "gene_biotype" column in the dataframe.
	For example, in the UCSC human genome GTF, IG Constant regions are listed as "IG_C_gene." If the user wanted to
	isolate constant regions only, it would be sufficient to pass the input as follows: component_list = ['IG_C'].

		Usage example: Suppose we want to isolate the variable and constant and joining IG regions from chromosomes
		2, 14, and 22 in the human genome. If our full genome dataframe is named "whole_genome", then we should
		call the function as follows:

		# Set up inputs
		desired_regions = ['IG_C', 'IG_V', 'IG_J']
		chromosomes = ['2', '14', '22']
		contaminant_list = ['GeneA', 'GeneB', etc] (this is provided in resource files)
		loci = read_gtf('IG_Loci.gtf') (this is provided in resource files)

		# Call function
		isolate_ig(whole_genome, contaminant_list, loci, chromosomes, desired_regions)

	Defaults: If no component list or chromosome list is provided, the function defaults to chromosomes 2, 14, and 22,
	and searches for IG_C and IG_V regions. Other inputs must be provided.

	:return: ig_dataframe: A smaller dataframe containing only desired IG regions and contaminants.
	"""
    # Convert dataframe to string format for ease of processing
    dataframe = dataframe.applymap(str)
    # Create a copy of the dataframe to search against the contaminant list.
    contaminant_dataframe = dataframe.applymap(str)
    # Isolate rows where the "gene_biotype" column starts with "IG_" and "feature" starts with "exon"
    dataframe = dataframe[dataframe['gene_biotype'].str.match('IG_') & dataframe['feature'].str.match('exon')]
    # Isolate all rows where "gene_biotype" DOES NOT contain "pseudogene"
    dataframe = dataframe[~dataframe.gene_biotype.str.contains("pseudogene")]
    # Isolate all rows where the gene biotype matches the desired regions (IG_C, IG_V, etc)
    dataframe = dataframe.loc[dataframe['gene_biotype'].str.contains('|'.join(component_list))]
    # Isolate all rows where the chromosome position is 2, 14, or 22
    ig_dataframe = dataframe.loc[dataframe['seqname'].str.contains('|'.join(chromosome_list))]

    # Isolate all rows of the dataframe where column 'gene_name' contains an element of contaminant_list
    # (a list of the gene names of known contaminants)
    contaminant_dataframe = contaminant_dataframe[contaminant_dataframe['gene_name'].isin(contaminant_list)]

    # Append the contaminant and loci dataframes to the IG dataframe to create one dataframe
    ig_dataframe = ig_dataframe.append(contaminant_dataframe).reset_index(drop=True)
    ig_dataframe = ig_dataframe.append(loci).reset_index(drop=True)

    # Most GTFs contain paralogs of certain IGs, designated with a 'D', for example, IGK1-23 is a paralog of IGK-23D.
    # These genes are similar enough that for our purposes they should be considered the same gene. This code isolates
    # all instances of D-designated paralogs, replaces their name with the non-D equivalent, and drops duplicates.

    # Isolate all D-designated paralogs into ig_dataframe2
    ig_dataframe2 = ig_dataframe[
        ig_dataframe['gene_name'].str.match('IGK') & ig_dataframe['gene_name'].str.contains('D') | ig_dataframe[
            'gene_name'].str.match('IGHV') & ig_dataframe['gene_name'].str.contains('D')]

    # Remove D from the gene names of paralogs. NOTE: This does remove all instances of 'D' in the gene name, but
    # it was confirmed that no instances of D besides paralog designators exist in IG gene names in the human GRCh38 GTF
    ig_dataframe2['gene_name'] = ig_dataframe2['gene_name'].str.replace('D', '')
    # Drop copies from existing dataframe and append ig_dataframe2
    ig_dataframe = ig_dataframe.drop(
        ig_dataframe[(ig_dataframe.gene_name.str.contains('D')) & (ig_dataframe.gene_name.str.match('IGK'))].index)
    ig_dataframe = ig_dataframe.drop(
        ig_dataframe[(ig_dataframe.gene_name.str.contains('D')) & (ig_dataframe.gene_name.str.match('IGHV'))].index)
    ig_dataframe = ig_dataframe.append(ig_dataframe2).reset_index(drop=True)


    return ig_dataframe


def interpret_featurecounts(filepath, resource_directory, samplename):
    """

	This function takes the output from featureCounts's operation on the input BAM and GTF files and creates
	several files, title.txt, Graph_IgH and Graph_IgL, which R uses to plot, as well as
	samplenamepurityCheckerresults.txt, a file containing the data for each sample in an easily-accessible text format.

	Unlike isolate_ig, this function has little utility on its own, so no usage example is provided. It is recommended
	that the user follow the format used later in the script, and not attempt to excise this function for separate use.
	It is unlikely to work independently without extensive re-writes.

	:param filepath: The directory in which the files built here will be deposited
	:param resource_directory: The directory from which the files used here will be sourced.
	:param samplename: The name of the sample.
	:return: No return, but several files will be written by the function.
	"""

    # Create dataframe called "reads" by importing the output from featurecounts. First row is skipped in the import
    # since it is just a header, second row is used to generate column labels. Tab-separated and new-line-terminated
    # are specified to ensure a proper read (the output dataframe will be one column or row if not specified)

    # filepath is used here instead of resource directory because featurecounts will write its output to the
    # directory specified by filepath
    reads = pd.read_csv(r'%s/%s.txt' % (filepath, samplename), sep='\t', lineterminator='\n',
                        skiprows=(0), header=(1))
    # Rename the column containing the counts to "Count". For whatever reason it comes labeled with the input file path.
    reads.rename(columns={reads.columns[6]: "Count"}, inplace=True)

    # Read in featurecounts's summary file
    summary = pd.read_csv(r'%s/%s.txt.summary' % (filepath, samplename), sep='\t',
                          lineterminator='\n', skiprows=(0), header=(0))
    # Rename the Count column, since it is given a long and unweildy name by default.
    summary.rename(columns={summary.columns[1]: "Count"}, inplace=True)

    # Create a new dataframe, "Condensed", containing data for Assigned reads and ignoring Unassigned reads EXCEPT
    # those unassigned because they did not map to anything included in the GTF. These represent Ig genes and Non-Ig
    # genes respectively, while the excluded data represents reads that map to more than one location, reads of too
    # poor quality to map, and other "noisy" data that should be excluded.
    condensed = summary[
        summary['Status'].str.contains('Assigned') | summary['Status'].str.contains('Unassigned_NoFeatures')]

    # Sum the "count" column of the condensed dataframe to generate the total number of verified reads (needed
    # to calculate RPKM).
    Featurecount_Total = condensed['Count'].sum()

    # Read in all text files containing the names of genes in specific loci (or known to be contaminants) as lists.
    Contaminant_List = open(r'%s/Non_Bcell_Contamination_GeneList_e98.txt' % resource_directory, 'r').read().split('\n')
    IGH_Variable_List = open(r'%s/IgH_Variable_Genes.txt' % resource_directory, 'r').read().split('\n')
    IGH_Constant_List = open(r'%s/IgH_Constant_Genes.txt' % resource_directory, 'r').read().split('\n')
    IGK_Variable_List = open(r'%s/IgK_Variable_Genes.txt' % resource_directory, 'r').read().split('\n')
    IGK_Constant_List = open(r'%s/IgK_Constant_Genes.txt' % resource_directory, 'r').read().split('\n')
    IGL_Variable_List = open(r'%s/IgL_Variable_Genes.txt' % resource_directory, 'r').read().split('\n')
    IGL_Constant_List = open(r'%s/IgL_Constant_Genes.txt' % resource_directory, 'r').read().split('\n')

    # Equivalent to featurecounts_counts post-processing

    # Drop the chromosome, start, end, and strand columns of the "reads" dataframe. Generate two new columns,
    # "Reads per base pair" (gene reads divided by gene length), and "RPKM" (reads per kilobase million), a measurement
    # equivalent to [(1,000,000)*(Number of Reads for a Gene)]/[(Gene Length in kb)*(Total Reads for the Sample)].
    # A multiplicative factor of one billion is used here instead of one million because featurecounts returns gene
    # length in base pairs, not kilobase pairs, and therefore the extra factor of one thousand is necessary.
    reads = pd.concat([reads['Geneid'], reads['Count'], reads['Length'], reads['Count'] / reads['Length'],
                       1000000000 * reads['Count'] / reads['Length'] / Featurecount_Total], axis=1)
    # Rename the new columns to "reads per bp" and "RPKM". When they are generated,
    # pandas labels them with numbers automatically.
    reads.rename(columns={reads.columns[3]: 'Reads per bp', reads.columns[4]: 'RPKM'}, inplace=True)

    # Calculate the geometric mean of the RPKM column for all identified genes known to be contaminants.

    # Geometric mean is equivalent to the **product** of n elements divided by n, as opposed to the more common
    # arithmetic mean, the **sum** of n elements divided by n.

    # Take the featurecounts output and isolate a dataframe containing only genes known to be
    # in the list of contaminants.
    geomeandf = reads[reads['Geneid'].isin(Contaminant_List)]
    # Add one to each element of the RPKM column. This is to avoid a multiply-by-zero situation when calculating
    # the geomean. At any instance of 0, the mean is instead multiplied by one, yielding the same result.
    # We assume adding 1 universally scales the geometric mean equivalently for all measurements.
    geomeandf['RPKM'] = geomeandf['RPKM'] + 1
    # Call scipy's gmean function on the RPKM column of the geomean dataframe to get the geometric mean.
    # It is rounded to two decimal places here for readability, but the user should feel free to choose any number.
    geomean = scipy.stats.gmean(geomeandf.loc[:, 'RPKM'], axis=0).round(2)

    # Equivalent to IGH_Variable_Counts, etc. in bash script

    # Create dataframes of genes specific to each locus by returning the subset of the complete dataframe where the gene
    # name (in column Geneid) is in one of the lists imported above.
    # The reset_index method is used again here since a column is added later, and if the indices are not consistent
    # between the two, the column will not be properly appended to the dataframe.
    IGHVdf = reads[reads['Geneid'].isin(IGH_Variable_List)].reset_index()
    IGHCdf = reads[reads['Geneid'].isin(IGH_Constant_List)].reset_index()
    IGKVdf = reads[reads['Geneid'].isin(IGK_Variable_List)].reset_index()
    IGKCdf = reads[reads['Geneid'].isin(IGK_Constant_List)].reset_index()
    IGLVdf = reads[reads['Geneid'].isin(IGL_Variable_List)].reset_index()
    IGLCdf = reads[reads['Geneid'].isin(IGL_Constant_List)].reset_index()
    Contaminantdf = reads[reads['Geneid'].isin(Contaminant_List)].reset_index()

    # Calculate the number of reads for each subset of genes by summing the
    # "Count" column of their respective dataframes.
    Total_IGHC_Reads = IGHCdf['Count'].sum()
    Total_IGHV_Reads = IGHVdf['Count'].sum()
    Total_IGKC_Reads = IGKCdf['Count'].sum()
    Total_IGKV_Reads = IGKVdf['Count'].sum()
    Total_IGLC_Reads = IGLCdf['Count'].sum()
    Total_IGLV_Reads = IGLVdf['Count'].sum()

    # Calculate the number of reads for the entire Heavy, Lambda, and Kappa loci. Since this information is included in
    # a single cell, and need not be generated by summing the counts of a subset of the data, the .str.contains and .at
    # methods are used, in place of the .isin and .sum methods used above. The reset_index method is necessary because
    # while there is only one row of data for each of these loci, its index may be arbitrary, and will be kept by pandas
    # by default, confusing the .at method. Forcing the index to 0 with the reset ensures that .at[0,'Count'] will work.
    Total_IGH = reads[reads['Geneid'].str.contains('HEAVY_Locus')].reset_index().at[0, 'Count']
    Total_IGK = reads[reads['Geneid'].str.contains('KAPPA_Locus')].reset_index().at[0, 'Count']
    Total_IGL = reads[reads['Geneid'].str.contains('LAMBDA_Locus')].reset_index().at[0, 'Count']

    # Generate several metrics used in later calculations using simple arithmetic on variables already produced.

    Total_IG = Total_IGH + Total_IGK + Total_IGL
    Percent_IG = Total_IG / Featurecount_Total
    Total_Light_Chain = Total_IGK + Total_IGL
    Total_Light_Variable = Total_IGKV_Reads + Total_IGLV_Reads
    Total_Light_Constant = Total_IGKC_Reads + Total_IGLC_Reads
    Percent_Kappa = Total_IGK / Total_Light_Chain
    Percent_Lambda = Total_IGL / Total_Light_Chain

    # About here, we officially transition to building the files that the R script wants

    # This function takes an IG subtype dataframe and returns a corresponding dataframe containing additional
    # information, such as frequency, which is used in R processing and retained as part of sample data
    def generate_calc_table(dataframe, group_total, label):
        labelseries = pd.Series([label] * len(dataframe.index))
        dataframe_Calc = pd.concat([dataframe['Geneid'], dataframe['Count'], dataframe['Count'] / group_total,
                                    dataframe['Count'] / Featurecount_Total, labelseries, dataframe['Length']], axis=1)
        dataframe_Calc.columns = ['Geneid', 'Count', 'List_Percent', 'Total_Percent', 'Subtype', 'Length']
        return dataframe_Calc

    # Call the above function on each dataframe to generate their corresponding Calc tables.
    IGHV_Calc = generate_calc_table(IGHVdf, Total_IGHV_Reads, 'IGHV')
    IGHC_Calc = generate_calc_table(IGHCdf, Total_IGHC_Reads, 'IGHC')
    IGKV_Calc = generate_calc_table(IGKVdf, Total_Light_Variable, 'IGKV')
    IGKC_Calc = generate_calc_table(IGKCdf, Total_Light_Constant, 'IGLC')
    IGLV_Calc = generate_calc_table(IGLVdf, Total_Light_Variable, 'IGLV')
    IGLC_Calc = generate_calc_table(IGLCdf, Total_Light_Constant, 'IGLC')

    # Concatenate above tables into two larger tables, the Heavy Chain table (IgH), and Light Chain Table (IgL)
    # Ignore previous index and rename columns (three are labeled 'Count' at this point due to their origin as
    # columns computed from the initial 'Count' column in generate_calc_table)
    Graph_IgL = pd.concat([IGKC_Calc, IGKV_Calc, IGLC_Calc, IGLV_Calc]).reset_index().drop(columns='index')
    Graph_IgL.columns = ['CommonName', 'Count', 'Percentage', 'TotalFrequency', 'Locus', 'ElementSize']
    Graph_IgH = pd.concat([IGHC_Calc, IGHV_Calc]).reset_index().drop(columns='index')
    Graph_IgH.columns = ['CommonName', 'Count', 'Percentage', 'TotalFrequency', 'Locus', 'ElementSize']

    # Write these tables to a tab-delimited text file. R will use these files to plot
    Graph_IgH.to_csv(r'%s/%sGraph_IgH.txt' % (filepath, samplename), sep='\t', float_format='%.12f',
                     index=False)
    Graph_IgL.to_csv(r'%s/%sGraph_IgL.txt' % (filepath, samplename), sep='\t', float_format='%.12f',
                     index=False)

    # This function returns a list of primary information from the input dataframe, e.g. when given IGHC_Calc, etc.
    # it will extract the two most-read genes, their frequencies, and the difference between their frequencies.
    def get_Primary(dataframe):
        Primary = dataframe.sort_values(by='Count', ascending=False).reset_index().at[0, 'Geneid']
        PrimaryFreq = dataframe.sort_values(by='Count', ascending=False).reset_index().at[0, 'List_Percent']
        Secondary = dataframe.sort_values(by='Count', ascending=False).reset_index().at[1, 'Geneid']
        SecondaryFreq = dataframe.sort_values(by='Count', ascending=False).reset_index().at[1, 'List_Percent']
        Delta = PrimaryFreq - SecondaryFreq
        return pd.Series([Primary, PrimaryFreq, Secondary, SecondaryFreq, Delta])

    # Concatenate the light constants and light variables into one dataframe each. This is done since there should
    # never be an instance when lambda and kappa light chains are both simultaneously present in a sample in
    # appreciable quantities, therefore only the top two constant and variable light
    # genes on either light locus are needed.
    IG_light_constant = IGKC_Calc.append(IGLC_Calc).reset_index().drop(columns='index')
    IG_light_variable = IGKV_Calc.append(IGLV_Calc).reset_index().drop(columns='index')

    # Call get_Primary on the relevant dataframes
    primaryIGHC = get_Primary(IGHC_Calc)
    primaryIGHV = get_Primary(IGHV_Calc)
    primaryIGLC = get_Primary(IG_light_constant)
    primaryIGLV = get_Primary(IG_light_variable)

    # The code below isolates the overall top two genes from the sample and their difference in frequency.
    # This information is included in the final plots.
    Topframe = pd.concat([primaryIGHC, primaryIGHV, primaryIGLC, primaryIGLV], axis=1).transpose()
    Topframe.insert(0, 'Locus', ['IGHC', 'IGHV', 'IGLC', 'IGLV'], allow_duplicates=False)
    Topframe.columns = ['Locus', 'Primary', 'PrimaryFreq', 'Secondary', 'SecondaryFreq', 'Delta']

    Top1 = Topframe.sort_values(by='PrimaryFreq', ascending=False).reset_index().drop(columns='index').at[
        0, 'PrimaryFreq']
    Top2 = Topframe.sort_values(by='PrimaryFreq', ascending=False).reset_index().drop(columns='index').at[
        1, 'PrimaryFreq']
    Top1_Delta = Topframe.sort_values(by='PrimaryFreq', ascending=False).reset_index().drop(columns='index').at[
        0, 'Delta']
    Top2_Delta = Topframe.sort_values(by='PrimaryFreq', ascending=False).reset_index().drop(columns='index').at[
        1, 'Delta']

    IgHResults = Graph_IgH
    IgLResults = Graph_IgL

    CompleteIgResults = IgHResults.append(IgLResults)
    VariableIgResults = CompleteIgResults[CompleteIgResults['Locus'].str.contains('V')]

    # Introduce initial condition for the clonality of the sample
    Monoclonal = False
    Polyclonal = False
    Biclonal = False
    LightChainOnly = False
    ManualReview = True

    # This block decides which "bucket" the sample falls into

    # Case where exactly at least 3 lines are above 85% of their respective groups and if three,
    # the smallest one is at least 75% (highly monoclonal)
    if len(CompleteIgResults[(CompleteIgResults['Percentage'] > 0.85)].index) >= 3 and \
            len(CompleteIgResults[(CompleteIgResults['Percentage'] > 0.75)].index) == 4:

        Monoclonal = True
        ManualReview = not ManualReview

    # All non-monoclonal cases
    else:
        # Case where exactly two light chains are above 75% (hallmark of light chain only)
        if len(IgLResults[(IgLResults['Percentage'] > 0.75)].index) == 2:
            # Case where, in addition to above, no heavy chains contribute > 0.001 total frequency (another hallmark of LCO)
            if len(IgHResults[(IgHResults['TotalFrequency'] > 0.001)].index) == 0:

                LightChainOnly = True
                ManualReview = not ManualReview

            # Case where there are exactly two prominent light chains but moderate heavy chain presence. If this stage
            # is reached, either something has gone wrong, or the heavy chain data is poor/corrupted. In either case,
            # manual review is necessary.
            else:

                ManualReview = True

        # Case where there are neither 4 chains above 85% nor exactly two light chains above 75%
        # (biclonal or polyclonal cases)
        else:
            # Case where, across the whole data set, between 6-8 bars are between 35% - 65% of their groups.
            # This is a hallmark of biclonality and is rare, but does sometimes occur.
            if len(CompleteIgResults[(CompleteIgResults['Percentage'] >= 0.35) & (
                    CompleteIgResults['Percentage'] <= 0.65)].index) >= 6 \
                    and len(CompleteIgResults[(CompleteIgResults['Percentage'] >= 0.35) & (
                    CompleteIgResults['Percentage'] <= 0.65)].index) <= 8:

                Biclonal = True
                ManualReview = not ManualReview

            # Cases where none of the conditions above are met, which leaves polyclonality or manual review required
            else:

                # Case where No variable genes make up more than 20% of the sample (a hallmark of polyclonality)
                if len(VariableIgResults[(VariableIgResults['Percentage'] > 0.20)].index) == 0:
                    Polyclonal = True
                    ManualReview = not ManualReview

                # If the above is not true, manual review is required
                else:

                    ManualReview = True

    # This block assigns clonality to the output, double checking that not more than one case is true. Such cases
    # should not theoretically be possible given the above logic, but in the eventuality an extremely unusual data set exploited
    # an unforseen edge case, manual review will automatically be invoked.

    if Monoclonal is True and Polyclonal is False and Biclonal is False and LightChainOnly is False and ManualReview is False:

        clonality = 'Likely Monoclonal'

    elif Polyclonal is True and Monoclonal is False and Biclonal is False and LightChainOnly is False and ManualReview is False:

        clonality = 'Likely Polyclonal'

    elif Biclonal is True and Monoclonal is False and Polyclonal is False and LightChainOnly is False and ManualReview is False:

        clonality = 'Likely Biclonal'

    elif LightChainOnly is True and Monoclonal is False and Polyclonal is False and Biclonal is False and ManualReview is False:

        clonality = 'Likely Light Chain Only'

    else:

        clonality = 'Manual Review Required'

    # This code generates a tab-separated text file containing the important results from the data in one row and
    # labels for each piece of data in a row above.

    # This list contains each of the labels.
    label_list = ["Sample", "PrimaryIgHC", "PrimaryIgHC_Freq", "SecondaryIgHC", "DeltaIgHC", "PrimaryIgHV",
                  "PrimaryIgHV_Freq", "SecondaryIgHV", "DeltaIgHV", "PrimaryIgLC", "PrimaryIgLC_Freq", "SecondaryIgLC",
                  "DeltaIgLC", "PrimaryIgLV", "PrimaryIgLV_Freq", "SecondaryIgLV", "DeltaIgLV", "TOTAL_IGHC_READS",
                  "TOTAL_IGHV_READS", "TOTAL_IGKC_READS", "TOTAL_IGKV_READS", "TOTAL_IGLC_READS", "TOTAL_IGLV_READS",
                  "TOTAL_IGH", "TOTAL_IGK", "TOTAL_IGL", "TOTAL_IG", "PERCENT_IG", "TOTAL_LIGHT_CHAIN",
                  "TOTAL_LIGHT_VARIABLE", "TOTAL_LIGHT_CONSTANT", "PERCENT_KAPPA", "PERCENT_LAMBDA", "Top1", "Top2",
                  "Mean_Top_Delta", "NonB_Contamination", "Clonality"]
    # This list contains each of the corresponding variables converted to strings so they can be written to text.

    results_list = ["%s" % samplename, str(primaryIGHC[0]), str(primaryIGHC[1]), str(primaryIGHC[2]),
                    str(primaryIGHC[4]),
                    str(primaryIGHV[0]), str(primaryIGHV[1]), str(primaryIGHV[2]), str(primaryIGHV[4]),
                    str(primaryIGLC[0]), str(primaryIGLC[1]), str(primaryIGLC[2]), str(primaryIGLC[4]),
                    str(primaryIGLV[0]), str(primaryIGLV[1]), str(primaryIGLV[2]), str(primaryIGLV[4]),
                    str(Total_IGHC_Reads), str(Total_IGHV_Reads), str(Total_IGKC_Reads), str(Total_IGKV_Reads),
                    str(Total_IGLC_Reads), str(Total_IGLV_Reads), str(Total_IGH), str(Total_IGK), str(Total_IGL),
                    str(Total_IG), str(Percent_IG), str(Total_Light_Chain), str(Total_Light_Variable),
                    str(Total_Light_Constant), str(Percent_Kappa), str(Percent_Lambda), str(Top1), str(Top2),
                    str((Top1_Delta + Top2_Delta) / 2), str(geomean), clonality]

    # This block of code opens a new text file, writes the first list into the file tab-separated, then writes
    # a new line, and does the same for the list of results.
    resultstextfile = open(r"%s/%spurityCheckerResults.txt" % (filepath, samplename), "w")
    for element in label_list:
        resultstextfile.write(element + "\t")
    resultstextfile.write("\n")
    for element in results_list:
        resultstextfile.write(element + "\t")
    resultstextfile.close()

    titletextfile = open(r"%s/%stitle.txt" % (filepath, samplename), "w")
    titletextfile.write("Percent Ig = %s ; Kappa/(K+L) = %s ; Lambda/(K+L) = %s ; Non B Contamination = %s"
                        % (str(round(Percent_IG, 4)), str(round(Percent_Kappa, 4)), str(round(Percent_Lambda, 4)),
                           str(geomean)))
    titletextfile.close()


# !!!!! THIS HAS BEEN COPIED FROM AGEPy!

def writeGTF(inGTF, file_path):
    """
    Write a GTF dataframe into a file
    :param inGTF: GTF dataframe to be written. It should either have 9 columns with the last one being the "attributes"
    section or more than 9 columns where all columns after the 8th will be colapsed into one.
    :param file_path: path/to/the/file.gtf
    :returns: nothing
    """
    # This block collapses all columns after 8 into the GTF's signature semicolon-separated ninth column. Additional
    # code was provided by me to handle the edge case where the score column's '.' are imported as nan, and to
    # write the GTF without use of Python's csv library. Code not otherwise specified was copied from AGEPy's GitHub

    inGTF['score'] = inGTF['score'].str.replace('nan', '.')
    cols = inGTF.columns.tolist()
    if len(cols) == 9:
        if 'attribute' in cols:
            df = inGTF
    else:
        df = inGTF[cols[:8]]
        df['attribute'] = ""
        for c in cols[8:]:
            if c == cols[len(cols) - 1]:
                df['attribute'] = df['attribute'] + c + ' "' + inGTF[c].astype(str) + '";'
            else:
                df['attribute'] = df['attribute'] + c + ' "' + inGTF[c].astype(str) + '"; '

    # This line was added to handle an unresolved pandas bug where to_csv alphabetizes columns in the csv under
    # certain conditions. While this code does nothing to change the dataframe, the output columns will be
    # alphabetized if we do not specify their order here.

    df2 = df[['seqname', 'source', 'feature', 'start', 'end', 'score', 'strand', 'frame', 'attribute']]
    df2.to_csv(r'%s.csv' % file_path, index=False)

    print('CSV Written')
    # This block of code converts the CSV to a GTF by taking each column, writing in as a string, inserting a tab, and
    # starting a new line after the ninth column. (even though it says [8], its a 0-index, which is confusing but still)
    # The text file will be saved in the specified file path. It WILL NOT overwrite files with the same name.
    print('Converting to GTF')
    data = pd.read_csv(r'%s.csv' % file_path, encoding='utf-8')
    with open(r'%s.gtf' % file_path, 'a+', encoding='utf-8') as f:
        for line in data.values:
            f.write((str(line[0]) + '\t' + str(line[1]) + '\t' + str(line[2]) + '\t' + str(line[3]) + '\t' + str(
                line[4]) + '\t' + str(line[5]) + '\t' + str(line[6]) + '\t' + str(line[7]) + '\t' + str(
                line[8]) + '\n'))
    print('GTF conversion complete')


# ------------------------------------------------------------------------------------------------------------------- #
# CODE THAT ACTUALLY RUNS THINGS
# ------------------------------------------------------------------------------------------------------------------- #

in_bam = read_aln_file(input_aln, threads, out_path, reference_genome_fasta=ref_fasta)

# Case where user wants to build an IG GTF from a different GTF than provided. In this case, the program builds
# the GTF and then processes the input BAM using the new GTF
if in_gtf is not None and build is True:
    call("echo 'Starting file build'", shell=True)
    call("echo 'Opening GTF'", shell=True)
    gtf_to_build = open(r'%s' % in_gtf, 'r')

    call("echo 'GTF opened, converting to dataframe'", shell=True)
    df = read_gtf(gtf_to_build)
    call("echo 'Conversion successful'", shell=True)

    call("echo 'Opening Loci'", shell=True)
    loci_gtf = open(r'%s/Immunoglobulin_GRCh38_Loci.gtf' % resource_directory, 'r')

    call("echo 'Loci opened, converting to dataframe'", shell=True)
    loci = read_gtf(loci_gtf)
    call("echo 'Conversion successful'", shell=True)

    call("echo 'Fetching contaminant list'", shell=True)
    contaminant_file = open(r'%s/Non_Bcell_Contamination_GeneList_e98.txt' % resource_directory, 'r')
    contaminant_list = contaminant_file.read().split('\n')
    call("echo 'Contaminant list found'", shell=True)

    call("echo 'Isolating IG regions'", shell=True)
    ig_dataframe = isolate_ig(df, contaminant_list, loci)
    call("echo 'Isolation Successful'", shell=True)
    # Call the to_gtf function on the specified file.

    call("echo 'Converting isolated dataframe to GTF'", shell=True)
    writeGTF(ig_dataframe, r'%s/%s' % (out_path, samplename))

    call("echo 'Conversion successful'", shell=True)

    if build_only == True:
        if keep_temp is False:
            os.remove(r'%s/%s.csv' % (out_path, samplename))
        sys.exit(0)

    # Direct shell to scratch for universal usage capabilities
    call("%s -g gene_name -O -s 0 -Q 10 -T %s -C -p -a %s/%s.gtf -o %s/"
         "%s.txt %s" % (featurecounts_path, threads, out_path, samplename, out_path, samplename, in_bam), shell=True)

# Case where the user wants to build a new GTF but no starting GTF is provided. In this case, an error is thrown, since
# there will be nothing to build from
elif in_gtf is None and build is True:

    sys.exit('ERROR: To build files an input GTF must be provided.')

# Case where a GTF is provided but the build command is not called. In this case, it is assumed the user wants to supply
# a custom GTF to featureCounts, and featureCounts is called using the supplied BAM and GTF. The user should note that
# ensuring the GTF cooperates with the rest of the program and their goals is their responsibility.
elif in_gtf is not None and build is False:

    # Run featurecounts from the shell
    call("%s -g gene_name -O -s 0 -Q 10 -T %s -C -p -a %s -o %s/"
         "%s.txt %s" % (featurecounts_path, threads, in_gtf, out_path, samplename, in_bam), shell=True)

# Case where no inputs except BAM are given and the build command is not called. In this case, it is assumed that the
# user wants to use the default GTF provided with the script.
else:

    # Run featurecounts from the shell
    #try:
        #call("featureCounts -g gene_name -O -s 0 -Q 10 -T %s -C -p -a %s/%s.gtf -o %s/"
             #"%s.txt %s" % (threads, resource_directory, default_gtf, out_path, samplename, in_bam),
             #shell=True)
    #except:
        #print('EXCEPT STATEMENT EXECUTED')
    call("%s -g gene_name -O -s 0 -Q 10 -T %s -C -p -a %s/%s.gtf -o %s/"
        "%s.txt %s" % (featurecounts_path, threads, resource_directory, default_gtf, out_path, samplename, in_bam),
        shell=True)

# Run the interpret_featurecounts function on featureCounts's output
interpret_featurecounts('%s' % out_path, '%s' % resource_directory, '%s' % samplename)

# Call the R script to produce the visual outputs
call('R <%s/igh_graph.R --no-save %s %s %s' % (resource_directory, resource_directory, out_path, samplename),
     shell=True)

# Remove temporary files if desired
if keep_temp is True:
    pass
elif keep_temp is False and build is True:
    if os.path.splitext(input_aln)[1] == ".cram":
        os.remove(r'%s/%s.bam' % (out_path, samplename))
        os.remove(r'%s/%s.bam.bai' % (out_path, samplename))
    os.remove(r'%s/%sGraph_IgH.txt' % (out_path, samplename))
    os.remove(r'%s/%sGraph_IgL.txt' % (out_path, samplename))
    os.remove(r'%s/%stitle.txt' % (out_path, samplename))
    os.remove(r'%s/%s.csv' % (out_path, samplename))
else:
    if os.path.splitext(input_aln)[1] == ".cram":
        os.remove(r'%s/%s.bam' % (out_path, samplename))
        os.remove(r'%s/%s.bam.bai' % (out_path, samplename))
    os.remove(r'%s/%sGraph_IgH.txt' % (out_path, samplename))
    os.remove(r'%s/%sGraph_IgL.txt' % (out_path, samplename))
    os.remove(r'%s/%stitle.txt' % (out_path, samplename))

sys.exit(0)

