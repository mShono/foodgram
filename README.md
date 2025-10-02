# foodgram

## About the project
The Foodgram project is a website where users can publish their own recipes, add other users’ recipes to favorites, and subscribe to other authors’ posts. Registered users also have access to a Shopping List service — it allows creating lists of ingredients needed to cook selected dishes.

The project is implemented with Django Rest Framework.

## Preparing the foodgram project to run
For local launch you will need:
- Docker
- git

1. Clone the repository and open it in your terminal:
```
git clone https://github.com/mShono/foodgram
cd foodgram
```
2. Create a .env file in the project root and fill it with the following environment variables:
POSTGRES_USER=<postgres_user>            # PostgreSQL username
POSTGRES_PASSWORD=<postgres_password>    # PostgreSQL password
POSTGRES_DB=<database_name>              # Database name
DB_HOST=db                               # Database host (default: 'db')
DB_PORT=5432                             # PostgreSQL port
SECRET_KEY=<your_django_secret_key>      # Django SECRET_KEY
DEBUG=True                               # Debug mode (True/False)
ALLOWED_HOSTS=127.0.0.1,localhost        # Allowed hosts
3. From the infra directory run:
```
docker compose up --build.
```

## Containers
- ### db (PostgreSQL):
stores application data.
Image: postgres:13.10.

- ### backend (Django backend):
The main Django application with business logic.
Image: masher88/foodgram-back:latest.

- ### frontend (React frontend):
Serves the frontend static files.
Image: infra-frontend:latest.

- ### nginx (Reverse Proxy):
Handles requests and serves static files.
Image: nginx:1.25.4-alpine.

## After containers are up
- The main web application will be available at: http://localhost
- API specification (docs) is available at: http://localhost/api/docs/
- API endpoints are available under: http://localhost/api/
- Admin site is available at: http://localhost/admin/
