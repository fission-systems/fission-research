.PHONY: reproduce test migration-reproduce
reproduce:
	python3 tools/reproduce.py

test:
	python3 -m unittest discover -s tests -v

migration-reproduce:
	python3 tools/migration_reproduce.py
