# Development

For local development/debugging use `localhost:8000`.

Create venv:
```bash
python3 -m venv venv
```

Activate vevn and install requirements:
```bash
source venv/bin/activate
pip3 install -r requirements.txt
```

How to run app from terminal using venv on local machine during debugging:

```
cd src && python3 main.py
```

[comment]: <> (```bash)

[comment]: <> (uvicorn src.main:app --host localhost --port 8000)

[comment]: <> (```)

# Deployment

Agent uses application configuration from `config.json`. 

`entrypoint` field - full command that agent will execute in container spawned from dockerimage defined in field `dockerimage`.

`port` - deployment port (we recommend to use 8000 by default like in fastapi)
