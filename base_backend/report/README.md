# IEEE Conference Paper Report

This directory contains the LaTeX source for the IEEE conference paper format report on the Smart Patch Simulator project.

## Files

- `ieee_paper.tex` - Main LaTeX document
- `README.md` - This file
- `Makefile` - Build automation (optional)

## Prerequisites

To compile this LaTeX document, you need:

1. **LaTeX Distribution:**
   - TeX Live (Linux/Mac): `sudo apt-get install texlive-full` or `brew install --cask mactex`
   - MiKTeX (Windows): Download from https://miktex.org/

2. **Required LaTeX Packages:**
   - IEEEtran class (usually included in full TeX distributions)
   - amsmath, amssymb, amsfonts
   - algorithmic, algorithm
   - graphicx
   - listings
   - hyperref
   - xcolor

## Compilation

### Method 1: Using pdflatex (Recommended)

```bash
pdflatex ieee_paper.tex
bibtex ieee_paper  # If you add .bib file later
pdflatex ieee_paper.tex
pdflatex ieee_paper.tex
```

### Method 2: Using Makefile

```bash
make
```

### Method 3: Using latexmk (Automatic)

```bash
latexmk -pdf ieee_paper.tex
```

## Output

The compilation will generate:
- `ieee_paper.pdf` - The final PDF document
- `ieee_paper.aux`, `ieee_paper.log`, etc. - Auxiliary files (can be deleted)

## Customization

Before submission, update:
1. Author information (name, affiliation, email) in the `\author` block
2. University/organization name in the author block
3. City and country information
4. Any specific conference requirements (if applicable)

## Adding Figures

To add figures, place image files in this directory and use:

```latex
\begin{figure}[!t]
\centering
\includegraphics[width=3.5in]{figure_name.png}
\caption{Figure caption here.}
\label{fig:figure_label}
\end{figure}
```

## Adding Tables

Use the standard LaTeX table environment:

```latex
\begin{table}[!t]
\centering
\caption{Table caption here.}
\label{tab:table_label}
\begin{tabular}{|c|c|}
\hline
Column 1 & Column 2 \\
\hline
Data 1 & Data 2 \\
\hline
\end{tabular}
\end{table}
```

## Notes

- The document uses the IEEE conference paper format (two-column)
- Maximum page limit for most IEEE conferences is 6-8 pages
- Current document is approximately 6-7 pages when compiled
- Algorithm blocks use the `algorithmic` package
- Code listings use the `listings` package

## Troubleshooting

**Error: "File `IEEEtran.cls' not found"**
- Install a full TeX distribution (texlive-full or MiKTeX)

**Error: "Undefined control sequence"**
- Make sure all required packages are installed
- Run `pdflatex` multiple times to resolve references

**Bibliography issues:**
- Currently using manual `thebibliography` environment
- Can be converted to BibTeX by creating a `.bib` file and using `\bibliography{}`

