# MMPurityChecker

## Introduction

The MMPurityChecker (Multiple Myeloma Purity Checker) is a tool designed to analyze RNAseq data from multiple myeloma tumor samples to assess their purity. It is designed for use as a command-line tool.

## Required Software

- Python 3.7.2 or later
- Pandas 1.2.5 or later
- Subreads 2.0.2 or later
- R 3.6.1 or later

## Inputs and Outputs

 ### Inputs
  
  **Required:**
  
   - An input BAM file

  **Optional:**
  
   - A GTF file (with the -b flag invoked to build a reference GTF using the input GTF, or without the -b flag to use the GTF directly). Defaults to provided GTF if absent.
   - An output path (to specify where the output files should go). Defaults to current working directory if absent.
   - A resource directory (to specify where the resource files are located). Defaults to current working directory if absent.
   - A name for the sample. Defaults to the name of the input BAM if absent.
   - The -b flag. Invoke to build the reference GTF. Must be used in tandem with the input GTF.

### Outputs

- Two R plots showing clonality of sample.
- One text file containing numerical results.
- One reference GTF (if -b is invoked).

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

### ***All examples should be called at the command line.***

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




