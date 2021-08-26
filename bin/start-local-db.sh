#!/usr/bin/sh
db_image="postgres:13"
db_host="localhost"
db_port=5432

POSTGRES_USER="postgres"
POSTGRES_PASSWORD="top-secret"
POSTGRES_DB="feedback_bot"

docker run -d --rm \
  -e "POSTGRES_USER=$POSTGRES_USER" \
  -e "POSTGRES_PASSWORD=$POSTGRES_PASSWORD" \
  -e "POSTGRES_DB=$POSTGRES_DB" \
  -p $db_port:5432 \
  $db_image

database_url="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${db_host}:${db_port}/${POSTGRES_DB}"
echo "Database URL: $database_url"
