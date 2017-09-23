#!/bin/bash

if [ $# -eq 1 ]
then
	cd $1 
	cd AutoGrader 
	python manage.py dbbackup  
	python manage.py mediabackup 
elif [ $# -eq 2 ]
then
  	cd $1
	source bin/activate
	cd AutoGrader
	$1/bin/python manage.py dbbackup 
	$1/bin/python manage.py mediabackup 
else
	echo "Invalid command"
	echo ""
	echo "=== HELP ==="
	echo "Basic Usage"
	echo "backup.sh /home/autograder"
	echo ""
	echo "Using Virtualenv"
	echo "backup.sh /home/sys-autograder/autograder virtualenv" 
	
fi