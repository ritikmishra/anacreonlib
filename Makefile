test:
	pipenv install
	pipenv run python -m unittest discover tests/

publish:
	rm -rf build/ dist/
	pipenv install --dev
	pipenv run python setup.py sdist bdist_wheel
	pipenv run twine upload dist/*

check_format:
	pipenv run python -m black --check anacreonlib/