dropdb -U talli tenant &&
createdb -U talli tenant &&
python manage.py migrate_schemas && python manage.py copy_db --domain="%s.localhost"
