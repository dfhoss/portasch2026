# Cadastro de participantes e instituições

## Objetivo

Adicionar à API e ao painel administrativo o cadastro de participantes do evento e o
catálogo independente de instituições de ensino, sem introduzir banco de dados.
Todos os endpoints exigem um JWT válido e seguem as fronteiras atuais de rotas,
modelos Pydantic e clients de persistência JSON.

## Escopo

### Incluído

- CRUD completo de instituições em `/institutions`.
- CRUD completo de participantes em `/participants`.
- Arquivos JSON independentes para cada recurso.
- Referência de cada participante a uma instituição por `institutionId`.
- Validação de nomes, campos obrigatórios, referências e conflitos de exclusão.
- Testes de contrato HTTP, autenticação, persistência e integridade entre recursos.
- Página administrativa protegida para o CRUD de instituições e participantes.

### Fora de escopo

- Cadastro público sem autenticação.
- Login, perfis ou permissões adicionais além do JWT existente.
- Inscrição em atividades, presença, certificados ou dados de turma.
- Cascata ou desvinculação automática ao excluir uma instituição.

## Recursos e contratos

Todos os endpoints usam `CurrentTokenData`, retornam os status HTTP do padrão existente
e ficam disponíveis sob o prefixo da aplicação (`/api` no deployment atual).

### Instituições

Recurso persistido em `institutions.json`, com a forma:

```json
{
  "nextId": 1,
  "institutions": []
}
```

O catálogo inicial deve ser criado a partir das escolas que estavam no grupo
`participating-teams` da seção `science-fair` de `schedule.json`. Todas serão cadastradas
com `state: "SC"` e `city: "Chapecó"`, preservando os nomes originais:

- Eeb Candido Ramos
- EEB Prof Lourdes A. S. Lago
- EEB Olga Fin Travi
- EEB Professora Zitta Flach
- EEB Cordilheira Alta
- Colégio Trilíngue Inovação
- EEB BELERMINO VICTOR DALLA VECCHIA
- E.E.B. Jorge Lacerda
- Eeb Prof Manuel De Freitas Trancoso
- Eeb Cedrense
- EEB RuI Barbosa

O grupo `participating-teams` será removido de `schedule.json`, mas a seção
`science-fair` / “Programação Feira de Ciências” permanecerá como seção vazia para
preservar a organização da programação.

Cada instituição possui:

```json
{
  "id": "institution-001",
  "name": "Escola Estadual Exemplo",
  "state": "São Paulo",
  "city": "São Paulo",
  "description": "Descrição opcional"
}
```

Campos de entrada:

- `name`: obrigatório, texto não vazio, até 200 caracteres.
- `state`: obrigatório, texto não vazio, até 100 caracteres.
- `city`: obrigatório, texto não vazio, até 100 caracteres.
- `description`: opcional, até 500 caracteres; vazio normalizado para `null`.

Endpoints:

| Método   | Caminho                          | Resultado                          |
| -------- | -------------------------------- | ---------------------------------- |
| `GET`    | `/institutions`                  | Lista todas as instituições.       |
| `GET`    | `/institutions/{institution_id}` | Retorna uma instituição.           |
| `POST`   | `/institutions`                  | Cria e retorna `201 Created`.      |
| `PUT`    | `/institutions/{institution_id}` | Substitui e retorna a instituição. |
| `DELETE` | `/institutions/{institution_id}` | Remove e retorna `204 No Content`. |

O nome da instituição é único após normalização Unicode, espaços e caixa. O ID é
gerado pelo client e preservado em atualizações.

### Participantes

Recurso persistido em `participants.json`, com a forma:

```json
{
  "nextId": 1,
  "participants": []
}
```

Cada participante possui:

```json
{
  "id": "participant-001",
  "name": "Nome do aluno",
  "cpf": "12345678909",
  "email": "aluno@example.org",
  "institutionId": "institution-001"
}
```

Campos de entrada:

- `name`: obrigatório, texto não vazio, até 200 caracteres.
- `cpf`: obrigatório, válido conforme os dígitos verificadores do CPF, normalizado
  para os 11 dígitos sem pontuação e único entre os participantes.
- `email`: obrigatório, texto não vazio, até 254 caracteres, normalizado com `strip`.
- `institutionId`: obrigatório e deve apontar para uma instituição existente.

O fato de todos os participantes serem alunos do último ano do ensino médio é uma
regra do evento, não um campo repetido em cada registro.

Endpoints:

| Método   | Caminho                          | Resultado                           |
| -------- | -------------------------------- | ----------------------------------- |
| `GET`    | `/participants`                  | Lista todos os participantes.       |
| `GET`    | `/participants/{participant_id}` | Retorna um participante.            |
| `POST`   | `/participants`                  | Cria e retorna `201 Created`.       |
| `PUT`    | `/participants/{participant_id}` | Substitui e retorna o participante. |
| `DELETE` | `/participants/{participant_id}` | Remove e retorna `204 No Content`.  |

O ID do participante é gerado pelo client e preservado em atualizações. O CPF identifica
unicamente a pessoa no cadastro; o contrato não exige unicidade de e-mail.

## Persistência e integridade

- `get_institutions_path()` resolve `INSTITUTIONS_PATH` no momento da chamada e usa
  `db/institutions.json` como fallback.
- `get_participants_path()` resolve `PARTICIPANTS_PATH` no momento da chamada e usa
  `db/participants.json` como fallback.
- Clients validam a estrutura dos arquivos, fazem cópia defensiva dos resultados e usam
  `atomic_write_json` para persistência.
- Criar ou atualizar participante valida `institutionId` no catálogo de instituições antes
  de persistir.
- Excluir instituição consulta os participantes; se houver referências, lança conflito
  com as referências dos participantes e não altera nenhum arquivo.
- Renomear instituição não altera participantes porque eles referenciam o ID.
- Erros de client são convertidos na fronteira HTTP: ausência em `404`, nome duplicado ou
  recurso em uso em `409`, entrada inválida em `422` e falha de persistência em `500`.

## Fluxo da API

```text
cliente autenticado
  -> POST /institutions
  -> resposta com institutionId
  -> POST /participants { name, cpf, email, institutionId }
  -> client valida a instituição
  -> participants.json gravado atomicamente
  -> resposta do participante
```

Rotas não acessam arquivos diretamente. O router valida o corpo e a autenticação, o
client aplica regras de domínio e persistência, e os modelos definem os contratos públicos
de entrada e saída.

## Página administrativa

A página fica no painel autenticado servido em `/home`, seguindo os padrões visuais e de
acessibilidade de `backend/DESIGN.md`. Ela adiciona as seções “Instituições” e
“Participantes” à navegação existente.

- “Instituições” lista nome, cidade e estado, com busca, criação, edição e exclusão.
- “Participantes” lista nome, CPF mascarado, e-mail e instituição, com busca, criação,
  edição e exclusão.
- Formulários usam diálogos acessíveis, labels explícitos, foco visível, mensagens de
  sucesso/erro e confirmação para exclusões.
- O CPF é exibido mascarado na lista e enviado somente quando necessário para criar ou
  editar o registro.
- A página usa o token JWT já armazenado pela sessão administrativa e não embute catálogos
  nem dados pessoais no HTML inicial.
- Instituições referenciadas por participantes exibem o conflito retornado pela API e não
  podem ser excluídas.

## Critérios de aceitação

- Requisições sem ou com JWT inválido são rejeitadas antes de acessar os catálogos.
- O CRUD completo funciona para os dois recursos e preserva IDs.
- Instituições e participantes ficam em arquivos separados, configuráveis por ambiente.
- Instituição inexistente não pode ser referenciada por participante.
- Instituição vinculada não pode ser excluída.
- Nomes equivalentes de instituições são rejeitados.
- CPF ausente, inválido ou duplicado é rejeitado.
- O grupo de equipes participantes não existe mais no `schedule.json`, e a seção da Feira
  de Ciências continua presente sem esse grupo.
- O painel autenticado permite gerenciar instituições e participantes sem expor CPF completo
  na listagem.
- Falhas de leitura, validação estrutural ou escrita não vazam detalhes de filesystem na
  resposta HTTP.
- A suíte existente continua passando sem alterar os arquivos de dados reais.
