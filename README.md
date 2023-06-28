# goals
[![codecov](https://codecov.io/gh/Taller-2-FIUBA/goals/branch/main/graph/badge.svg?token=bewfhNDORY)](https://codecov.io/gh/Taller-2-FIUBA/goals)

Service for interacting with user goals.
Keep in mind this service requires the authentication service to function correctly.

```bash
sudo apt install python3.11 python3.11-venv
python3.11 -m venv venv
source venv/bin/activate
pip install pip --upgrade
pip install -r requirements.txt -r dev-requirements.txt
```

## Tests

```bash
tox
```

## Docker

You'll need a postgres image, and you can build your own for the app.

```
docker pull postgres
docker build --tag IMAGE_NAME .
```

Where `IMAGE_NAME` is a name to identify the image later.

Then run:

```
docker network create NETWORK_NAME
docker run --rm --name goals_db --network NETWORK_NAME -e PGUSER=POSTGRES_USERNAME -e POSTGRES_PASSWORD=POSTGRES_PASSWORD
postgres
docker run --rm -p 8004:8004 --network NETWORK_NAME --name CONTAINER_NAME IMAGE_NAME
```

Where `IMAGE_NAME` is the name chosen in the previous step, `CONTAINER_NAME`
is a name to identify the container running the app and `NETWORK_NAME` is the name chosen
for the network connecting the containers. `POSTGRES_USERNAME` and `POSTGRES_PASSWORD`
are self-explanatory.

Notice `--rm` tells docker to remove the container after exists, and
`-p 8004:8004` maps the port 8004 in the container to the port 8004 in the host.
App port can be set up in Dockerfile, other configuration options available in config file.
