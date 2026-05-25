.PHONY: validate metrics new-plan close-plan

validate:
	@if [ -n "$(CLOSE_PLAN)" ]; then \
		bash scripts/validate_harness.sh --close-plan "$(CLOSE_PLAN)"; \
	else \
		bash scripts/validate_harness.sh; \
	fi

metrics:
	python3 scripts/harness_metrics.py

new-plan:
	@if [ -z "$(NAME)" ]; then echo "NAME is required"; exit 2; fi
	@if [ -n "$(PACK)" ]; then \
		python3 scripts/harness_new_plan.py "$(NAME)" "$(PACK)"; \
	else \
		python3 scripts/harness_new_plan.py "$(NAME)"; \
	fi

close-plan:
	@if [ -z "$(PLAN)" ]; then echo "PLAN is required"; exit 2; fi
	python3 scripts/harness_close_plan.py "$(PLAN)"
