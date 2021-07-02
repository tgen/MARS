# MMPurityChecker

**Introduction**

The MMPurityChecker (Multiple Myeloma Purity Checker) is a tool designed to analyze RNAseq data from multiple myeloma tumor samples to assess their purity. It is designed for use as a command-line tool.

**Required Software**

- Python 3.7.2 or later
- Pandas 1.2.5 or later
- Subreads 2.0.2 or later
- R 3.6.1 or later

**Inputs and Outputs**

  **Inputs**
  - Required:
   - An input BAM file
  - Optional:
   - A GTF file (with the -b flag invoked to build a reference GTF using the input GTF, or without the -b flag to use the GTF directly). Defaults to provided GTF if absent.
   - An output path (to specify where the output files should go). Defaults to current working directory if absent.
   - A resource directory (to specify where the resource files are located). Defaults to current working directory if absent.
   - A name for the sample. Defaults to the name of the input BAM if absent.
   - The -b option. Invoke to build the reference GTF. Must be used in tandem with the input GTF.

**Biological Theory Behind Design**

**Usage Examples**

All examples should be called at the command line.

To build a reference GTF and use it to analyze the BAM file, specifying name, resource directory, and output path:

/path/to/python/script/main.py -i /path/to/input/BAMfile.bam -g /path/to/input/GTFfile.gtf -b -o /my/output/path -d /my/resource/path -n my_sample_name

To use the default GTF, specifying name and output path:

/path/to/python/script/main.py -i /path/to/input/BAMfile.bam -o /my/output/path -d /my/resource/path -n my_sample_name

To use a custom GTF, with all resources and outputs in the current working directory.

/path/to/python/script/main.py -i /path/to/input/BAMfile.bam -g /path/to/input/GTFfile.gtf

To use as few inputs as possible:

/path/to/python/script/main.py -i /path/to/input/BAMfile.bam




