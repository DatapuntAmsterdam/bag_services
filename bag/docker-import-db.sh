#!/usr/bin/env bash

set -u   # crash on missing environment variables
set -e   # stop on any error
set -x   # log every command.

source docker-wait.sh

# download csv
python objectstore/objectstore.py

# load dat in database
python manage.py migrate
python manage.py run_import bag --no-index &  \
python manage.py run_import brk --no-index

python manage.py run_import wkpb --no-index
