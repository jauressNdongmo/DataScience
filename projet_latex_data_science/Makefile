TARGET=main

export TEXINPUTS=..:
export BIBINPUTS=..:

all: $(TARGET).pdf

$(TARGET).pdf: $(TARGET).tex
	@echo "--- Etape 1: Compilation pdflatex ---"
	-pdflatex -interaction=nonstopmode $(TARGET).tex
	@echo "--- Etape 2: Compilation bibtex ---"
	-bibtex $(TARGET)
	@echo "--- Etape 3: Compilation pdflatex (intégration des références) ---"
	-pdflatex -interaction=nonstopmode $(TARGET).tex
	@echo "--- Etape 4: Compilation finale pdflatex ---"
	-pdflatex -interaction=nonstopmode $(TARGET).tex
	@echo "--- Compilation réussie ! ---"
	@echo "--- Nettoyage automatique des fichiers temporaires ---"
	@$(MAKE) clean



fast:
	pdflatex -interaction=nonstopmode $(TARGET).tex



clean:
	rm -f *.aux *.bbl *.blg *.log *.out *.toc *.lof *.lot *.mw \
	      */.aux */*.aux

		  
distclean: clean
	rm -f $(TARGET).pdf

.PHONY: all clean distclean fast $(TARGET).pdf
