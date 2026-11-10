# Student CRUD Manager - developer shortcuts
IMAGE      ?= student-crud-manager
TAG        ?= latest
CONTAINER  ?= student-crud
PORT       ?= 8000
VOLUME     ?= student-data
# Optional CA bundle for builds behind a TLS-intercepting proxy, e.g. make build PIP_CA=/path/ca.crt
PIP_CA     ?=
SECRET     := $(if $(PIP_CA),--secret id=pip_ca,src=$(PIP_CA),)

.PHONY: help build test run stop logs status clean up down

help:            ## Show available targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-8s %s\n", $$1, $$2}'

build:           ## Build the production image
	docker build $(SECRET) -t $(IMAGE):$(TAG) .

test:            ## Run the test suite inside Docker (test stage)
	docker build $(SECRET) --target test -t $(IMAGE):test .

run:             ## Run the container in the background on $(PORT)
	docker run -d --name $(CONTAINER) -p $(PORT):8000 -v $(VOLUME):/app/data $(IMAGE):$(TAG)
	@echo "App running at http://localhost:$(PORT)"

stop:            ## Stop and remove the container (data volume is kept)
	-docker stop $(CONTAINER)
	-docker rm $(CONTAINER)

logs:            ## Follow container logs
	docker logs -f $(CONTAINER)

status:          ## Show container status and health
	docker ps --filter name=$(CONTAINER) --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

clean: stop      ## Stop container, remove images and the data volume
	-docker rmi $(IMAGE):$(TAG) $(IMAGE):test
	-docker volume rm $(VOLUME)

up:              ## Start with Docker Compose
	docker compose up -d --build

down:            ## Stop Docker Compose services
	docker compose down
