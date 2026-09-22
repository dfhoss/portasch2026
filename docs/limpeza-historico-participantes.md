# Limpeza do histórico de participantes

## Objetivo

Remover dos commits as informações de `db/participants.json` e impedir que o
arquivo volte a ser rastreado pelo Git, preservando a cópia local para uso do
ambiente.

## Situação encontrada

O arquivo estava rastreado na árvore atual como `db/participants.json`. Durante
a validação da primeira reescrita, também foi encontrada uma versão histórica
do mesmo arquivo em `backend/db/participants.json`.

O `git-filter-repo` não segue renomeações automaticamente quando recebe um
caminho específico. Por isso, filtrar apenas o caminho atual não seria
suficiente: a versão antiga continuaria acessível pelas refs que ainda
contivessem o caminho `backend/db/participants.json`.

## Procedimento executado

1. Verifiquei o estado do repositório, os branches locais, as refs remotas e o
   histórico que mencionava o arquivo. A alteração local não relacionada em
   `.vscode/` foi preservada.
2. Preservei temporariamente a cópia de trabalho de
   `db/participants.json` fora do repositório. Essa cópia não foi criada como
   uma ref ou backup Git e foi removida ao final do procedimento.
3. Executei uma primeira reescrita com o caminho atual:

   ```powershell
   uvx --from git-filter-repo git-filter-repo --force `
     --path db/participants.json --invert-paths
   ```

4. A verificação mostrou que o blob antigo ainda estava alcançável pela
   versão histórica em `backend/db/participants.json`. Essa primeira tentativa
   não foi considerada concluída.
5. Executei uma segunda reescrita incluindo os dois caminhos:

   ```powershell
   uvx --from git-filter-repo git-filter-repo --force `
     --path db/participants.json `
     --path backend/db/participants.json `
     --invert-paths
   ```

   Essa operação reescreveu todas as refs locais e podou os objetos antigos.
6. Restaurei a cópia local de `db/participants.json`. Ela ficou não rastreada e
   ignorada.
7. Adicionei esta regra ao `.gitignore`:

   ```gitignore
   /db/participants.json
   ```

8. Registrei a regra no commit `3473565`, com a mensagem
   `Ignora participantes locais`.

## Validações realizadas

As verificações finais confirmaram que:

- nenhum dos dois caminhos aparece nas refs ou no histórico local;
- o blob original não existe mais no banco de objetos;
- `git fsck --full --no-reflogs --unreachable --no-progress` não encontrou
  objetos inacessíveis;
- `git check-ignore -v -- db/participants.json` confirma a regra do
  `.gitignore`;
- `git ls-files --error-unmatch -- db/participants.json` confirma que o
  arquivo não está rastreado;
- não há alterações rastreadas pendentes.

## Estado do remoto

O `git-filter-repo` removeu automaticamente o remote `origin` durante a
reescrita como medida de segurança. A URL foi restaurada localmente, mas não
foi executado `fetch` nem `force-push`.

Consequentemente, o repositório local está limpo, mas o remoto ainda pode
conter os commits antigos. Antes de sincronizar o remoto, é necessário
coordenar um force-push apenas das branches desejadas. Um `fetch` antes dessa
limpeza pode trazer novamente as refs antigas para o repositório local.
