# Moffat Intel
## Introduction
This is a project that provides end-to-end solutions for Construction Management and other related professions to create projects, accept bids, budget for plans, and track bank draws.

## Setup
1. Clone the repository
2. Install the dependencies
   1. Navigate to the root directory of the project
   2. run `python venv venv`
   3. run `source venv/bin/activate`
   4. run `pip install -r requirements.txt`
3. Once everything is installed, navigate to /MoffatIntel/MoffatIntel and run `python manage.py runserver`
   1. If there are database issues, run `python manage.py makemigrations` and `python manage.py migrate` before running the server
4. If this is your first time running the server, you'll need to create a superuser to access the admin panel
   1. run `python manage.py createsuperuser`
   2. Follow the prompts to create a superuser
   3. Navigate to `localhost:8000/admin` and login with the superuser credentials
   4. You can now create new users, projects, bids, etc. from the admin panel
5. To access the main site, navigate to `localhost:8000/projectmanagement`
6. Use your superuser credentials or other credentials created in the admin panel to login