install: venv upgrade

venv:
ifndef VIRTUAL_ENV
		virtualenv tmp-env
endif

upgrade:
	. tmp-env/bin/activate; \
	cd ..; \
	python setup.py install; \
	pip install -U pytest;

test:
	. tmp-env/bin/activate; \
	py.test -v *.py;

clean:
	rm -rf tmp-env
