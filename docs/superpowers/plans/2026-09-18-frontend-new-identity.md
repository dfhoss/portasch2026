# Nova identidade do frontend — Implementation Plan

> Registro histórico da migração inicial. As decisões posteriores do usuário (fundo claro, banner centralizado, carrossel circular e consolidação documental) estão no [DESIGN único do frontend](../../../frontend/DESIGN.md). Ele prevalece sobre os valores e critérios antigos registrados abaixo.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aplicar a nova paleta/fontes e os banners responsivos sem mudar os contratos da home.
**Architecture:** Tokens centralizados compartilhados pelas folhas atuais; fontes locais; picture responsivo. Tema legado isolado, nova identidade de alto contraste pendente.
**Tech Stack:** HTML/CSS/JavaScript estáticos; Python unittest e Playwright para testes renderizados.
**Spec:** docs/superpowers/specs/2026-09-18-frontend-new-identity.md

## Global Constraints
- Somente frontend, specs/plans e testes relacionados; não modificar backend/db/participants.json nem outros dados.
- Sem build, bundler, package.json ou dependência runtime nova.
- lang="pt-BR", landmarks, rótulos, foco, teclado e toque preservados.
- Carrossel: 3 cartões acima de 900px, 2 de 601px a 900px, 1 até 600px; gap 20px; autoplay 5s; debounce resize 150ms; swipe maior que 50px.
- Sem alterar scripts de negócio/carrossel salvo correção indispensável demonstrada por teste e registrada.
- Sem rolagem horizontal involuntária em 390, 768 e 1440px.
- Fontes e imagens locais, nomes reais, caminhos relativos.
- Alto contraste novo permanece pendente; não adicionar toggle novo.
- Preservar mudanças não relacionadas do checkout principal.

## Ambiente e comandos
Worktree: C:/Users/Administrador/Desktop/projetos/portasch2026/.worktrees/frontend-new-identity
Python já provisionado: C:/Users/Administrador/Desktop/projetos/portasch2026/backend/.venv/Scripts/python.exe
Executar testes da raiz do worktree:
```powershell
& 'C:/Users/Administrador/Desktop/projetos/portasch2026/backend/.venv/Scripts/python.exe' -m unittest discover -s frontend/tests -p 'test_*.py' -v
```
Criar servidor HTTP temporário dentro do harness (ThreadingHTTPServer, SimpleHTTPRequestHandler(directory=str(repo_root)), porta 0, thread daemon, shutdown/server_close no cleanup). Usar Playwright sync API com Chromium já instalado. Não importar aplicação backend.

### Task 1: Tokens e fontes aplicados à home
**Files:** criar frontend/static/css/tokens.css, fonts.css, frontend/static/assets/fonts/*.woff; criar frontend/tests/browser_support.py e test_identity_tokens.py; modificar head de frontend/index.html, frontend/static/css/main.css e schedule.css. Atualizar DESIGN.md e README.md apenas para os contratos de tokens/fontes desta tarefa.
**Interfaces:** consumir a paleta/45 papéis exatos de frontend/DESIGN.md e as faces disponíveis em frontend/static/assets/fonts/. Produzir folhas fonts.css e tokens.css carregadas antes de main.css e schedule.css; preservar data-theme standard/high-contrast/dark.
**Requisitos específicos:** migrar cores de componentes e pseudo-elementos; remover duplicação root e overrides legados de schedule.css para o bloco legado centralizado. Manter legado legível com pares semânticos equivalentes às cores atuais. Não alterar hero estruturalmente ainda; sua composição é substituída na Task 2. Aplicar Open Sans 400/700, Disket Mono 400/700, Retropix 400, Garet 400/700 conforme spec; eliminar peso 900 nos papéis sem face correspondente.
- [ ] Escrever harness unittest/Playwright e testes de resultado no navegador antes de CSS. Padrão de asserções:
```python
self.page.goto(self.base_url + "/frontend/")
self.assertEqual(
    self.page.locator("body").evaluate("(e) => getComputedStyle(e).backgroundColor"),
    "rgb(210, 222, 207)",
)
self.assertEqual(
    self.page.locator(".activity-card").first.evaluate(
        "(e) => getComputedStyle(e).backgroundColor"
    ),
    "rgb(255, 255, 255)",
)
self.assertIn(
    "Open Sans", self.page.locator("body").evaluate("(e) => getComputedStyle(e).fontFamily")
)
self.assertEqual(
    self.page.locator(".carousel-btn.next").evaluate("(e) => getComputedStyle(e).backgroundColor"),
    "rgb(57, 58, 237)",
)
```
Adicionar comportamento selecionado/finalizado e troca via atributo legado em elementos reais. Verificar que faces solicitadas retornam FontFace carregada e que não há PENDENTE em stylesheets runtime.
- [ ] Executar comando unittest acima, registrar falhas de cor/fonte esperadas (RED). Evitar falha por dependência/configuração como evidência.
- [ ] Implementar tokens lendo bloco completo de DESIGN.md, centralizar legado e faces locais, migrar seletores. Exemplo de consumo:
```css
body { background: var(--color-page); color: var(--color-text); font-family: var(--font-body); }
.carousel-btn { background: var(--color-action-surface); color: var(--color-action-text); }
.status-badge.live { background: var(--color-status-live-surface); color: var(--color-status-live-text); }
```
- [ ] Reexecutar testes, corrigir só o que a implementação exige, registrar GREEN. Fazer self-review do diff, referências e pesos.
- [ ] Atualizar docs de runtime e commit explícito somente dos arquivos desta tarefa; escrever relatório task-1-report.md com comandos e saída RED/GREEN, commits e limitações.

### Task 2: Hero desktop/mobile, nomes e regressões
**Files:** renomear os dois assets da spec; modificar frontend/index.html e static/css/main.css; criar frontend/tests/test_identity_hero.py; atualizar frontend/DESIGN.md e README.md.
**Interfaces:** consumir fonts.css/tokens.css e o harness de Task 1. Produzir picture .hero-picture com img .hero-image; breakpoint mobile 600px.
- [ ] Escrever testes de currentSrc e proporção antes de mudar HTML/arquivos:
```python
self.page.set_viewport_size({"width": 1440, "height": 1000})
self.page.goto(self.base_url + "/frontend/")
hero = self.page.locator(".hero-image")
self.assertEqual(hero.count(), 1, "A home precisa de um único hero")
self.assertTrue(hero.evaluate("(e) => e.currentSrc").endswith("/hero-desktop.jpg"))
self.page.set_viewport_size({"width": 390, "height": 844})
self.page.wait_for_function(
    "document.querySelector('.hero-image')?.currentSrc.endsWith('/hero-mobile.png')"
)
self.assertEqual(hero.evaluate("(e) => e.naturalWidth"), 1080)
```
Testar razão natural versus renderizada com tolerância de 1px, ausência de overflow em 390/768/1440, h1 único, carregamento de imagens/fontes/agenda e console sem erros próprios da aplicação. Adicionar checks de controles por teclado, swipe curto versus >50px, resize 3/2/1 e estados dos controles. Usar relógio determinístico para autoplay se testar o timer. Testar falha de rede da agenda preservando conteúdo de fallback/interação existente, sem exigir nova UX.
- [ ] Rodar unittest e observar RED esperado por ausência do hero.
- [ ] Renomear via operações literais seguras, preservar hashes, atualizar referências. Usar esta estrutura:
```html
<header class="banner" role="banner" aria-label="UFFS de Portas Abertas">
  <h1 class="visually-hidden">UFFS de Portas Abertas</h1>
  <picture class="hero-picture">
    <source media="(max-width: 600px)" srcset="static/assets/images/hero-mobile.png" width="1080" height="437">
    <img class="hero-image" src="static/assets/images/hero-desktop.jpg" width="5938" height="1250"
      alt="Campus Chapecó. 27 de outubro, das 08h30 às 21h." fetchpriority="high">
  </picture>
</header>
```
Hero sem altura fixa/cover/corte, width 100%, height auto, display block. Remover CSS da composição antiga sem afetar classes de outras seções. Visually-hidden acessível e não display:none.
- [ ] Executar suite completa; observar GREEN e conferir screenshots em 390/768/1440. Corrigir apenas regressões da mudança ou defeitos preexistentes que bloqueiem requisito, documentando estes últimos.
- [ ] Atualizar documentação ativa, DESIGN.md (normal implementado, papel móvel confirmado, JPG preferido, placeholders HC mantidos), README incluindo comando de teste reproduzível com ambiente Playwright disponível; verificar caminhos dos renames.
- [ ] Commit explícito da tarefa e relatório task-2-report.md com hashes preservados, evidência RED/GREEN e screenshots/limitações.

## Revisão e entrega
Após cada tarefa, controlador gera review-package e solicita revisão de spec/qualidade. Corrigir achados por subagente e revalidar testes afetados. Ao final, revisão de branch inteira e verificação independente no MCP Playwright. Guardar worktree/branch para integração revisável; nenhuma alteração de dados ou merge automático.
