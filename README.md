# Breeze [![Build Status](https://travis-ci.org/TDT4140-Breeze/Breeze.svg?branch=master)](https://travis-ci.org/TDT4140-Breeze/Breeze)

## Installation
- Clone repository from Github
- Install requirements outlined in requirements.txt with ```pip install -r requirements.txt```
- Run 'python manage.py makemigrations' and 'python manage.py migrate'
- Start the redis server
- Start the Django server with 'python manage.py runserver'
- Breeze is now running on your localhost

## Preferred workflow
1. Create feature branch from development
1. Do work on feature branch
1. Merge feature branch back into development with `git merge --no-ff branch-name`
1. When code in development branch is deemed production ready, it can be merged into master
