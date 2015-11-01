#!/bin/sh
source $OPENSHIFT_HOMEDIR/python/virtenv/venv/bin/activate
python $OPENSHIFT_REPO_DIR/manage.py tenant_activators

