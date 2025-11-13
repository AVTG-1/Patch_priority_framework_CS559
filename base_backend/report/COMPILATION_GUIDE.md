# IEEE Paper Compilation Guide

## Quick Start

1. **Navigate to the report directory:**
   ```bash
   cd report
   ```

2. **Compile the LaTeX document:**
   ```bash
   pdflatex ieee_paper.tex
   pdflatex ieee_paper.tex  # Run twice for references
   ```

   Or use the Makefile:
   ```bash
   make pdf
   ```

3. **View the generated PDF:**
   ```bash
   make view  # Linux
   # or
   open ieee_paper.pdf  # Mac
   # or
   start ieee_paper.pdf  # Windows
   ```

## Document Structure

The IEEE paper includes:

1. **Title and Abstract** - Overview of the Smart Patch Simulator
2. **Introduction** - Background, problem statement, objectives
3. **Related Work** - Vulnerability prioritization, game theory, risk assessment
4. **System Architecture** - High-level design, data models, algorithms
5. **Implementation** - Technology stack, modules, testing
6. **Results** - Experimental setup, analysis, parameter sensitivity
7. **Conclusion** - Summary, contributions, limitations, future work
8. **References** - Bibliography in IEEE format

## Key Features

- **IEEE Conference Format**: Two-column layout, standard IEEE styling
- **Algorithms**: PageRank-style importance calculation algorithm
- **Mathematical Formulations**: Payoff functions, RIS calculations
- **Code Listings**: JSON export format example
- **Comprehensive Coverage**: All aspects of the project documented

## Customization Before Submission

Before submitting to a conference, update:

1. **Author Information** (lines ~25-30):
   - Replace `[Your University/Organization]` with actual name
   - Update `[City, Country]` with actual location
   - Update email address

2. **Conference-Specific Requirements**:
   - Check page limits (typically 6-8 pages)
   - Add conference name in header if required
   - Adjust formatting per conference guidelines

3. **Content Enhancements**:
   - Add figures/screenshots if available
   - Add tables with experimental data
   - Expand results section with more detailed analysis

## Adding Figures

1. Place image files (PNG, PDF, JPG) in the `report/` directory
2. Add figure code:
   ```latex
   \begin{figure}[!t]
   \centering
   \includegraphics[width=3.5in]{figure_name.png}
   \caption{Your caption here.}
   \label{fig:label}
   \end{figure}
   ```
3. Reference in text: `As shown in Figure~\ref{fig:label}`

## Adding Tables

```latex
\begin{table}[!t]
\centering
\caption{Table caption.}
\label{tab:label}
\begin{tabular}{|l|c|r|}
\hline
Header 1 & Header 2 & Header 3 \\
\hline
Data 1 & Data 2 & Data 3 \\
\hline
\end{tabular}
\end{table}
```

## Troubleshooting

### Common Issues

**"File `IEEEtran.cls' not found"**
- Solution: Install full TeX distribution
  - Ubuntu/Debian: `sudo apt-get install texlive-full`
  - Mac: `brew install --cask mactex`
  - Windows: Install MiKTeX from https://miktex.org/

**"Undefined control sequence"**
- Solution: Run `pdflatex` multiple times to resolve cross-references

**Overfull/Underfull hbox warnings**
- These are usually cosmetic. Adjust text or figure sizes if needed.

**Bibliography not showing**
- Current version uses manual bibliography. To use BibTeX:
  1. Create `references.bib` file
  2. Replace `\begin{thebibliography}` section with `\bibliography{references}`
  3. Run: `pdflatex`, `bibtex`, `pdflatex`, `pdflatex`

## Page Count

Current document is approximately **6-7 pages** when compiled, which fits within typical IEEE conference limits (6-8 pages).

## Next Steps

1. Review and customize author information
2. Add any missing experimental results
3. Consider adding figures/diagrams for better visualization
4. Proofread for grammar and clarity
5. Check all references are properly cited
6. Verify all equations and algorithms are correct
7. Submit to target conference/journal

## Support

For LaTeX questions:
- Overleaf documentation: https://www.overleaf.com/learn
- IEEE author guidelines: Check your target conference website
- LaTeX Stack Exchange: https://tex.stackexchange.com/

