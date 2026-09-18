# Task 1 — relatório

## Resultado

Implementados tokens semânticos da nova paleta, aliases legados, fontes locais e migração das
folhas da home. O hero e a estrutura do carrossel não foram alterados (escopo da Task 2).

## TDD e validação

RED observado antes da correção, no comando:

```text
C:/Users/Administrador/Desktop/projetos/portasch2026/backend/.venv/Scripts/python.exe -m unittest discover -s frontend/tests -p 'test_*.py' -v
```

Resultado: 4/5 passaram; `test_legacy_theme_attribute_switches_equivalent_component_pairs` falhou
com `rgb(67, 72, 220) != rgb(200, 255, 0)`. A interpolação vinha da transição de background do
botão durante a troca do atributo de tema. A transição de cor foi removida; a transição de escala
permanece.

GREEN, após a implementação:

```text
Ran 5 tests in 5.788s
OK
```

Faces locais carregadas, pares standard/legado e finalizado verificados, e nenhum `PENDENTE`
presente nas folhas runtime.

## Arquivos

Criados `frontend/static/css/tokens.css`, `frontend/static/css/fonts.css`, as sete faces em
`frontend/static/assets/fonts/` e os testes/harness em `frontend/tests/`. Modificados `index.html`,
`main.css`, `schedule.css`, `README.md` e `DESIGN.md`.

## Self-review e limitações

Revisei o diff para manter os breakpoints, gap e scripts inalterados. O alto contraste novo continua
pendente por especificação; `high-contrast`/`dark` são apenas aliases legados documentados.
