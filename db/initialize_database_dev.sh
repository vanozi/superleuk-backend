#! /bin/sh
# Create databases
psql -c "CREATE DATABASE dev;"
# psql -U postgres -d dev -a -f ./sql_files/setup_testdata.sql