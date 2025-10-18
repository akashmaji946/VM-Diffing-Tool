# Deployment

## Development (not for production)
```
cd frontend/server
python3 app.py
```

## Production (Gunicorn)
```
pip install gunicorn
cd frontend/server
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```
Place Gunicorn behind Nginx with HTTPS termination.

## Environment
- Copy `frontend/server/.env.sample` to `.env`
- Set strong secrets and proper file paths
