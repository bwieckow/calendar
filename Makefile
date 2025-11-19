# Detect OS - works on Windows, Linux, and macOS
ifeq ($(OS),Windows_NT)
    DETECTED_OS := Windows
else
    DETECTED_OS := $(shell uname -s)
endif

ical_lambda_layer:
	cd ./infrastructure/ical_lambda_layer && \
	mkdir -p python && \
	pip install -r requirements.txt -t python && \
	zip -r ical-layer.zip python

virtualenv:
	python3 -m venv venv
ifeq ($(DETECTED_OS),Windows)
	.\venv\Scripts\activate && pip install -r requirements.txt
	@echo "Virtual environment created. Activate with: venv\Scripts\activate"
else
	. venv/bin/activate && pip install -r requirements.txt
	@echo "Virtual environment created. Activate with: source venv/bin/activate"
endif
	@echo "Virtual environment created and dependencies installed."

get_test:
	python -c 'import json; from src.lambda_function import lambda_handler; event = json.load(open("src/event_get.json")); context = {}; response = lambda_handler(event, context); print(json.dumps(response, indent=2))'

post_test:
	python -c 'import json; from src.lambda_function import lambda_handler; event = json.load(open("src/event_post.json")); context = {}; response = lambda_handler(event, context); print(json.dumps(response, indent=2))'

# Clean up generated files
clean:
	rm -rf ./infrastructure/ical_lambda_layer/python
	rm -f ./infrastructure/ical_lambda_layer/ical-layer.zip
	rm -rf venv
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Setup SSM parameters (requires AWS CLI configured)
setup_ssm:
	@echo "Setting up SSM parameters..."
	@echo "Please update these commands with your actual values:"
	@echo "aws ssm put-parameter --name calendar-ical-feed-url --value 'YOUR_ICAL_URL' --type String --overwrite"
	@echo "aws ssm put-parameter --name calendar-ses-from-email --value 'YOUR_EMAIL' --type String --overwrite"
	@echo "aws ssm put-parameter --name /ops-master/cloudfront/apikey --value 'YOUR_API_KEY' --type String --overwrite"
	@echo "aws ssm put-parameter --name calendar-payu-second-key --value 'YOUR_PAYU_KEY' --type SecureString --overwrite"

# Verify SES email (requires AWS CLI configured)
verify_ses_email:
	@read -p "Enter email address to verify: " email; \
	aws ses verify-email-identity --email-address $$email --region eu-west-1

# Help command
help:
	@echo "Available commands:"
	@echo "  make ical_lambda_layer  - Build Lambda layer with dependencies"
	@echo "  make virtualenv           - Create and setup virtual environment"
	@echo "  make get_test             - Test GET request (retrieve events)"
	@echo "  make post_test            - Test POST request (send invitation)"
	@echo "  make clean                - Remove generated files and caches"
	@echo "  make setup_ssm            - Display commands to setup SSM parameters"
	@echo "  make verify_ses_email     - Verify email address in AWS SES"
	@echo "  make help                 - Show this help message"

.PHONY: ical_lambda_layer virtualenv get_test post_test clean setup_ssm verify_ses_email help