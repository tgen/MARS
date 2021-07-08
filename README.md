# MMPurityChecker

## Introduction

The MMPurityChecker (Multiple Myeloma Purity Checker) is a tool designed to analyze RNAseq data from multiple myeloma 
tumor samples to assess their purity. It is designed for use as a command line tool.

## Inputs, Outputs, and Corresponding Flags

 ### Inputs
  
  **Required:**
  
   - An input BAM file. Corresponds to the `-i` flag as follows: `-i /path/to/input/BAMfile.bam`

  **Optional:**
   - The `-b` flag. Invoke to build the reference GTF from an input GTF. The `-b` flag requires no accompanying
     directory or file and can be typed alone, but if invoked, it must be used in tandem with the `-g` flag and an input GTF.  
   - A GTF file. If absent, the program uses the default GTF in RESOURCE_FILES. **If provided _without_ the `-b` 
     flag invoked, the provided GTF will be used instead of the default.** Corresponds to the `-g` flag as 
     follows: `-g /path/to/input/GTFfile.gtf`
   - An output path specifying where the output files should go. Defaults to current working directory if absent.
     Corresponds to the `-o` flag as follows: `-o /my/output/path`
   - A resource directory specifying where the resource files are located. Defaults to current working directory if absent.
     Corresponds to the `-d` flag as follows: `-d /my/resource/path`
   - A name for the sample. Defaults to the name of the input BAM if absent. 
     Corresponds to the `-n` flag as follows: `-n my_sample_name`
   

### Outputs

- Two R plots showing clonality of sample.
- One text file containing numerical results.
- One reference GTF (if `-b` is invoked).

## Required Software

- Python 3.7.2 or later
- Pandas 1.2.5 or later
- Subreads 2.0.2 or later
- R 3.6.1 or later

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

**To build a reference GTF and use it to analyze the BAM file, specifying 
name, resource directory, and output path:**

`/path/to/python/script/main.py -i /path/to/input/BAMfile.bam -g /path/to/input/GTFfile.gtf -b -o /my/output/path -d 
/my/resource/path -n my_sample_name`

**To use the default GTF, specifying name and output path:**

`/path/to/python/script/main.py -i /path/to/input/BAMfile.bam -o /my/output/path 
-d /my/resource/path -n my_sample_name`

**To use a custom GTF, with all resources and outputs in the current 
working directory.**

`/path/to/python/script/main.py -i /path/to/input/BAMfile.bam -g /path/to/input/GTFfile.gtf`

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
