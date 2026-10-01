.PHONY: reproduce test
reproduce:
	python3 tools/reproduce.py

test:
	python3 -m unittest discover -s tests -v
