activate:
	@echo "Activating venv..."
	@source venv/bin/activate

update-requirements:
	@echo "Updating requirements.txt..."
	@pip freeze > requirements.txt && echo "requirements.txt updated"
