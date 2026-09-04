# Diretrizes do repositório

## Comandos de desenvolvimento

- `uv sync --dev` — instala o ambiente e as ferramentas travadas em `uv.lock`.
- `uv run uvicorn app:app --reload --env-file .env` — inicia a API local; a documentação fica em `/api/docs`.
- Para testar o painel em um Android conectado por USB, confirme o aparelho com `adb devices -l`, execute `adb reverse tcp:8000 tcp:8000` e abra `http://localhost:8000/admin` no celular. O `adb` deve estar no `PATH`; nesta máquina, o fallback é `C:\Users\Administrador\AppData\Local\Microsoft\WinGet\Packages\Google.PlatformTools_Microsoft.Winget.Source_8wekyb3d8bbwe\platform-tools\adb.exe`.
- `uv run pytest` — executa a suíte unitária e de contrato.
- `uv run pytest tests/e2e` — executa E2E; requer `uv run playwright install chromium` previamente.
- Ao terminar os testes, o `tests/conftest.py` remove `.pytest_cache`, `.pytest-tmp-unit` e `.pytest-tmp-*`; não mantenha esses artefatos no workspace.
- Validação: `uv run ruff check .`, `uv run ruff format --check .` e `uv run ty check`.

O `TOKEN_JWT` já está configurado em `.env`; mantenha o arquivo fora do versionamento e nunca versione credenciais ou hashes reais.

## Regras de design

- Leia `ARCHITECTURE.md` antes de adicionar ou reorganizar funcionalidades; atualize-o se mudar responsabilidades, fluxo, fronteiras de persistência ou o padrão de feature.
- Para mudanças em `static/admin/`, leia `DESIGN.md` e mantenha tokens semânticos, acessibilidade, foco, responsividade e animações reduzidas; altere `DESIGN.md` junto com novos tokens CSS.
- Se um ajuste visual não produzir o efeito esperado, pare de acumular tentativas locais e pesquise referências técnicas confiáveis antes de propor outra alteração; registre a regra resultante em `DESIGN.md` quando ela for específica da interface.
- Mantenha handlers finos e lance `HTTPException` apenas na fronteira HTTP; regras e acesso a dados ficam nos módulos apropriados.

## Armadilhas e pontos de atenção

### Configuração e persistência

- Resolva os caminhos `DATABASE_PATH`, `SCHEDULE_PATH`, `LOCATIONS_PATH` e `KNOWLEDGE_AXES_PATH` em tempo de chamada, nunca em cache de import; isso permite isolamento dos testes e deployments.
- JSON é persistido atomicamente com arquivo temporário, `fsync` e `os.replace`; converta falhas de filesystem em `PersistenceError` nos repositórios.
- Renomear um local também altera as sessões da agenda; se a segunda gravação falhar, restaure o catálogo de locais.

### Integridade dos catálogos

- Valide referências da agenda antes de salvar; `null` para local ou eixo é válido.
- Renomear eixo preserva seu ID e não reescreve referências da agenda. Não exclua local/eixo referenciado: retorne conflito com as atividades afetadas.
- Nomes são comparados após normalização Unicode, espaços e caixa; duplicatas equivalentes devem ser rejeitadas.

### Painel e segurança

- `/admin` entrega somente o shell público; o navegador valida o JWT antes de buscar os catálogos protegidos em `/admin/api/*`.
- Dados de usuários e hashes são sensíveis. Não embuta catálogos ou credenciais no HTML inicial nem em fixtures versionadas.

## Convenções

- Use `uv` para ambiente e comandos, quatro espaços, type hints públicos e o limite de 100 caracteres configurado no Ruff.
- Toda documentação Markdown de orientação do agente deve usar exclusivamente português. Preserve em outros idiomas apenas nomes técnicos, identificadores de código, comandos, URLs, citações e textos que precisem corresponder literalmente à interface.
- Commits devem ser curtos, imperativos e em português. PRs devem listar validações e destacar alterações de ambiente ou formato de dados.
