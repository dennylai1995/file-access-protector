.PHONY: run-test
run-test:
	pip install -r ./test/test.requirement.txt && \
	cp file_access_protector.py ./test/file_util && \
	cd ./test && \
	PYTHONDONTWRITEBYTECODE=1 pytest --cov=file_util --cov-report=html:coverage_report/coverage_html --cov-report=xml:coverage_report/coverage.xml . && \
	genbadge coverage -i ./coverage_report/coverage.xml -o ./coverage-badge.svg