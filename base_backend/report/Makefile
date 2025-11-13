# Makefile for IEEE Paper LaTeX Document

TEXFILE = ieee_paper.tex
PDFFILE = ieee_paper.pdf
LATEX = pdflatex
BIBTEX = bibtex
LATEXMK = latexmk

# Default target
all: pdf

# Compile PDF using pdflatex
pdf:
	$(LATEX) $(TEXFILE)
	$(LATEX) $(TEXFILE)
	@echo "PDF generated: $(PDFFILE)"

# Compile using latexmk (automatic)
auto:
	$(LATEXMK) -pdf $(TEXFILE)

# Clean auxiliary files
clean:
	rm -f *.aux *.log *.out *.toc *.bbl *.blg *.fdb_latexmk *.fls *.synctex.gz

# Clean everything including PDF
cleanall: clean
	rm -f $(PDFFILE)

# View PDF (Linux)
view:
	xdg-open $(PDFFILE) 2>/dev/null || evince $(PDFFILE) 2>/dev/null || okular $(PDFFILE) 2>/dev/null

# View PDF (Mac)
view-mac:
	open $(PDFFILE)

# View PDF (Windows - requires start command)
view-win:
	start $(PDFFILE)

# Help
help:
	@echo "Available targets:"
	@echo "  make pdf      - Compile PDF (default)"
	@echo "  make auto     - Compile using latexmk"
	@echo "  make clean    - Remove auxiliary files"
	@echo "  make cleanall - Remove all generated files including PDF"
	@echo "  make view     - Open PDF (Linux)"
	@echo "  make view-mac - Open PDF (Mac)"
	@echo "  make help     - Show this help message"

.PHONY: all pdf auto clean cleanall view view-mac view-win help

