#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import os
import scipy
from gtfparse import read_gtf
from subprocess import call
from scipy import stats

# shell=True is so you can handle redirects
call("echo 'Running'", shell=True)
 #quit()

# Argument parser to facilitate calling from the command line

parser = argparse.ArgumentParser(description='Check purity of multiple myeloma tumor samples.')
parser.add_argument('-i', '--input_bam',
                    required=True,
                    help='BAM file for tumor sample')
parser.add_argument('-g', '--input_gtf',
                    help='GTF to be used in processing')
parser.add_argument('-o', '--output_path',
                    required=True,
                    help='Output path')
parser.add_argument('-b', '--build_files',
                    help='Type Y if you want to build the GTF, leave blank otherwise')

args = parser.parse_args()

out_path = args.output_path
in_gtf = args.input_gtf
in_bam = args.input_bam
build = args.build_files



# ------------------------------------------------------------------------------------------------------------------- #
# FUNCTIONS THAT SUPPORT CODE AT BOTTOM
# ------------------------------------------------------------------------------------------------------------------- #

# TODO: this function is putting nan in the score column instead of replacing it. Not fatal, but need to fix.
def to_gtf(dataframe, filepath):
    """
    Function converts a python dataframe into a GTF (Gene Transfer Format) file.
    !!!NOTE: This function is designed to be used on dataframes that were generated
    from existing GTF files using the "read_gtf" function from PyPI's gtfparse
    Python library, found here: <https://pypi.org/project/gtfparse/>. It is
    unlikely to work with other dataframes.

    :param dataframe: A dataframe generated from an existing GTF file.
    :param filepath: The location where the file should be written, including name, but EXCLUDING extension
    (the function takes care of that). It should be written as a raw string to prevent unicode escape errors.
    For example, if you want to write to /Users/myname/Desktop, name the file "example.gtf", and your dataframe is
    called "df", you should call the function as follows:
                        to_gtf(df, '/Users/myname/Desktop/example')

    :return: No true return, but it will place the output GTF file in the specified file path.
    """
    print('Converting dataframe to GTF')
    # Replace any NaN values generated by read_gtf. By default, read_gtf creates a dataframe
    # with 26 columns, each corresponding to one piece of possible information that could be included in a GTF, without
    # respect to whether that information is present. If not present, the cell is filled with NaN. NaN must be
    # replaced with a unique string (see immediately below) for later processing.

    dataframe = dataframe.replace(np.nan, 'YOUMUSTREPLACETHISSTRING', regex=True)

    # Convert all data in the dataframe to string format. By default, data is brought into the dataframe
    # as float, int, or string, depending on what would be "normal." It must be converted to string format
    # for later combination of columns.
    dataframe = dataframe.applymap(str)

    # Repeat the same procedure as above with NaN, but look for empty cells instead of cells marked NaN. Depending
    # on Python version or IDE, either or both may occur, so this covers that eventuality.
    dataframe = dataframe.replace('', 'YOUMUSTREPLACETHISSTRING', regex=True)

    # This ugly block of code puts the title of each column in front of the cell data and adds quotes and
    # semicolons to be consistent with the GTF format. For example, if in the gene_id column we have:
    #
    #   [gene_id]                                                       [gene_id]
    #   [ABC123]           ----- it converts to ---->                   [gene_id "ABC123"; ]
    #   [DEF456]                                                        [gene_id "DEF456"; ]
    #   etc

    dataframe['gene_id'] = 'gene_id "' + dataframe['gene_id'].astype(str) + '"; '
    dataframe['gene_version'] = 'gene_version "' + dataframe['gene_version'].astype(str) + '"; '
    dataframe['gene_name'] = 'gene_name "' + dataframe['gene_name'].astype(str) + '"; '
    dataframe['gene_source'] = 'gene_source "' + dataframe['gene_source'].astype(str) + '"; '
    dataframe['gene_biotype'] = 'gene_biotype "' + dataframe['gene_biotype'].astype(str) + '"; '
    dataframe['transcript_id'] = 'transcript_id "' + dataframe['transcript_id'].astype(str) + '"; '
    dataframe['transcript_version'] = 'transcript_version "' + dataframe['transcript_version'].astype(str) + '"; '
    dataframe['transcript_name'] = 'transcript_name "' + dataframe['transcript_name'].astype(str) + '"; '
    dataframe['transcript_source'] = 'transcript_source "' + dataframe['transcript_source'].astype(str) + '"; '
    dataframe['transcript_biotype'] = 'transcript_biotype "' + dataframe['transcript_biotype'].astype(str) + '"; '
    dataframe['tag'] = 'tag "' + dataframe['tag'].astype(str) + '"; '
    dataframe['transcript_support_level'] = 'transcript_support_level "' + dataframe['transcript_support_level'].astype(
        str) + '"; '
    dataframe['exon_number'] = 'exon_number "' + dataframe['exon_number'].astype(str) + '"; '
    dataframe['exon_id'] = 'exon_id "' + dataframe['exon_id'].astype(str) + '"; '
    dataframe['exon_version'] = 'exon_version "' + dataframe['exon_version'].astype(str) + '"; '
    dataframe['ccds_id'] = 'ccds_id "' + dataframe['ccds_id'].astype(str) + '"; '
    dataframe['protein_id'] = 'protein_id "' + dataframe['protein_id'].astype(str) + '"; '
    dataframe['protein_version'] = 'protein_version "' + dataframe['protein_version'].astype(str) + '"; '

    # This next ugly block of code removes all data from any cell containing the string
    # "YOUMUSTREPLACETHISSTRING", and replaces it with a null string. Recognize that we added this string
    # earlier to all cells which contained NaN/were empty. Now these cells contain something like
    # [gene_id "YOUMUSTREPLACETHISSTRING"; ], which is obviously nonsense that we don't want in our final file.
    # After we remove those entries, we can simply merge the last 16 columns into the semicolon-delineated column 9
    # that is used in a GTF. A notable exception is the "score" column (at the bottom), in which "score" is usually
    # kept as a period if no value is present.

    dataframe.loc[dataframe['gene_id'].str.contains('YOUMUSTREPLACETHISSTRING'), 'gene_id'] = ''
    dataframe.loc[dataframe['gene_version'].str.contains('YOUMUSTREPLACETHISSTRING'), 'gene_version'] = ''
    dataframe.loc[dataframe['gene_name'].str.contains('YOUMUSTREPLACETHISSTRING'), 'gene_name'] = ''
    dataframe.loc[dataframe['gene_source'].str.contains('YOUMUSTREPLACETHISSTRING'), 'gene_source'] = ''
    dataframe.loc[dataframe['gene_biotype'].str.contains('YOUMUSTREPLACETHISSTRING'), 'gene_biotype'] = ''
    dataframe.loc[dataframe['transcript_id'].str.contains('YOUMUSTREPLACETHISSTRING'), 'transcript_id'] = ''
    dataframe.loc[dataframe['transcript_version'].str.contains('YOUMUSTREPLACETHISSTRING'), 'transcript_version'] = ''
    dataframe.loc[dataframe['transcript_name'].str.contains('YOUMUSTREPLACETHISSTRING'), 'transcript_name'] = ''
    dataframe.loc[dataframe['transcript_source'].str.contains('YOUMUSTREPLACETHISSTRING'), 'transcript_source'] = ''
    dataframe.loc[dataframe['transcript_biotype'].str.contains('YOUMUSTREPLACETHISSTRING'), 'transcript_biotype'] = ''
    dataframe.loc[dataframe['tag'].str.contains('YOUMUSTREPLACETHISSTRING'), 'tag'] = ''
    dataframe.loc[
        dataframe['transcript_support_level'].str.contains('YOUMUSTREPLACETHISSTRING'), 'transcript_support_level'] = ''
    dataframe.loc[dataframe['exon_number'].str.contains('YOUMUSTREPLACETHISSTRING'), 'exon_number'] = ''
    dataframe.loc[dataframe['exon_id'].str.contains('YOUMUSTREPLACETHISSTRING'), 'exon_id'] = ''
    dataframe.loc[dataframe['exon_version'].str.contains('YOUMUSTREPLACETHISSTRING'), 'exon_version'] = ''
    dataframe.loc[dataframe['ccds_id'].str.contains('YOUMUSTREPLACETHISSTRING'), 'ccds_id'] = ''
    dataframe.loc[dataframe['protein_id'].str.contains('YOUMUSTREPLACETHISSTRING'), 'protein_id'] = ''
    dataframe.loc[dataframe['protein_version'].str.contains('YOUMUSTREPLACETHISSTRING'), 'protein_version'] = ''
    dataframe.loc[dataframe['score'].str.contains('YOUMUSTREPLACETHISSTRING'), 'score'] = '.'

    # Combine all normally semicolon-delineated data into one column

    dataframe['Combined_Column'] = dataframe['gene_id'] + dataframe['gene_version'] + dataframe['gene_name'] + \
                                   dataframe['gene_source'] + dataframe['gene_biotype'] + dataframe['transcript_id'] + \
                                   dataframe['transcript_version'] + dataframe['transcript_name'] + dataframe[
                                       'transcript_source'] + \
                                   dataframe['transcript_biotype'] + dataframe['tag'] + dataframe[
                                       'transcript_support_level'] + \
                                   dataframe['exon_number'] + dataframe['exon_id'] + dataframe['exon_version'] + \
                                   dataframe['ccds_id'] + dataframe['protein_id'] + dataframe['protein_version']

    # Drop all columns that were just combined (since all their data has been duplicated into Combined_Column
    dataframe = dataframe.drop(
        dataframe.columns[[8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]], axis=1)
    print('Writing CSV')
    # Send the edited dataframe to a CSV file in the desired filepath. The code below (data = ...) converts the CSV to
    # tab-separated text and saves as a GTF in the desired filepath.
    dataframe.to_csv(r'%s.csv' % filepath, index=False)
    print('CSV Written')
    # This block of code converts the CSV to a GTF by taking each column, writing in as a string, inserting a tab, and
    # starting a new line after the ninth column. (even though it says [8], its a 0-index, which is confusing but still)
    # The text file will be saved in the specified file path. It WILL NOT overwrite files with the same name.
    print('Converting to GTF')
    data = pd.read_csv(r'%s.csv' % filepath, encoding='utf-8')
    with open(r'%s.gtf' % filepath, 'a+', encoding='utf-8') as f:
        for line in data.values:
            f.write((str(line[0]) + '\t' + str(line[1]) + '\t' + str(line[2]) + '\t' + str(line[3]) + '\t' + str(
                line[4]) + '\t' + str(line[5]) + '\t' + str(line[6]) + '\t' + str(line[7]) + '\t' + str(
                line[8]) + '\n'))
    print('GTF conversion complete')
    # This removes the CSV that was made earlier, since it's only necessary to write the GTF. If you want to keep the
    # CSV, feel free to disable/delete this line.
    print('Removing CSV')
    os.remove(r'%s.csv' % filepath)
    print('CSV Removed')
# TODO: gtf builder is not including contaminants or loci, need to fix (this one is fatal)

def isolate_ig(dataframe, chromosome_list=['2', '14', '22'], component_list=['IG_V', 'IG_C']):
    """
    This function takes an input dataframe (typically one generated by using the read_gtf function on a GTF of a
    reference organism's genome) and isolates all genes known to encode for IGs based on the the desired
    immunoglobulin components and chromosomes specified by the user. It excludes pseudogenes and only includes exons.

    :param dataframe: An input dataframe of an organism's genome.
    :param chromosome_list: An input list of chromosomes on which immunoglobulin loci are expected to be found.
    Typically 2, 14, and 22 in humans, but may vary between organisms. List can be expanded or condensed at
    the discretion of the user.
    :param component_list: An input list of immunoglobulin components to search for (e.g. variable, constant, joining).
    The values in the list must match at least part of the string encoded under the "gene_biotype" column in the dataframe.
    For example, in the UCSC human genome GTF, IG Constant regions are listed as "IG_C_gene." If the user wanted to
    isolate constant regions only, it would be sufficient to pass the input as follows: component_list = ['IG_C'].

        Usage example: Suppose we want to isolate the variable and constant and joining IG regions from chromosomes
        2, 14, and 22 in the human genome. If our full genome dataframe is named "whole_genome", then we should
        call the function as follows:

        desired_regions = ['IG_C', 'IG_V', 'IG_J']
        chromosomes = ['2', '14', '22']
        isolate_ig(whole_genome, chromosomes, desired_regions)

    Defaults: If no component list or chromosome list is provided, the function defaults to chromosomes 2, 14, and 22,
    and searches for IG_C and IG_V regions. An input dataframe must be provided.

    :return: ig_dataframe: A smaller dataframe containing only desired IG regions.
    """
    # Convert dataframe to string format for ease of processing
    dataframe = dataframe.applymap(str)
    # Isolate rows where the "gene_biotype" column starts with "IG_" and "feature" starts with "exon"
    dataframe = dataframe[dataframe['gene_biotype'].str.match('IG_') & dataframe['feature'].str.match('exon')]
    # Isolate all rows where "gene_biotype" DOES NOT contain "pseudogene"
    dataframe = dataframe[~dataframe.gene_biotype.str.contains("pseudogene")]
    # Isolate all rows where the gene biotype matches the desired regions (IG_C, IG_V, etc)
    dataframe = dataframe.loc[dataframe['gene_biotype'].str.contains('|'.join(component_list))]
    # Isolate all rows where the chromosome position is 2, 14, or 22
    ig_dataframe = dataframe.loc[dataframe['seqname'].str.contains('|'.join(chromosome_list))]

    return ig_dataframe


def interpret_featurecounts(filepath, samplename):
    '''

    :param filepath: The directory in which the files built here will be deposited, and the files used here will
    be sourced from.
    :param samplename:
    :return:
    '''

    # equivalent to temp_featurecounts_counts in bash script

    # Create dataframe called "reads" by importing the output from featurecounts. First row is skipped in the import
    # since it is just a header, second row is used to generate column labels. Tab-separated and new-line-terminated
    # are specified to ensure a proper read (the output dataframe will be one column or row if not specified)
    reads = pd.read_csv(r'%s/temp_featureCounts_Counts_BERT_TEST.txt' % filepath, sep='\t', lineterminator='\n',
                        skiprows=(0), header=(1))
    # Rename the column containing the counts to "Count". For whatever reason it comes labeled with the input file path.
    reads.rename(columns={reads.columns[6]: "Count"}, inplace=True)

    # Read in featurecounts's summary file
    summary = pd.read_csv(r'%s/temp_featureCounts_Counts_BERT_TEST.txt.summary' % filepath, sep='\t',
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
    Contaminant_List = open(r'%s/Non_Bcell_Contamination_GeneList_e98.txt' % filepath, 'r').read().split(
        '\n')
    IGH_Variable_List = open(r'%s/IgH_Variable_Genes.txt' % filepath, 'r').read().split('\n')
    IGH_Constant_List = open(r'%s/IgH_Constant_Genes.txt' % filepath, 'r').read().split('\n')
    IGK_Variable_List = open(r'%s/IgK_Variable_Genes.txt' % filepath, 'r').read().split('\n')
    IGK_Constant_List = open(r'%s/IgK_Constant_Genes.txt' % filepath, 'r').read().split('\n')
    IGL_Variable_List = open(r'%s/IgL_Variable_Genes.txt' % filepath, 'r').read().split('\n')
    IGL_Constant_List = open(r'%s/IgL_Constant_Genes.txt' % filepath, 'r').read().split('\n')

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
    global Total_IG
    Total_IG = Total_IGH + Total_IGK + Total_IGL
    global Percent_IG
    Percent_IG = Total_IG / Featurecount_Total
    global Total_Light_Chain
    Total_Light_Chain = Total_IGK + Total_IGL
    global Total_Light_Variable
    Total_Light_Variable = Total_IGKV_Reads + Total_IGLV_Reads
    global Total_Light_Constant
    Total_Light_Constant = Total_IGKC_Reads + Total_IGLC_Reads
    global Percent_Kappa
    Percent_Kappa = Total_IGK / Total_Light_Chain
    global Percent_Lambda
    Percent_Lambda = Total_IGL / Total_Light_Chain


    #####################################
    # About here, we officially transition to building the files that the R script wants
    #####################################

    def generate_calc_table(dataframe, group_total, label):
        labelseries = pd.Series([label] * len(dataframe.index))
        dataframe_Calc = pd.concat([dataframe['Geneid'], dataframe['Count'], dataframe['Count'] / group_total,
                                    dataframe['Count'] / Featurecount_Total, labelseries, dataframe['Length']], axis=1)
        dataframe_Calc.columns = ['Geneid', 'Count', 'List_Percent', 'Total_Percent', 'Subtype', 'Length']
        return dataframe_Calc

    IGHV_Calc = generate_calc_table(IGHVdf, Total_IGHV_Reads, 'IGHV')
    IGHC_Calc = generate_calc_table(IGHCdf, Total_IGHC_Reads, 'IGHC')
    IGKV_Calc = generate_calc_table(IGKVdf, Total_Light_Variable, 'IGKV')
    IGKC_Calc = generate_calc_table(IGKCdf, Total_Light_Constant, 'IGKC')
    IGLV_Calc = generate_calc_table(IGLVdf, Total_Light_Variable, 'IGLV')
    IGLC_Calc = generate_calc_table(IGLCdf, Total_Light_Constant, 'IGLC')

    Graph_IgL = pd.concat([IGKC_Calc, IGKV_Calc, IGLC_Calc, IGLV_Calc]).reset_index().drop(columns = 'index')
    Graph_IgL.columns = ['CommonName', 'Count', 'Percentage', 'TotalFrequency', 'Locus', 'ElementSize']
    Graph_IgH = pd.concat([IGHC_Calc, IGHV_Calc]).reset_index().drop(columns = 'index')
    Graph_IgH.columns = ['CommonName', 'Count', 'Percentage', 'TotalFrequency', 'Locus', 'ElementSize']

    Graph_IgH.to_csv(r'%s/Graph_IgH.txt' % filepath, sep='\t', float_format='%.12f', index=False)
    Graph_IgL.to_csv(r'%s/Graph_IgL.txt' % filepath, sep='\t', float_format='%.12f', index=False)

    def get_Primary(dataframe):
        #
        Primary = dataframe.sort_values(by='Count', ascending=False).reset_index().at[0, 'Geneid']
        PrimaryFreq = dataframe.sort_values(by='Count', ascending=False).reset_index().at[0, 'List_Percent']
        Secondary = dataframe.sort_values(by='Count', ascending=False).reset_index().at[1, 'Geneid']
        SecondaryFreq = dataframe.sort_values(by='Count', ascending=False).reset_index().at[1, 'List_Percent']
        Delta = PrimaryFreq - SecondaryFreq
        return pd.Series([Primary, PrimaryFreq, Secondary, SecondaryFreq, Delta])

    # Equivalent to forTable_IgLC etc in bash script
    IG_light_constant = IGKC_Calc.append(IGLC_Calc).reset_index().drop(columns = 'index')
    IG_light_variable = IGKV_Calc.append(IGLV_Calc).reset_index().drop(columns = 'index')

    primaryIGHC = get_Primary(IGHC_Calc)
    primaryIGHV = get_Primary(IGHV_Calc)
    primaryIGLC = get_Primary(IG_light_constant)
    primaryIGLV = get_Primary(IG_light_variable)

    Topframe = pd.concat([primaryIGHC, primaryIGHV, primaryIGLC, primaryIGLV], axis=1).transpose()
    Topframe.insert(0, 'Locus', ['IGHC', 'IGHV', 'IGLC', 'IGLV'], allow_duplicates=False)
    Topframe.columns = ['Locus', 'Primary', 'PrimaryFreq', 'Secondary', 'SecondaryFreq', 'Delta']

    Top1 = Topframe.sort_values(by='PrimaryFreq', ascending=False).reset_index().drop(columns = 'index').at[0, 'PrimaryFreq']
    Top2 = Topframe.sort_values(by='PrimaryFreq', ascending=False).reset_index().drop(columns = 'index').at[1, 'PrimaryFreq']
    Top1_Delta = Topframe.sort_values(by='PrimaryFreq', ascending=False).reset_index().drop(columns = 'index').at[0, 'Delta']
    Top2_Delta = Topframe.sort_values(by='PrimaryFreq', ascending=False).reset_index().drop(columns = 'index').at[1, 'Delta']

    # This code generates a tab-separated text file containing the important results from the data in one row and
    # labels for each piece of data in a row above.

    # This list contains each of the labels.
    label_list = ["Sample", "PrimaryIgHC", "PrimaryIgHC_Freq", "SecondaryIgHC", "DeltaIgHC", "PrimaryIgHV",
                  "PrimaryIgHV_Freq", "SecondaryIgHV", "DeltaIgHV", "PrimaryIgLC", "PrimaryIgLC_Freq", "SecondaryIgLC",
                  "DeltaIgLC", "PrimaryIgLV", "PrimaryIgLV_Freq", "SecondaryIgLV", "DeltaIgLV", "TOTAL_IGHC_READS",
                  "TOTAL_IGHV_READS", "TOTAL_IGKC_READS", "TOTAL_IGKV_READS", "TOTAL_IGLC_READS", "TOTAL_IGLV_READS",
                  "TOTAL_IGH", "TOTAL_IGK", "TOTAL_IGL", "TOTAL_IG", "PERCENT_IG", "TOTAL_LIGHT_CHAIN",
                  "TOTAL_LIGHT_VARIABLE", "TOTAL_LIGHT_CONSTANT", "PERCENT_KAPPA", "PERCENT_LAMBDA", "Top1", "Top2",
                  "Mean_Top_Delta", "NonB_Contamination"]
    # This list contains each of the corresponding variables converted to strings so they can be written to text.
    # TODO: make this the actual sample name # tentatively done
    results_list = ["%s" % samplename, str(primaryIGHC[0]), str(primaryIGHC[1]), str(primaryIGHC[2]), str(primaryIGHC[4]),
                    str(primaryIGHV[0]), str(primaryIGHV[1]), str(primaryIGHV[2]), str(primaryIGHV[4]),
                    str(primaryIGLC[0]), str(primaryIGLC[1]), str(primaryIGLC[2]), str(primaryIGLC[4]),
                    str(primaryIGLV[0]), str(primaryIGLV[1]), str(primaryIGLV[2]), str(primaryIGLV[4]),
                    str(Total_IGHC_Reads), str(Total_IGHV_Reads), str(Total_IGKC_Reads), str(Total_IGKV_Reads),
                    str(Total_IGLC_Reads), str(Total_IGLV_Reads), str(Total_IGH), str(Total_IGK), str(Total_IGL),
                    str(Total_IG), str(Percent_IG), str(Total_Light_Chain), str(Total_Light_Variable),
                    str(Total_Light_Constant), str(Percent_Kappa), str(Percent_Lambda), str(Top1), str(Top2),
                    str((Top1_Delta + Top2_Delta) / 2), str(geomean)]

    # This block of code opens a new text file, writes the first list into the file tab-separated, then writes
    # a new line, and does the same for the list of results.
    textfile = open(r"%s/%spurityCheckerResults.txt" % (filepath, samplename), "w")
    for element in label_list:
        textfile.write(element + "\t")
    textfile.write("\n")
    for element in results_list:
        textfile.write(element + "\t")
    textfile.close()


# ------------------------------------------------------------------------------------------------------------------- #
# CODE THAT ACTUALLY RUNS THINGS
# ------------------------------------------------------------------------------------------------------------------- #


# returns GTF with essential columns such as "feature", "seqname", "start", "end"
# alongside the names of any optional keys which appeared in the attribute column
pd.set_option('display.max_columns', 30)
# pd.set_option('display.width', 2000)

if build == 'Y':
    gtf_to_build = open(r'%s' % in_gtf, 'r')
    print('GTF opened, converting to dataframe')
    call("echo 'GTF opened, converting to dataframe'", shell=True)
    df = read_gtf(gtf_to_build)
    print('Conversion successful')
    call("echo 'Conversion successful'", shell=True)
    print('Isolating IG regions')
    call("echo 'Isolating IG regions'", shell=True)
    ig_dataframe = isolate_ig(df)
    print('Isolation Successful')
    call("echo 'Isolation Successful'", shell=True)
    # Call the to_gtf function on the specified file.
    print('Converting isolated dataframe to GTF')
    call("echo 'Converting isolated dataframe to GTF'", shell=True)
    to_gtf(ig_dataframe, r'%s/Maidentest' % out_path)
    print('Conversion successful')
    call("echo 'Conversion successful'", shell=True)

else:
    pass

# Run featurecounts from the shell
call("/home/bodinet/Downloads/subread-2.0.2-Linux-x86_64/bin/featureCounts -g gene_name -O -s 0 -Q 10 -T 4 -C -p -a %s/Maidentest.gtf -o /scratch/bodinet/testfolder/"
     "temp_featureCounts_Counts_maidentest.txt /scratch/bodinet/MMRF_2331/rna/alignment/star/"
     "MMRF_2331_1_BM_CD138pos_T3_TSMRU/MMRF_2331_1_BM_CD138pos_T3_TSMRU.star.bam" % out_path, shell=True)



# Run the interpret_featurecounts function on featurecounts' output
interpret_featurecounts('%s' % out_path, '%s' % in_bam)

call("R %s/igh_graph.R --no-save" % out_path, shell=True)








