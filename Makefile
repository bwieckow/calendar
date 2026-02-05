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
	@echo "Setting up SSM parameters for Brevo SMTP..."
	@echo "Please update these commands with your actual values:"
	@echo "aws ssm put-parameter --name /calendar/dev/ical-feed-url --value 'YOUR_ICAL_URL' --type SecureString --overwrite"
	@echo "aws ssm put-parameter --name /calendar/dev/smtp-from-email --value 'YOUR_EMAIL' --type SecureString --overwrite"
	@echo "aws ssm put-parameter --name /calendar/dev/smtp-username --value 'YOUR_BREVO_LOGIN' --type SecureString --overwrite"
	@echo "aws ssm put-parameter --name /calendar/dev/smtp-password --value 'YOUR_BREVO_SMTP_KEY' --type SecureString --overwrite"
	@echo "aws ssm put-parameter --name /ops-master/cloudfront/apikey --value 'YOUR_API_KEY' --type SecureString --overwrite"
	@echo "aws ssm put-parameter --name /calendar/dev/payu-second-key --value 'YOUR_PAYU_KEY' --type SecureString --overwrite"

# Setup Brevo account (informational)
setup_brevo:
	@echo "Brevo SMTP Setup Instructions:"
	@echo "1. Sign up at https://www.brevo.com (free tier: 300 emails/day)"
	@echo "2. Go to Settings → SMTP & API → SMTP"
	@echo "3. Generate an SMTP key (this is your password)"
	@echo "4. Add and verify a sender email address"
	@echo "5. Store credentials in SSM using 'make setup_ssm'"

# Help command
help:
	@echo "Available commands:"
	@echo "  make ical_lambda_layer  - Build Lambda layer with dependencies"
	@echo "  make virtualenv         - Create and setup virtual environment"
	@echo "  make get_test           - Test GET request (retrieve events)"
	@echo "  make post_test          - Test POST request (send invitation)"
	@echo "  make clean              - Remove generated files and caches"
	@echo "  make setup_ssm          - Display commands to setup SSM parameters"
	@echo "  make setup_brevo        - Display Brevo SMTP setup instructions"
	@echo "  make help               - Show this help message"

.PHONY: ical_lambda_layer virtualenv get_test post_test clean setup_ssm setup_brevo help