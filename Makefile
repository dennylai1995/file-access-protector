.PHONY: run-test
run-test:
	pip install -r test.requirement.txt && \
	cd src && \
	PYTHONDONTWRITEBYTECODE=1 python3 -m pytest --cov=file_access_protector --cov-report=html:coverage_report/coverage_html --cov-report=xml:coverage_report/coverage.xml . && \
	genbadge coverage -i coverage_report/coverage.xml -o ./tests/coverage-badge.svg