# MMPurityChecker

## Introduction

The MMPurityChecker (Multiple Myeloma Purity Checker) is a tool designed to analyze RNAseq data from multiple myeloma 
tumor samples to assess their purity. It is designed for use as a command line tool.

## Inputs, Outputs, and Corresponding Flags

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
   - `-b` The `-b` flag. Invoke to build the reference GTF from an input GTF. The `-b` flag requires no accompanying
     directory or file and can be typed alone, but if invoked, it must be used in tandem with the `-g` flag and an input GTF.  
   - `-g` A GTF file. If absent, the program uses the default GTF in RESOURCE_FILES. **If provided _without_ the `-b` 
     flag invoked, the provided GTF will be used instead of the default.** Corresponds to the `-g` flag as 
     follows: `-g /path/to/input/GTFfile.gtf`
   - `-o` An output path specifying where the output files should go. Defaults to current working directory if absent.
     Corresponds to the `-o` flag as follows: `-o /my/output/path`
   - `-k` The `-k` flag. Invoke to keep temporary files used in the script. The `-k` flag requires no accompanying
     directory or file and can be typed alone. Users should be warned that invoking the  `-k` flag will leave temporary
     files in both the output and resource directories.
   - `-f` An input FASTA file. If the input file is in CRAM format, an input FASTA must also be provided. Corresponds 
     to the `-f` flag as follows: `-f /path/to/FASTAfile.fa`  
   - `-d` A resource directory specifying where the resource files are located. Defaults to current working directory if absent.
     Corresponds to the `-d` flag as follows: `-d /my/resource/path`
   - `-n` A name for the sample. Defaults to the name of the input BAM/CRAM/SAM if absent. 
     Corresponds to the `-n` flag as follows: `-n my_sample_name`
   - `-t` An integer number of threads to use. Default is 1 thread. Corresponds to the `-t` flag as follows:
     `-t [INT]`, for example `-t 6`
   

### Outputs

- Two R plots showing clonality of sample.
- One text file containing numerical results.
- One reference GTF (if `-b` is invoked).

## Required Software

- Python 3.7.2 or later
- Pandas 1.2.5 or later
- Subreads 2.0.2 or later
- R 3.6.1 or later
- Samtools 1.9 or later (tested with 1.10)

## Required Files
Downloading the "RESOURCE_FILES" folder from this repository should ensure the user has all 
necessary files. Once RESOURCE_FILES is placed in a convenient directory, invoking the `-d` 
flag to the directory as follows should allow the user to run the purity checker as intended:
`-d my/resource/path/RESOURCE_FILES`


## Biological Theory Behind Design

Multiple Myeloma (MM) is a cancer of plasma cells, a type of white blood
cell responsible for producing a single unique immunoglobulin (IG). 
Experimental data show that it is extremely rare for mutations in oncogenes 
causing uncontrolled cell growth and mutations in genes responsible for IG 
production to overlap. Consequently, a 100% pure myeloma sample should 
theoretically exhibit production of only one IG RNA sequence, with additional 
IG RNA serving as an indicator of decreased purity. Furthermore, production 
of RNA associated with genes *downregulated* in plasma cells should serve as 
an additional indicator of contamination. This software uses the Subreads 
tool featureCounts to obtain RNA counts corresponding to IG genes and known 
contaminants, and graphs the output to provide an indication of sample purity.

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
File To be Provided with its FAI index.`. Including an input FASTA using the `-f` flag will fix the error.