# MangaShelf 📚

Biblioteca pessoal de mangás *self-hosted*: um bot em Python organiza arquivos `.cbz` e o [Komga](https://komga.org/) serve a coleção para leitura no navegador, no PC ou no iPad.

O projeto **não tem leitor próprio**. Ele cuida da parte de arquivos (baixar, validar, nomear, organizar) e deixa catálogo, leitura e progresso para o Komga.

## Como funciona

```text
Fonte configurada ──► Bot Python (CLI) ──► Biblioteca local (CBZ) ──► Komga ──► Navegador (PC / iPad)
```

- **Bot:** descobre capítulos, baixa para um arquivo `.part`, valida o CBZ e só então move para a biblioteca. Retoma de onde parou e nunca sobrescreve um arquivo válido.
- **Komga:** indexa a pasta da biblioteca (somente leitura) e guarda o progresso de leitura.
- O bot não depende do banco de dados do Komga: a integração é só pela pasta de arquivos.

## Requisitos

- Python 3.12+
- Docker e Docker Compose

## Início rápido

### 1. Subir o Komga

```bash
cp .env.example .env          # ajuste PUID/PGID com `id -u` e `id -g`
mkdir -p data/komga data/library data/downloads data/state logs
docker compose up -d
```

Abra `http://localhost:25600`, crie a conta de administrador e adicione `/data` como pasta da biblioteca.

> Para guardar a biblioteca em outro disco, mova `data/library` para lá e deixe um link simbólico no lugar.

### 2. Instalar o bot

```bash
python3 -m venv .venv
.venv/bin/pip install -e 'bot[dev]'
.venv/bin/pytest bot
```

### 3. Configurar uma fonte

```bash
cp config/sources.example.yaml config/sources.yaml   # não é versionado
```

Edite o arquivo com a URL base, as pastas e os limites de download.

## Comandos

```bash
mangashelf discover --source <fonte> --series <serie>                 # lista capítulos
mangashelf download --source <fonte> --series <serie> [--from N --to M]  # baixa (retoma sozinho)
mangashelf verify   --series "Nome da Série"                          # valida CBZ e acha lacunas
mangashelf status   --series <serie>                                  # resumo do estado
```

Depois de baixar, peça ao Komga para **escanear os arquivos da biblioteca** (o Komga não detecta arquivos novos sozinho).

## Organização da biblioteca

```text
data/library/Nome da Série/
├── Capitulo_001.cbz
├── Capitulo_002.cbz
└── Capitulo_010.5.cbz      # capítulos decimais são suportados
```

## Estrutura do repositório

```text
compose.yaml               Komga via Docker Compose
config/                    exemplo de configuração das fontes
bot/src/mangashelf/
├── cli.py                 comandos
├── downloader.py          download com .part, retentativas e backoff
├── archive.py             validação de CBZ
├── library.py             nomes, ordenação e lacunas
├── state.py               estado em SQLite
└── sources/               adaptadores de fonte (base.py define o contrato)
```

## Escrevendo um adaptador de fonte

Um adaptador implementa `discover(series) -> list[Chapter]`, retornando o número e a URL de download de cada capítulo, e é registrado em `sources/__init__.py`. O restante (download, validação, estado, CLI) é reaproveitado.

## Acesso remoto

Use uma VPN privada (por exemplo Tailscale). **Não exponha a porta 25600 diretamente na internet.**

## Uso responsável

Este projeto é uma ferramenta de organização de arquivos. Use-o **somente com conteúdo que você tem direito de acessar e armazenar** e respeitando os termos de cada fonte. O bot usa concorrência baixa, pausas entre downloads e *backoff*, e não contorna DRM, paywalls, CAPTCHAs ou qualquer controle de acesso. Os autores não fornecem nem hospedam conteúdo.

## Status

MVP funcional: Komga em Docker, CLI com download retomável, validação e estado. Ideias futuras: atualização incremental, comando `import` para arquivos locais, backup e rescan automático do Komga.
