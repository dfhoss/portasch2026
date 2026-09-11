# Componente Programação Completa (Portas Abertas)

Este pacote isolado e autossuficiente contém o HTML, CSS, JavaScript, dados e o arquivo de especificação de design (`DESIGN.md` seguindo o padrão [designmd.co](https://www.designmd.co/)) da seção `<section id="complete-program">`.

---

## 📁 Estrutura dos Arquivos

| Arquivo | Descrição |
| :--- | :--- |
| **`DESIGN.md`** | **Tokens de design** em formato YAML Frontmatter (`version: alpha`) e documentação completa de estilos, tipografia, acessibilidade e regras para reprodução em outros repositórios. |
| **`component.html`** | Snippet HTML puro e limpo contendo exatamente a `<section id="complete-program">` para cópia e colagem direta. |
| **`styles.css`** | Folha de estilo completa e independente com todas as variáveis CSS (`--color-...`), layout responsivo, tipografia e tema de Alto Contraste. |
| **`script.js`** | Módulo JavaScript interativo que gerencia a alternância de visualização (**Turno** vs **Eixo do Conhecimento**), acessibilidade por teclado (ARIA radiogroup), acordeões e cálculo de status finalizado. |
| **`schedule-data.json`** | Dados em JSON com as 16 áreas/cursos, sessões de horários, locais e mapeamento com os eixos da Cine Brasil / Inep. |
| **`index.html`** | Página de demonstração pronta para abrir no navegador, com botões para testar o modo Alto Contraste e expandir todos os acordeões. |

---

## 🚀 Como usar em outro repositório

### Opção 1: HTML / CSS / JS Vanilla
1. Copie a pasta `complete-program/` para o seu novo repositório.
2. No seu arquivo HTML, adicione o CSS e importe o script:
```html
<link rel="stylesheet" href="./complete-program/styles.css">

<!-- Cole o conteúdo de complete-program/component.html aqui -->

<script type="module" src="./complete-program/script.js"></script>
```

### Opção 2: React / Next.js / Vue
Consulte a seção `5. How to Reproduce in Another Repository` dentro de [`DESIGN.md`](./DESIGN.md) para exemplos de código de integração e configuração do Tailwind CSS.

---

## 🎨 Principais Tokens de Design

- **Primária:** `#015a83`
- **Superfície:** `#ffffff`
- **Fundo da página:** `#fffff6`
- **Bordas estruturais:** `2px solid #015a83`
- **Raio dos cartões:** `0.75rem` (12px)
- **Pills e Botões:** `999px`
- **Tipografia:** `Disket Mono` / `Space Mono` (Títulos), `Garet` / `Montserrat` (Apoio/UI), `Open Sans` (Corpo).
