install:
	pip3 install --upgrade pip
	python3 -m pip install --upgrade setuptools
	pip3 install --no-cache-dir  --force-reinstall -Iv grpcio==1.31.0
	pip3 install
	pip install tinkoff-voicekit-client
	pip install prompt

.PHONY: install
