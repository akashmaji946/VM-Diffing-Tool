# Docker

### Build image
```
docker build -t vmtool:latest -f docker/Dockerfile .
```

### Run container
```
docker run -d \
  --name VMT-Docker \
  --privileged \
  --device /dev/kvm:/dev/kvm \
  -p 8000:8000 \
  -v $HOME:$HOME:ro \
  -v $(pwd)/frontend/server/database:/app/frontend/server/database \
  vmtool:latest
```

### Check logs or exec
```
docker logs -f VMT-Docker
docker exec -it VMT-Docker /bin/bash
```

### Stop container
```
docker stop VMT-Docker
docker rm VMT-Docker
docker rmi vmtool:latest
```

### Compose (optional)
See `docker/docker-compose.yml` if you prefer docker-compose.

```bash
cd docker
docker-compose up -d
docker logs -f VMT-Docker
docker-compose down
```

### Environment
- Copy `frontend/server/.env.sample` to `.env`
- Set strong secrets and proper file paths
- Set `MAIL_SERVER` to `smtp.gmail.com` if using Gmail
- Set `MAIL_PORT` to `587` if using Gmail
- Set `MAIL_USE_TLS` to `True` if using Gmail
- Set `MAIL_USERNAME` to your Gmail address
- Set `MAIL_PASSWORD` to your Gmail app password
- Set `MAIL_DEFAULT_SENDER` to your Gmail address
- Set `MAIL_USE_SSL` to `False` if using Gmail
- Set `MAIL_DEBUG` to `True` if using Gmail

