import pandas as pd
import numpy as np
import os
from gtfparse import read_gtf
from subprocess import call

    # shell=True is so you can handle redirects like in the 3rd command
    call("echo('It works')", shell=True)
exit

# ------------------------------------------------------------------------------------------------------------------- #
# FUNCTIONS THAT SUPPORT CODE AT BOTTOM
# ------------------------------------------------------------------------------------------------------------------- #


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
                        to_gtf(df, r'/Users/myname/Desktop/example')
                        *** The r is not a typo. This formats the path as a raw string.
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
    dataframe.to_csv('%s.csv' % filepath, index=False)
    print('CSV Written')
    # This block of code converts the CSV to a GTF by taking each column, writing in as a string, inserting a tab, and
    # starting a new line after the ninth column. (even though it says [8], its a 0-index, which is confusing but still)
    # The text file will be saved in the specified file path. It WILL NOT overwrite files with the same name.
    print('Converting to GTF')
    data = pd.read_csv('%s.csv' % filepath, encoding='utf-8')
    with open('%s.gtf' % filepath, 'a+', encoding='utf-8') as f:
        for line in data.values:
            f.write((str(line[0]) + '\t' + str(line[1]) + '\t' + str(line[2]) + '\t' + str(line[3]) + '\t' + str(
                line[4]) + '\t' + str(line[5]) + '\t' + str(line[6]) + '\t' + str(line[7]) + '\t' + str(
                line[8]) + '\n'))
    print('GTF conversion complete')
    # This removes the CSV that was made earlier, since it's only necessary to write the GTF. If you want to keep the
    # CSV, feel free to disable/delete this line.
    print('Removing CSV')
    os.remove('%s.csv' % filepath)
    print('CSV Removed')


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


# ------------------------------------------------------------------------------------------------------------------- #
# CODE THAT ACTUALLY RUNS THINGS
# ------------------------------------------------------------------------------------------------------------------- #


# returns GTF with essential columns such as "feature", "seqname", "start", "end"
# alongside the names of any optional keys which appeared in the attribute column
pd.set_option('display.max_columns', 30)
# pd.set_option('display.width', 2000)

Homo_Sapiens_38 = open("/Users/bodinet/Downloads/Mus_musculus.GRCm38.98.gtf", 'r')
print('GTF opened, converting to dataframe')
df = read_gtf(Homo_Sapiens_38)
print('Conversion successful')
df = df.head(20)

# Call the to_gtf function on the specified file.
to_gtf(df, r'/Users/bodinet/Desktop/mouse_test3')

# print('step3')
# df.to_csv(r'/Users/bodinet/Downloads/Mouse_Dataframe_8.csv', index = True, header=True)
# print('step4')

humandf = pd.read_csv(r'/Users/bodinet/Downloads/Human_Dataframe_8.csv')
chromosomelist = ['2', '14', '22']
rlist = ['IG_V', 'IG_C']

igs_isolated = isolate_ig(humandf, chromosomelist, rlist)
