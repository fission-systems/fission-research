.PHONY: reproduce test migration-reproduce layout-reproduce
reproduce:
	python3 tools/reproduce.py

test:
	python3 -m unittest discover -s tests -v

migration-reproduce:
	python3 tools/migration_reproduce.py

layout-reproduce:
	python3 tools/register_layout_reproduce.py
