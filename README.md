# Wintersweet

[![API Documentation](https://img.shields.io/badge/OpenAPi%20v3-API%20Docs-8bbf04)](https://app.swaggerhub.com/apis-docs/outloudvi/project_polya_server/1.1.1) [![OpenAPI validation badge](https://img.shields.io/swagger/valid/3.0?label=scheme&specUrl=https%3A%2F%2Fraw.githubusercontent.com%2Foutloudvi%2Fpolya-server%2Fmaster%2Fapi.yaml)](https://github.com/outloudvi/polya-server/blob/master/api.yaml)

Server side for Project Polya.

```
gunicorn -w 1 polyaserver.main:api --reload
```