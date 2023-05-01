# TG Group Manager

## .env

```python
API_HASH=
API_ID=
BOT_LOG=
BOT_ID=
BOT_NAME=""
BOT_TOKEN=
ADMIN_GROUP=

```

## Docker run

```
git clone https://github.com/kohfuchs/telegram_group_manager.git
cd telegram_group_manager/
vim .env
```

```
docker build -t tg_group_manager .
docker run --env-file .env --name tg_group_manager -d -v ./db:/db tg_group_manager
```x