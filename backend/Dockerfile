FROM python:3.9

WORKDIR /app

RUN pip install gunicorn==20.1.0 

COPY requirements_backend.txt ../requirements

RUN pip install -r ../requirements/requirements_backend.txt --no-cache-dir

COPY . .

RUN chmod +x commands.sh

CMD ["bash", "./commands.sh"]
