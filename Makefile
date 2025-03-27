google_lambda_layer:
	cd ./infrastructure/google_lambda_layer && \
	mkdir -p python && \
	pip install -r requirements.txt -t python && \
	zip -r google-layer.zip python

virtualenv:
	python -m venv venv
	ifeq ($(OS),Windows_NT)
		venv\Scripts\activate
	else
		source venv/bin/activate
	endif
	pip install -r requirements.txt

get_test:
	python -c 'import json; from src.lambda_function import lambda_handler; event = json.load(open("src/event_get.json")); context = {}; response = lambda_handler(event, context); print(response)'

post_test:
	python -c 'import json; from src.lambda_function import lambda_handler; event = json.load(open("src/event_post.json")); context = {}; response = lambda_handler(event, context); print(response)'