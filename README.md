### aria2bot
---

如何使用

docker-compose.yml

```
version: '3'
services:
  onebot:
    image: taohuajiu/ariabottu:latest
    container_name: ariabota
    environment:
      - bot_token=6485084788*******eXKJIOmacMA
      - aria2c_rpc_url = "http://mc*****/jsonrpc"
      - aria2c_rpc_key = "ta*****0"
    volumes:
      - /dockerapp/aria2bot:/ariabot
```

docker-compose up -d
