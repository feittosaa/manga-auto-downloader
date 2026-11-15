# MAD — Manga Auto Downloader

**MAD (Manga Auto Downloader)** é uma solução *self-hosted* para download, organização e gerenciamento de uma biblioteca pessoal de mangás.

O projeto utiliza um bot em Python para baixar, validar e organizar capítulos em arquivos `.cbz`, enquanto o [Komga](https://komga.org/) disponibiliza a coleção para leitura pelo navegador, seja no PC, tablet ou iPad.

O MAD **não possui um leitor próprio**. Seu objetivo é automatizar o gerenciamento dos arquivos, deixando o catálogo, a leitura e o acompanhamento do progresso sob responsabilidade do Komga.

## Como funciona

```text
Fonte configurada → MAD (Python CLI) → Biblioteca local (CBZ) → Komga → Navegador
```

- **MAD:** Descobre capítulos, realiza downloads temporários em arquivos `.part`, valida os arquivos CBZ e os organiza na biblioteca. Permite retomar downloads interrompidos sem sobrescrever arquivos válidos.
- **Komga:** Indexa a biblioteca em modo somente leitura, disponibiliza os mangás pelo navegador e gerencia o progresso de leitura.
- **Integração:** A comunicação entre MAD e Komga ocorre pela biblioteca de arquivos, sem dependência direta do banco de dados do Komga.

## Requisitos

- Python 3.12+
- Docker e Docker Compose

## Instalação

### 1. Iniciar o Komga

```bash
cp .env.example .env
mkdir -p data/komga data/library data/downloads data/state logs
docker compose up -d
```

Configure `PUID` e `PGID` no arquivo `.env` utilizando os valores retornados por `id -u` e `id -g`.

Acesse `http://localhost:25600`, crie uma conta de administrador e adicione `/data` como diretório da biblioteca.

> Para armazenar os mangás em outro disco, mova `data/library` para o local desejado e crie um link simbólico apontando para ele.

### 2. Instalar o MAD

```bash
python3 -m venv .venv
.venv/bin/pip install -e 'bot[dev]'
.venv/bin/pytest bot
```

### 3. Configurar as fontes

```bash
cp config/sources.example.yaml config/sources.yaml
```

Edite `config/sources.yaml` para definir as fontes, os diretórios e os limites de download.

O arquivo de configuração não é versionado.

## Comandos

```bash
# Descobrir capítulos disponíveis
mad discover --source <fonte> --series <serie>

# Baixar capítulos
mad download --source <fonte> --series <serie> [--from N --to M]

# Validar arquivos e identificar capítulos ausentes
mad verify --series "Nome da Série"

# Consultar o estado dos downloads
mad status --series <serie>
```

Os downloads podem ser retomados automaticamente após interrupções.

Após adicionar novos arquivos à biblioteca, execute uma verificação dos arquivos pelo Komga para atualizar o catálogo.

## Organização da biblioteca

```text
data/library/
└── Nome da Série/
    ├── Capitulo_001.cbz
    ├── Capitulo_002.cbz
    └── Capitulo_010.5.cbz
```

O MAD suporta capítulos numerados, incluindo numerações decimais.

## Estrutura do projeto

```text
compose.yaml
config/
bot/
└── src/
    └── mad/
        ├── cli.py
        ├── downloader.py
        ├── archive.py
        ├── library.py
        ├── state.py
        └── sources/
```

| Componente | Responsabilidade |
|---|---|
| `compose.yaml` | Configuração do Komga via Docker Compose |
| `config/` | Configurações e exemplos de fontes |
| `cli.py` | Interface de linha de comando |
| `downloader.py` | Downloads, retentativas e controle de falhas |
| `archive.py` | Validação dos arquivos CBZ |
| `library.py` | Organização, nomenclatura e identificação de capítulos ausentes |
| `state.py` | Persistência do estado em SQLite |
| `sources/` | Adaptadores para diferentes fontes |

## Adaptadores de fontes

O MAD utiliza uma arquitetura extensível que permite adicionar diferentes fontes de download.

Cada adaptador implementa o método:

```python
discover(series) -> list[Chapter]
```

O método retorna os capítulos disponíveis e suas respectivas URLs. Novos adaptadores devem ser registrados em `sources/__init__.py`.

As funcionalidades de download, validação, organização e persistência são compartilhadas entre os adaptadores.

## Acesso remoto

A biblioteca pode ser acessada por outros dispositivos utilizando o Komga.

Para acesso fora da rede local, recomenda-se uma VPN privada, como [Tailscale](https://tailscale.com/) ou [ZeroTier](https://www.zerotier.com/).

**Não é recomendado expor diretamente a porta 25600 à internet.**

## Uso responsável

O MAD é uma ferramenta destinada à automação e organização de bibliotecas pessoais.

Utilize o projeto apenas com conteúdos que você possui autorização para acessar e armazenar, respeitando os direitos autorais e os termos de uso das fontes.

O projeto utiliza limites de concorrência, intervalos entre downloads e mecanismos de *backoff*. Não implementa mecanismos para contornar DRM, paywalls, CAPTCHAs ou outras restrições de acesso.

Nenhum conteúdo é fornecido ou hospedado pelos autores.

## Status do projeto

**MVP funcional**, incluindo:

- Integração com Komga via Docker.
- Download automatizado e retomável.
- Validação e organização de arquivos CBZ.
- Persistência de estado em SQLite.
- Interface de linha de comando.
- Suporte a múltiplas fontes por adaptadores.

### Melhorias planejadas

- Atualização incremental de capítulos.
- Importação de arquivos locais.
- Backup automatizado da biblioteca.
- Sincronização e atualização automática do catálogo Komga.
