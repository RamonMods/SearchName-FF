<div align="center">

<img src="public/assets/favicon.svg" width="96" alt="SearchName-FF">

# SearchName-FF

Encontre o UID de um jogador de Free Fire pelo nickname, direto no navegador.

[![GitHub Pages](https://img.shields.io/badge/Pages-ramonmods.github.io%2FSearchName--FF-111111?style=for-the-badge&logo=github&logoColor=white)](https://ramonmods.github.io/SearchName-FF/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](#)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=for-the-badge&logo=flask&logoColor=white)](#)

<br>
<a href="https://pixgg.com/ramon"><img src="https://img.shields.io/badge/Pix-pixgg.com%2Framon-32BCAD?style=for-the-badge&logo=pix&logoColor=white" alt="Apoiar o projeto" /></a>
</div>

---

## Sobre

O SearchName-FF busca jogadores de Free Fire pelo nickname e devolve o UID de
cada conta que combina com o nome, na região escolhida. A consulta usa o mesmo
servidor de jogo que o app oficial usa. Não pede login, senha, token nem
credencial de terceiro — só o nickname e a região.

O site é estático (HTML/CSS/JS puro, fontes self-hosted) e a busca é feita pela
API Flask no mesmo serviço. Não armazena nada: o resultado fica em cache na
memória por 2 minutos e não é gravado em banco.

## Recursos

- **Busca por nome**: nickname completo ou parcial, de 3 a 32 caracteres.
- **Filtro por região**: BR, US, NA, SAC, IND, ME, ID, TH, SG, PK e outras.
- **UID de cada conta**: a lista mostra nickname e UID lado a lado, com botão de copiar.
- **Sem cadastro**: nenhum login, senha ou dado pessoal é solicitado.
- **Rate limit**: 20 buscas por minuto por IP.
- **Cache**: 2 minutos por consulta para não sobrecarregar o servidor.
- **Multiplataforma**: funciona em qualquer navegador (celular ou desktop).

## Como funciona

1. Você informa o nickname e a região.
2. A API monta uma sessão de consulta e faz login no servidor de jogo da Garena.
3. A busca (`FuzzySearchAccountByName`) devolve as contas que combinam com o nome.
4. O resultado aparece na tela: nickname, UID e tempo de resposta.

### Endpoints

| Rota | Descrição |
|---|---|
| `GET /search?name=Deus&server_name=BR` | Busca por nickname |
| `GET /regions` | Lista as regiões suportadas |
| `GET /healthz` | Health check do Render |

## Site

Acesse: **https://ramonmods.github.io/SearchName-FF/**

## Estrutura

```
public/                 site estático (servido pelo próprio Flask) + PWA
  index.html            landing
  search/               ferramenta de busca por nickname
  assets/               favicon, preview, fontes woff2
  manifest.json         manifesto PWA (instalável no celular)
  sw.js                 service worker (cache offline)
core/
  garena.py             cliente do servidor de jogo: sessão, login e busca
  __init__.py
api/
  app.py                Flask: site + busca, CORS, cache, rate limit
  requirements.txt
.github/
  workflows/pages.yml   deploy do site no GitHub Pages
  FUNDING.yml           apoio via Pix (pixgg.com/ramon)
render.yaml             serviço único no Render
```

## Rodar localmente

```bash
pip install -r api/requirements.txt
python api/app.py
# http://127.0.0.1:5000
```

## Apoio

Se o projeto te ajudou, apoie via Pix:

**https://pixgg.com/ramon**

---

<div align="center">
<sub>SearchName-FF é um projeto independente, não afiliado nem endossado pela Garena.</sub>
</div>
