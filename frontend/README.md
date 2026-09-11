# Frontend — UFFS de Portas Abertas

Frontend estático da página pública do UFFS de Portas Abertas. A versão-base (`0e6d610`) apresenta
um banner da identidade Contraste e a seção “Rolando agora”, com cartões de atividades em um
carrossel responsivo.

## Executar localmente

Na raiz do repositório:

```powershell
py -m http.server 4173 --directory frontend
```

Abra <http://localhost:4173/>. Se `py` não estiver disponível, use:

```powershell
python -m http.server 4173 --directory frontend
```

Não há `package.json`, bundler ou dependências de frontend nessa versão; o navegador carrega
`index.html`, `styles.css`, `carousel.js` e os assets relativos diretamente.

## Organização

| Caminho | Responsabilidade |
| --- | --- |
| `index.html` | Estrutura semântica da home e conteúdo dos cartões |
| `styles.css` | Identidade visual, layout, breakpoints e estados |
| `carousel.js` | Navegação, autoplay, indicadores, teclado, swipe e resize |
| `assets/` | Imagens e materiais visuais da página |
| `DESIGN.md` | Tokens e regras visuais/acessíveis |
| `AGENTS.md` | Regras operacionais para manutenção por agentes |

## Comportamento do carrossel

- 3 cartões são exibidos acima de `900px`, 2 entre `601px` e `900px`, e 1 até `600px`.
- O autoplay avança a cada 5 segundos e reinicia depois de navegação manual.
- Setas esquerda/direita e swipe horizontal navegam entre atividades; o swipe exige mais de
  50px de deslocamento.
- O resize é processado após 150ms para recriar os indicadores e recalcular o deslocamento.

## Validação manual

1. Abra a página em desktop e redimensione para tablet e celular.
2. Confirme que imagens e estilos carregam sem erros no console.
3. Use Tab para alcançar os controles e as setas para navegar.
4. Verifique os estados desabilitados no início/fim e o retorno ao primeiro item no autoplay.
5. Teste swipe em um dispositivo móvel ou no modo responsivo do navegador.

Para alterações visuais ou de interação, consulte [`DESIGN.md`](./DESIGN.md) e registre em
[`AGENTS.md`](./AGENTS.md) somente regras operacionais que não possam ser descobertas rapidamente
no código.

## Evolução da branch

Commits posteriores podem adicionar áreas como `complete-program/`. Esses pacotes têm seus próprios
documentos e contratos; preserve a separação até que a home e o componente sejam integrados
intencionalmente.

## Referências técnicas

Para decisões de UI, consulte a seção [Referências para implementação](./DESIGN.md#referências-para-implementação)
no `DESIGN.md`. Ela reúne as referências usadas pelo backend para tipografia, botões, estados,
layout, overflow, tokens CSS e acessibilidade visual:

- Material Design 3, Fluent 2, Carbon e GOV.UK para padrões de componentes e hierarquia;
- W3C e Design Tokens Community Group para propriedades personalizadas e tokens;
- MDN para `var()`, Flexbox e `overflow`.

Antes de introduzir um novo padrão visual, verifique primeiro se ele pode ser expresso pelos
tokens e regras já documentados no `DESIGN.md`.
