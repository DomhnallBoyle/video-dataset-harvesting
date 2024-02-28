Requirements: 
- docker
- [docker-compose](https://docs.docker.com/compose/install/)

Run pipeline: 
```
TBD
```

Development:
```
# create containers from docker images
docker-compose up --no-start

# css watcher
sass --watch app/static/scss:app/static/css

# construct db - ensure db running and visible
export PYTHONPATH=app:$PYTHONPATH
python -c 'from main.utils.db import construct_db; construct_db(recreate=True)'

# start dataset server
export PYTHONPATH=app:$PYTHONPATH
python app/main/server.py

# start video server
python -m http.server 8001
```