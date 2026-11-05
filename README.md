# MangaShelf 📚

> Biblioteca pessoal de mangás: download e organização de capítulos em CBZ, leitura rápida pelo navegador e acesso pelo iPad.

## 1. Visão geral

O **MangaShelf** é um projeto *self-hosted* para organizar uma coleção pessoal de mangás e tornar a leitura mais confortável, rápida e consistente entre dispositivos.

A proposta é **não desenvolver um leitor do zero**. O projeto terá um **bot em Python** responsável por obter, validar e organizar arquivos `.cbz`, enquanto o **Komga** funcionará como servidor da biblioteca e leitor web.

O caso inicial é uma série com aproximadamente **350 capítulos disponíveis em CBZ**, mas a arquitetura deve permitir adicionar outras séries no futuro.

### Objetivos

- Baixar e organizar capítulos disponíveis para download, sem operações manuais repetitivas.
- Retomar downloads interrompidos e evitar arquivos duplicados.
- Validar integridade e sequência dos capítulos.
- Disponibilizar a coleção em um servidor local leve, via Komga.
- Ler pelo navegador no **PC (Fedora/Linux)** e no **iPad (Safari)**.
- Manter a experiência de biblioteca e o progresso de leitura centralizados no Komga, quando utilizado em ambos os dispositivos.
- Facilitar backups, manutenção e expansão para outras séries.

### Fora do escopo inicial

- Criar uma engine de leitura própria.
- Criar aplicativos nativos para iPad ou desktop.
- OCR, tradução automática ou alteração das páginas.
- Hospedar uma biblioteca pública ou redistribuir conteúdo.
- Contornar DRM, autenticação, paywalls ou mecanismos de proteção de sites.

## 2. Arquitetura proposta

```text
Fonte de capítulos (downloads autorizados)
                  |
                  v
       Bot Python (CLI)
       - descobre links
       - baixa CBZ
       - retoma falhas
       - verifica arquivos
       - organiza pastas
                  |
                  v
      Biblioteca local (CBZ)
                  |
                  v
          Komga (Docker)
          - indexa séries
          - serve biblioteca
          - leitor web
          - progresso de leitura
                  |
          +-------+--------+
          |                |
          v                v
     PC / Firefox     iPad / Safari
          |                |
          +---- rede local -+
                  |
       Acesso remoto opcional
        (VPN: Tailscale etc.)
```

### Responsabilidades

| Componente | Responsabilidade |
| --- | --- |
| **Bot Python** | Descobrir capítulos a partir de fonte configurada, baixar, verificar e organizar CBZ. |
| **Biblioteca local** | Preservar arquivos com nomes e diretórios estáveis. |
| **Komga** | Indexação, catálogo, leitura no navegador e estado de leitura. |
| **Docker Compose** | Executar e persistir o servidor Komga. |
| **iPad / PC** | Consumir a biblioteca via navegador, sem copiar todos os CBZ para cada dispositivo. |

> **Princípio de design:** o bot não deve depender do banco de dados interno do Komga. A integração ocorre por meio dos arquivos salvos na pasta que o Komga indexa.

## 3. Stack inicial

- **Linguagem do bot:** Python 3.12+.
- **Execução do servidor:** Docker + Docker Compose.
- **Biblioteca e leitor:** [Komga](https://komga.org/).
- **Formatos:** arquivos `.cbz` (arquivos ZIP com imagens ordenadas).
- **Acesso:** navegador web; Safari no iPad e Firefox/Zen no PC.
- **Acesso remoto (opcional):** Tailscale ou outra VPN privada.
- **Persistência do bot:** manifesto JSON ou SQLite para registrar downloads e estado de execução; definir durante o MVP.
- **HTTP no bot:** `httpx` ou `requests`, conforme a necessidade da fonte.

A escolha de uma ferramenta de automação de navegador (como Playwright) deve ocorrer **somente se downloads HTTP diretos não forem suficientes** e se o uso for permitido pela fonte.

## 4. Funcionalidades do bot

### MVP — essenciais

1. **Fonte configurável:** informar URL base, pasta de destino e configurações de download, sem gravar esses valores diretamente no código.
2. **Descoberta de capítulos:** identificar os capítulos e seus links de download, conforme as páginas disponibilizadas pela fonte.
3. **Download em lote:** baixar os capítulos solicitados, com concorrência baixa e configurável.
4. **Retomada:** continuar a execução sem baixar novamente arquivos completos e válidos.
5. **Integridade:** verificar se cada CBZ é um ZIP legível, contém imagens e não está vazio.
6. **Ordenação:** preservar a ordem de capítulos, inclusive números decimais ou especiais quando aplicável.
7. **Registro de resultados:** manter logs e um relatório de sucessos, erros e capítulos pendentes.
8. **Execução segura:** usar timeouts, tentativas com espera progressiva e gravação temporária antes de mover o arquivo para a biblioteca.

### Melhorias futuras

- Atualização incremental para detectar novos capítulos.
- Suporte a múltiplas fontes por meio de adaptadores (`sources/`).
- Verificação mais detalhada de nomes/ordem de imagens dentro do CBZ.
- Re-download seletivo de arquivos inválidos.
- Interface web simples para gerenciar tarefas, se o CLI se tornar insuficiente.
- Rotina agendada de atualizações.

### Comportamento esperado

- Se o capítulo já existir **e for válido**, ignorar o download.
- Se um arquivo estiver incompleto ou corrompido, registrar o problema e permitir nova tentativa.
- Nunca sobrescrever silenciosamente um arquivo válido.
- Usar `.part` ou outro nome temporário enquanto o download não termina.
- Respeitar limites de taxa, termos de uso e direitos de acesso da fonte.

## 5. Estrutura de diretórios sugerida

```text
mangashelf/
├── README.md
├── .env.example
├── .gitignore
├── compose.yaml
├── config/
│   └── sources.example.yaml
├── bot/
│   ├── pyproject.toml
│   ├── src/
│   │   └── mangashelf/
│   │       ├── cli.py
│   │       ├── config.py
│   │       ├── downloader.py
│   │       ├── archive.py
│   │       ├── library.py
│   │       ├── state.py
│   │       └── sources/
│   │           ├── base.py
│   │           └── example.py
│   └── tests/
├── data/                   # não versionar
│   ├── library/
│   │   └── Nome da Série/
│   │       ├── Capitulo_001.cbz
│   │       ├── Capitulo_002.cbz
│   │       └── Capitulo_003.cbz
│   ├── downloads/         # temporários
│   ├── state/             # manifesto / SQLite
│   └── komga/             # configuração persistente
└── logs/                   # não versionar
```

**Observação:** `data/`, `logs/`, credenciais, cookies e `.env` não devem entrar no Git.

## 6. Komga com Docker Compose

Arquivo `compose.yaml` sugerido para o desenvolvimento local:

```yaml
services:
  komga:
    image: gotson/komga:latest
    container_name: mangashelf-komga
    user: "${PUID:-1000}:${PGID:-1000}"
    ports:
      - "25600:25600"
    volumes:
      - ./data/komga:/config
      - ./data/library:/data:ro
    environment:
      - TZ=America/Sao_Paulo
    restart: unless-stopped
```

> O mapeamento `:ro` evita que o servidor de leitura modifique acidentalmente os CBZ. Caso alguma função futura exija escrita na biblioteca, revisar essa decisão conscientemente.

### Inicialização prevista

```bash
mkdir -p data/komga data/library data/downloads data/state logs
docker compose up -d
```

Acessar `http://localhost:25600`, concluir a configuração inicial e cadastrar `/data` como pasta da biblioteca no Komga.

**Atenção:** confira `id -u` e `id -g` no Fedora e ajuste `PUID` e `PGID` se necessário. A pasta montada precisa ter permissões adequadas para leitura.

## 7. Experiência de leitura

### No PC

1. Acessar o Komga pelo navegador em `http://localhost:25600`.
2. Escolher série e capítulo.
3. Ler sem depender da interface do site de origem.

### No iPad — mesma rede Wi-Fi

1. Descobrir o IP local do computador que hospeda o Komga.
2. Abrir no Safari `http://IP_DO_PC:25600`.
3. Entrar com a conta configurada no Komga.
4. Selecionar a série e ler pelo navegador.

O computador servidor deve estar **ligado e acessível na rede**. O firewall do Fedora também deve permitir a porta escolhida apenas nas redes desejadas.

### Fora de casa — opcional

Usar VPN privada, por exemplo Tailscale, instalada nos dispositivos compatíveis, para acessar o servidor com autenticação de rede. **Não publicar a porta 25600 diretamente na internet.**

### Leitura offline

O MVP é voltado a leitura com conexão ao servidor. Leitura offline no iPad exigirá uma etapa adicional, como baixar arquivos permitidos para um leitor local ou integrar um aplicativo compatível com Komga. **Não considerar sincronização offline automática como funcionalidade garantida do MVP.**

## 8. Interface de linha de comando desejada

Os comandos abaixo definem **comportamento planejado**; ainda precisam ser implementados:

```bash
# Inspeciona a fonte e lista os capítulos encontrados
mangashelf discover --source minha-fonte --series minha-serie

# Baixa uma série, retomando os downloads já concluídos
mangashelf download --source minha-fonte --series minha-serie

# Baixa um intervalo específico
mangashelf download --source minha-fonte --series minha-serie --from 1 --to 50

# Valida os CBZ já presentes
mangashelf verify --series minha-serie

# Mostra um resumo do estado
mangashelf status --series minha-serie
```

## 9. Etapas de desenvolvimento

### Fase 1 — infraestrutura e leitura

- [ ] Criar estrutura do repositório e `.gitignore`.
- [ ] Configurar Komga no Compose.
- [ ] Adicionar manualmente 1–2 CBZ para teste.
- [ ] Verificar leitura no Fedora.
- [ ] Verificar leitura no Safari do iPad, pela rede local.
- [ ] Confirmar progresso compartilhado ao usar a mesma conta do Komga.

**Entrega:** biblioteca funcional sem bot.

### Fase 2 — prova de conceito do downloader

- [ ] Analisar como a fonte disponibiliza os arquivos e o que ela permite.
- [ ] Implementar adaptador específico para a fonte.
- [ ] Descobrir links e metadados de capítulos.
- [ ] Baixar 3–5 capítulos para teste, com limites conservadores.
- [ ] Validar e ordenar os CBZ corretamente.

**Entrega:** downloader confiável para poucos capítulos.

### Fase 3 — download completo

- [ ] Implementar manifesto de estado e retomada.
- [ ] Adicionar tratamento de falhas, logs e tentativas.
- [ ] Testar reinício no meio do download.
- [ ] Executar lote completo dos ~350 capítulos.
- [ ] Auditar capítulos ausentes, duplicados e arquivos inválidos.
- [ ] Confirmar que o Komga indexou a coleção.

**Entrega:** coleção inicial completa e navegável.

### Fase 4 — manutenção e melhorias

- [ ] Atualizações incrementais.
- [ ] Backup da biblioteca e das configurações do Komga.
- [ ] Acesso remoto por VPN, se necessário.
- [ ] Suporte a novas fontes e séries.
- [ ] Avaliar leitura offline no iPad.

## 10. Critérios de sucesso do MVP

O MVP será considerado pronto quando:

- O Komga estiver funcionando no Fedora via Docker Compose.
- Um CBZ de teste abrir corretamente tanto no PC quanto no iPad.
- O bot conseguir descobrir e baixar os capítulos disponibilizados pela fonte selecionada, dentro das permissões de acesso.
- A execução puder ser interrompida e retomada sem repetir downloads válidos.
- A biblioteca estiver organizada em ordem correta e sem arquivos corrompidos conhecidos.
- O leitor disponibilizar a coleção sem depender do site de origem durante a leitura.

## 11. Cuidados de segurança e uso

- Baixar somente conteúdo ao qual o usuário tenha direito de acesso e conforme os termos da fonte.
- Não implementar bypass de DRM, paywall, CAPTCHA ou controles de acesso.
- Evitar sobrecarregar o servidor de origem: limitar concorrência, aplicar *backoff* e respeitar respostas de erro (`429`, `503` etc.).
- Não guardar segredos em commits, logs ou arquivos de exemplo.
- Proteger o Komga por autenticação e manter os componentes atualizados.
- Preferir VPN privada para acesso remoto, em vez de expor o serviço diretamente.
- Fazer backup de `data/library` e `data/komga` separadamente.

## 12. Primeiras decisões pendentes

Antes de implementar o downloader, definir:

1. **Fonte inicial:** qual site oferece os downloads de CBZ e como os links são apresentados?
2. **Padrão de capítulos:** numeração simples, decimal, volumes ou extras?
3. **Estado do bot:** JSON para protótipo ou SQLite desde o início?
4. **Instalação:** bot como CLI local ou segundo serviço Docker?
5. **Armazenamento:** em qual unidade e diretório manter a biblioteca?

**Recomendação:** começar pela Fase 1. Validar a leitura no iPad com dois CBZ antes de investir tempo no bot. Depois, implementar um único adaptador de fonte e expandir gradualmente.

---

**Status:** proposta / planejamento — implementação ainda não iniciada.
