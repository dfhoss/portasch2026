# ADR: Montar `db/` do workspace no Docker

## Status

Aceita.

## Contexto

O Compose usava um volume nomeado em `/app/db`. Quando o volume foi criado antes
da inclusão de `settings.json`, ele passou a ocultar o catálogo presente na imagem.
O site público então recebia `404` em `/db/settings.json` e não renderizava a agenda.

## Decisão

O serviço `app` monta `./db:/app/db` no `docker-compose.yml`. A imagem continua
incluindo os catálogos no build, mas o ambiente Compose usa explicitamente a pasta
`db/` do workspace como fonte persistente.

## Consequências

- Recriar a imagem preserva os JSONs já existentes no workspace.
- Alterações feitas pelo painel aparecem diretamente nos arquivos de `db/`.
- A pasta `db/` precisa ser preservada e ter permissões de leitura e escrita para o
  processo do container.
- A persistência deixa de ser isolada pelo Docker; backups e proteção dos dados ficam
  sob responsabilidade do ambiente que contém o workspace.
