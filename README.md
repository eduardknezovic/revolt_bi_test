
# Setup

```
docker-compose up --build -d
```

Database migration migration will be executed on build

# Testing

Once the docker container is up:

```
docker-compose exec web /bin/bash
python manage.py test
```

