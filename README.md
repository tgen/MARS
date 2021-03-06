# MARS
**Primary Developer:** Bertrand Odinet

**Additional Developers:** Dr. Jonathan J. Keats, Dr. Christophe Legendre, Bryce Turner, Daniel Enriquez

## Introduction

The MARS program (Myeloma Analysis for RNASeq) is a tool designed to analyze RNAseq data from Multiple Myeloma 
tumor samples to assess their purity. It is designed for use as a command line tool.

## Biological Theory Behind Design

Multiple Myeloma (MM) is a cancer of plasma cells, a type of white blood
cell responsible for producing a single unique immunoglobulin (IG, synonym for antibody). 
Experimental data show that MM tumors produce a single IG, where all cells share the same VDJ sequence, and the same 
selection of heavy and light chains. Consequently, a 100% pure myeloma sample should 
express only one IG RNA sequence, with additional 
IG RNA serving as an indicator of decreased purity. Furthermore, production 
of RNA associated with genes expressed in non-B lineage cells should serve as 
an additional indicator of contamination. This software uses featureCounts, a module of the Subread tool,
to quickly obtain RNA counts corresponding to IG genes and known 
contaminants, and graphs the output to provide an indication of sample purity.

### Example of Outputs for Monoclonal Sample


![MMRF_1086_1_BM_CD138pos_T2_TSMRU starIGH](https://user-images.githubusercontent.com/57779509/126364043-a87b9692-55ca-410a-b026-197556d8cf3b.png)
![MMRF_1086_1_BM_CD138pos_T2_TSMRU starIGL](https://user-images.githubusercontent.com/57779509/126364073-b3f3b6cb-70b3-4bc6-9942-7932a801a5b0.png)



### Example of Outputs for Polyclonal Sample


![MMRF_1101_2_BM_CD138pos_T2_TSMRU starIGH](https://user-images.githubusercontent.com/57779509/126364227-bc021384-8b77-4721-8fd6-628bd520cc33.png)
![MMRF_1101_2_BM_CD138pos_T2_TSMRU starIGL](https://user-images.githubusercontent.com/57779509/126364243-efb55d58-7c17-41d5-ba10-06496bf3e9ee.png)


## Inputs, Outputs, and Flags

 ### Inputs
  
  **Required:**
  
   - `-i` An input file, which can be in BAM, CRAM, or SAM format. If in CRAM format, it will be converted to BAM for 
     analysis, and a BAI index file will be generated. \
     If in CRAM format, a FASTA file must also be provided using the `-f` flag. \
     If in CRAM format, a CRAI index file must be present in the 
     same directory as the CRAM file, and if in BAM format, the same must be true for a BAI index file. 
     Corresponds to the `-i` flag as follows:
     `-i /path/to/input/BAMfile.bam` or `-i /path/to/input/SAMfile.sam` or `-i /path/to/input/CRAMfile.cram`

  **Optional:**
   - `-b` Invoke the `-b` flag to build the reference GTF from an input GTF. The `-b` flag requires no accompanying
     directory or file and can be typed alone, but if invoked, it must be used in tandem with the `-g` flag and an input GTF.
     

   - `-g` A GTF file. If absent, the program uses the default GTF in RESOURCE_FILES. **If provided _without_ the `-b` 
     flag invoked, the provided GTF will be used instead of the default.** Corresponds to the `-g` flag as 
     follows: `-g /path/to/input/GTFfile.gtf`
     

   - `-o` An output path specifying where the output files should go. Defaults to current working directory if absent.
     Corresponds to the `-o` flag as follows: `-o /my/output/path`
     

   - `-k` Invoke the `-k` flag to keep temporary files used in the script. The `-k` flag requires no accompanying
     directory or file and can be typed alone. Users should be understand that invoking the  `-k` flag will leave temporary
     files in the output directory.
     

   - `-f` An input FASTA file. If the input file is in CRAM format, an input FASTA must also be provided, along with the FAI index. Corresponds 
     to the `-f` flag as follows: `-f /path/to/FASTAfile.fa`  
     

   - `-d` A resource directory specifying where the resource files are located. Defaults to current working directory if absent.
     Corresponds to the `-d` flag as follows: `-d /my/resource/path`
     

   - `-n` A name for the sample. Defaults to the name of the input BAM/CRAM/SAM if absent. 
     Corresponds to the `-n` flag as follows: `-n my_sample_name`
     

   - `-t` An integer number of threads to use. Default is 1 thread. Corresponds to the `-t` flag as follows:
     `-t [INT]`, for example `-t 6`


   - `-build_only` Invoke this flag to only build an IG GTF from a reference GTF and output into the output path, but not
     use the GTF to analyze an alignment file. Must be used in tandem with the `-b` flag, as well as the `-g` flag and 
     an input GTF. The `-i` flag must also be included with a dummy alignment file name, in order to satisfy the program's
     error-checking functions (any string followed by `.bam` or `.sam` will work, even if no file with that name exists. We actually recommend using `dummy.bam`). It is recommended to use the `-n` flag in this mode to name the output GTF, since by default,
     it will be given the name of the dummy alignment file. If `-k` is invoked with `-build_only`, then the CSV file used to generate the GTF will be kept in the output path.
   

### Outputs

- Two R plots showing clonality of sample, in the form `sample_nameIGL.png` and `sample_nameIGH.png`.
- One text file containing numerical results, in the form `sample_namepurityCheckerResults.txt`.
- One reference GTF (if `-b` is invoked), in the form `sample_name.gtf`.

**Definitions of Results**
- Sample: The sample name
- PrimaryIgHC: The most-expressed IG heavy constant region (in terms of total reads among all IgHC regions)
- PrimaryIgHCFreq: The fraction of PrimaryIgHC reads with respect to all IgHC reads. That is, if 90% of reads for all
  IgHC regions map to IGHA1, PrimaryIgHCFreq = 0.9.
- SecondaryIgHC: The second-most-expressed IG heavy constant region
- DeltaIgHC: The difference in expression between PrimaryIgHC and SecondaryIgHC, calculated by
  taking the difference between the PrimaryIgHCFreq and what would be SecondaryIgHCFreq (SecondaryIgHCFreq is not included for brevity)
- For [Primary/Secondary/Freq/Delta] [IgHV/IgLC/IgLV], the explanations are essentially identical to above
- TOTAL_IGHC_READS: The total number of Ig Heavy Constant reads
- TOTAL_IGHV_READS: The total number of Ig Heavy Variable reads
- TOTAL_IGKC/V_READS: The total number of Ig Kappa Light Chain Constant/Variable reads
- TOTAL_IGLC/V_READS: The total number of Ig Lambda Light Chain Constant/Variable reads
- TOTAL_IGH: Total IG Heavy reads, regardless of constant or variable
- TOTAL_IGK: Total IG Light Kappa reads, regardless of constant or variable
- TOTAL_IGL: Total IG Light Lambda reads, regardless of constant or variable
- TOTAL_IG: Total IG reads, without exception
- PERCENT_IG: TOTAL_IG divided by all reads in the sample
- TOTAL_LIGHT_CHAIN: Reads for all light chain segments
- TOTAL_LIGHT_VARIABLE: Reads for all light variable, whether kappa or lambda
- TOTAL_LIGHT_CONSTANT: Reads for all light constant, whether kappa or lambda
- PERCENT_KAPPA: Kappa reads divided by all light chain reads
- PERCENT_LAMBDA: Lambda reads divided by all light chain reads
- Top1: The most expressed gene overall, as a fraction of reads of all Ig genes
- Top2: The second-most expressed gene overall, as a fraction of reads of all Ig genes
- Mean_Top_Delta: The average of the Deltas of Top1 and Top2 with respect to their Ig families
- NonB_Contamination: The geometric mean of the RPKM of the samples
- Clonality: The likely clonality of the sample, as determined by the program

## Required Software

- Python 3.7.2 or later 
  - pandas 1.2.5 or later 
  - argparse
  - scipy
  - os
  - sys
  - gtfparse
  - subprocess
- R 3.6.1 or later
  - ggplot2
  - stringr
- Subread 2.0.2 or later
- Samtools 1.9 or later (tested with 1.10)

The build mode of the program has been tested with the Ensembl human GTF format.

The input file (BAM, CRAM, SAM) should contain RNA data, where mapping adheres to the Tophat format (i.e. unique alignment = 255).
The program as a whole has been tested with files aligned via STAR.

## Required Files
Cloning this repository should ensure the user has all necessary files, which are included in the RESOURCE_FILES folder. 
Once RESOURCE_FILES is placed in a convenient directory, invoking the `-d` 
flag to the directory as follows should allow the user to run the MARS program as intended:
`-d my/resource/path/RESOURCE_FILES`

## Managing Program Defaults
MARS uses a file called USER_DEFAULTS.txt to manage default preferences that are unlikely to change
frequently enough to warrant a command line argument, but should still be editable without rewriting actual lines 
of code.


***PLEASE NOTE:*** As specified in the file itself, the layout, formatting, and number of lines in USER_DEFAULTS.txt are each important 
for ensuring correct processing. Please abide by the recommendations here when editing the default file, unless you 
intend to rewrite the code itself, or otherwise are extremely confident in your understanding of the program and have
a specific reason to contradict the recommendations below.


**The defaults available to change in this file are as follows:**

- **The name of the default GTF:** This is the GTF that will be used if no GTF is specified at the command line. To 
  change, load a GTF of your preference into your resource directory, and replace 'HUMAN_IG_DEFAULT' in line 3 of the 
  USER_DEFAULTS file with the name of your GTF. The `.gtf` extension ***SHOULD NOT*** be included.
  
  The RESOURCE_FILES folder comes with a pre-built GTF called HUMAN_IG_DEFAULT.gtf, containing human IGs and known contaminants,
  based on the GRCh38 human GTF from the Genome Reference Consortium. As of July 2021, this was the most up-to-date 
  version available.
  

- **The default chromosomes:** If building a new GTF, these are the chromosomes that will be searched in the new GTF
  for immunoglobulin genes. To edit, simply add, subtract or replace the numbers in line 5 of the 
  USER_DEFAULTS file with the number of the chromosome(s) you want to include. Chromosome numbers should be 
  space-separated integers only, with no additional characters. Even if the base GTF designates chromosomes with the 
  'chr1, chr2, etc.' convention, as opposed to the '1, 2, etc.' convention, only the numbers should be included. 
The program is capable of handling either case as long as only the number is provided. 

    By default, chromosomes 2, 14, and 22 are listed in the file, as these are the chromosomes where human IG genes are found.
These are not the correct chromosomes for other animals, and should be changed before attempting to build an IG GTF 
for a different organism.
  

- **The default Immunoglobulin components:** If building a new GTF, these are the specific sub-type of IG gene that will
  be included. To edit, simply add, subtract or replace the strings in line 7 of the 
  USER_DEFAULTS file with the type of components you want to include. Components should be 
  space-separated strings only, with no additional characters.
  
  By default, IG_V and IG_C are listed in the file, corresponding to genes for all IG variable and IG constant regions.
  IG_J (joining) and IG_D (diversity) are excluded because they do little to help assess purity. These strings correspond to the naming 
  convention in the source GTF, and are not guaranteed to be universal. Consequently, when building a new GTF, the user
  should check the gene biotype tag to ensure the naming convention has not changed.
  
  
- **The path to featureCounts:** The program will search in this path to launch Subread's featureCounts tool. To 
  change, replace the path in line 9 of the USER_DEFAULTS file with an alternate path. 
  
  The file comes with a path
  that is functional within the Phoenix Translational Genomics Research Institute (TGen), where this program was 
  developed.


## Usage Examples

***\*NOTE: All examples should be used at the command line.****

### Correct Usage Examples

**To build a reference GTF and use it to analyze a CRAM file, specifying 
name, resource directory, and output path, while keeping temporary files, and using 8 threads:**

`/path/to/python/script/main.py -i /path/to/input/CRAMfile.cram -g /path/to/input/GTFfile.gtf -b -o /my/output/path -d 
/my/resource/path -n my_sample_name -k -t 8 -f /path/to/input/FASTAfile.fa`

**To build a reference GTF and use it to analyze a BAM file, specifying 
name, resource directory, and output path, removing temporary files:**

`/path/to/python/script/main.py -i /path/to/input/BAMfile.bam -g /path/to/input/GTFfile.gtf -b -o /my/output/path -d 
/my/resource/path -n my_sample_name`

**To build a reference GTF only, without keeping temporary files, assigning it a specific name:**

`/path/to/python/script/main.py -i dummy.bam -g /path/to/input/GTFfile.gtf -b -o /my/output/path -d 
/my/resource/path -n name_of_new_gtf -build_only`

**To use the default GTF on a BAM, specifying name and output path:**

`/path/to/python/script/main.py -i /path/to/input/BAMfile.bam -o /my/output/path 
-d /my/resource/path -n my_sample_name`

**To use a custom GTF on a SAM file, with all resources and outputs in the current 
working directory.**

`/path/to/python/script/main.py -i /path/to/input/SAMfile.sam -g /path/to/input/GTFfile.gtf`

**To use as few inputs as possible:**

`/path/to/python/script/main.py -i /path/to/input/BAMfile.bam`

### Common Incorrect Usage Examples

**Incorrect use of slash in path:**

`/path/to/python/script/main.py -i /path/to/input/BAMfile.bam -g /path/to/input/GTFfile.gtf -b -o /my/output/path/ -d 
/my/resource/path/ -n my_sample_name`

The example above will result in an error because a `/` is used at the end of the paths under the `-o` and `-d` flags.
At any point where it is necessary to add a `/` to write or reference a file, the program will do it automatically.
Including the `/` will likely cause an error such as: `ERROR: The directory '/my/resource/path//HUMAN_IG_DEFAULT.gtf' does not exist.`
Removing the `/` will fix the error.

**Incorrect use of `-b` flag:**

`/path/to/python/script/main.py -i /path/to/input/BAMfile.bam -b -o /my/output/path -d /my/resource/path -n my_sample_name`

The example above will result in an error because the user has told the program to filter a GTF that does not exist.
Using `-b` without `-g` will likely cause an error such as: `ERROR: To build files an input GTF must be provided.` Including
an input GTF using the `-g` flag will fix the error.

**Missing input BAM file:**

`/path/to/python/script/main.py -g /path/to/input/GTFfile.gtf -b -o /my/output/path -d 
/my/resource/path -n my_sample_name`

The example above will result in an error because the user has not provided a BAM file for the program to analyze.
Not using `-i` will likely cause an error such as: `ERROR: argument -i/--input_bam: expected one argument`. Including
an input BAM using the `-i` flag will fix the error.

**Missing input FASTA file with CRAM:**

`/path/to/python/script/main.py -i /path/to/input/CRAMfile.cram -g /path/to/input/GTFfile.gtf -b -o /my/output/path -d 
/my/resource/path -n my_sample_name`

The example above will result in an error because the user has not provided a FASTA file for the program to convert
the CRAM into a BAM for analysis.
Not providing a FASTA will likely cause an error such as: `ERROR: reading CRAM file requires a Reference Genome Fasta 
File To be Provided with its FAI index.` Including an input FASTA using the `-f` flag will fix the error.
