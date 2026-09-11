/**
 * Complete Program Schedule - Interactive Component Script
 * Portas Abertas UFFS - Standalone & Reusable Module
 */

const DEFAULT_SCHEDULE_DATA = {"version": 1, "eventDate": "2026-10-26", "timeZone": "America/Sao_Paulo", "knowledgeAxes": {"general": "Atividades gerais", "education": "Educação", "arts-and-humanities": "Artes e humanidades", "social-sciences-communication-and-information": "Ciências sociais, comunicação e informação", "business-administration-and-law": "Negócios, administração e direito", "natural-sciences-mathematics-and-statistics": "Ciências naturais, matemática e estatística", "computing-and-ict": "Computação e Tecnologias da Informação e Comunicação", "engineering-manufacturing-and-construction": "Engenharia, produção e construção", "agriculture-forestry-fisheries-and-veterinary": "Agricultura, silvicultura, pesca e veterinária", "health-and-welfare": "Saúde e bem-estar"}, "section": {"id": "complete-program", "title": "Programação completa", "description": "Intervalos: manhã, das 12h às 13h; tarde, das 17h30 às 19h.", "groups": [{"id": "general-activities", "title": "Atividades gerais", "knowledgeAxis": "general", "items": [{"id": "general-recepcao-nos-auditorios-dos-blocos-a-e-b-das-8h30-as-21h", "title": "Recepção nos Auditórios dos Blocos A e B, das 8h30 às 21h", "description": "Breve apresentação da UFFS e", "sessions": [{"startTime": "08:30", "endTime": "21:00", "location": "Auditórios dos Blocos A e B"}], "link": null}]}, {"id": "administracao", "title": "ADMINISTRAÇÃO", "knowledgeAxis": "business-administration-and-law", "items": [{"id": "administracao-voz-e-acao-conhecendo-o-curso-de-administracao", "title": "Voz e Ação: conhecendo o curso de Administração", "description": "Visita e explicação sobre o\n espaço maker e estúdio de podcast", "sessions": [{"startTime": "08:30", "endTime": "12:00", "location": "Bloco A - Sala 105"}, {"startTime": "13:00", "endTime": "18:00", "location": "Bloco A - Sala 105"}, {"startTime": "19:00", "endTime": "21:00", "location": "Bloco A - Sala 105"}], "link": null}, {"id": "administracao-oficina-de-comunicacao-e-oratoria", "title": "Oficina de Comunicação e Oratória", "description": "Técnicas de comunicação e boa oratória", "sessions": [{"startTime": "09:30", "endTime": "21:00", "location": "Bloco A - Sala 103"}, {"startTime": "15:00", "endTime": "21:00", "location": "Bloco A - Sala 103"}, {"startTime": "19:00", "endTime": "21:00", "location": "Bloco A - Sala 103"}], "link": null}, {"id": "administracao-pitch-relampago-e-quiz", "title": "Pitch Relâmpago e Quiz", "description": "Quiz sobre a profissão de Administrador e \nsimulação de Startup", "sessions": [{"startTime": "08:30", "endTime": "12:00", "location": "Bloco A - Sala 106"}, {"startTime": "13:00", "endTime": "18:00", "location": "Bloco A - Sala 106"}, {"startTime": "19:00", "endTime": "21:00", "location": "Bloco A - Sala 106"}], "link": null}]}, {"id": "agronomia", "title": "AGRONOMIA", "knowledgeAxis": "agriculture-forestry-fisheries-and-veterinary", "items": [{"id": "agronomia-apresentacao-do-curso-de-agronomia", "title": "Apresentação do curso de Agronomia", "description": "Apresentação de diferentes atividades e áreas de atuação do profissional de Agronomia", "sessions": [{"startTime": "08:30", "endTime": "21:00", "location": "Bloco A - Sala 203"}], "link": null}, {"id": "agronomia-visitacao-ao-laboratorio-de-lupas-luparia", "title": "Visitação ao laboratório de Lupas (Luparia)", "description": "Demonstração/observação de estruturas vegetais, insetos e rochas (Lupas e Microscópios)", "sessions": [{"startTime": "08:30", "endTime": "12:00", "location": "LAB 04 - Sala 102"}, {"startTime": "13:00", "endTime": "18:00", "location": "LAB 04 - Sala 102"}, {"startTime": "19:00", "endTime": "21:00", "location": "LAB 04 - Sala 102"}], "link": null}, {"id": "agronomia-maquinas-agricolas", "title": "Máquinas Agrícolas", "description": "Apresentação de máquinas e implementos agrícolas utilizados nas atividades práticas, na área experimental.", "sessions": [{"startTime": "08:30", "endTime": "21:00", "location": "Estacionamento em frente à Cantina"}], "link": null}]}, {"id": "ciencia-da-computacao", "title": "CIÊNCIA DA COMPUTAÇÃO", "knowledgeAxis": "computing-and-ict", "items": [{"id": "ciencia-da-computacao-oficina-de-circuitos", "title": "Oficina de Circuitos", "description": "Desafios Interativos da Computação", "sessions": [{"startTime": "08:30", "endTime": "21:00", "location": "Bloco B - Sala 409"}], "link": null}, {"id": "ciencia-da-computacao-oficina-de-programacao", "title": "Oficina de Programação", "description": "Desafios de Lógica de Programação", "sessions": [{"startTime": "08:30", "endTime": "21:00", "location": "Bloco B - Sala 405"}], "link": null}]}, {"id": "ciencias-economicas", "title": "CIÊNCIAS ECONÔMICAS", "knowledgeAxis": "social-sciences-communication-and-information", "items": [{"id": "ciencias-economicas-apresentacao-do-curso-de-ciencias-economicas", "title": "Apresentação do curso de Ciências Econômicas", "description": "Apresentação dos projetos de extensão de Educação Financeira, Índice de Inflação em Chapecó e Região e de Gestão Ambiental", "sessions": [{"startTime": "08:30", "endTime": "21:00", "location": "Bloco A - Sala 204"}], "link": null}, {"id": "ciencias-economicas-observatorio-do-mercado-financeiro", "title": "Observatório do Mercado Financeiro", "description": "Apresentação dos indicadores do Mercado Financeiro e\nda Bolsa de Valores", "sessions": [{"startTime": "08:30", "endTime": "12:00", "location": "Bloco A - Sala 408 Lab. de informática"}, {"startTime": "13:00", "endTime": "18:00", "location": "Bloco A - Sala 408 Lab. de informática"}], "link": null}]}, {"id": "ciencias-sociais", "title": "CIÊNCIAS SOCIAIS", "knowledgeAxis": "social-sciences-communication-and-information", "items": [{"id": "ciencias-sociais-apresentacao-do-curso-de-ciencias-sociais", "title": "Apresentação do curso de Ciências Sociais", "description": "O que faz um cientista social, os caminhos da pesquisa e da docência, atividades que o projeto de extensão realiza a partir dos temas da antropologia, da ciência política e da sociologia.", "sessions": [{"startTime": "19:00", "endTime": "21:00", "location": "Bloco B - Sala 107"}], "link": null}, {"id": "ciencias-sociais-sala-tematica-audiovisual-e-ciencias-sociais", "title": "Sala Temática: Audiovisual e Ciências Sociais", "description": "Exibição de curtas e diálogos que abordam temas de interesse das\n Ciências Sociais e diálogo.", "sessions": [{"startTime": "19:30", "endTime": "20:00", "location": "Bloco A - Sala 305"}, {"startTime": "20:10", "endTime": "20:40", "location": "Bloco A - Sala 305"}, {"startTime": "20:50", "endTime": "21:20", "location": "Bloco A - Sala 305"}], "link": null}]}, {"id": "enfermagem", "title": "ENFERMAGEM", "knowledgeAxis": "health-and-welfare", "items": [{"id": "enfermagem-oficina-sobre-atendimento-a-parada-cardiorrespiratoria", "title": "Oficina sobre atendimento à parada cardiorrespiratória", "sessions": [{"startTime": "08:30", "endTime": "21:00", "location": "Bloco Lab. 01 - Sala 109 e 110 -Enfermagem"}], "link": null}, {"id": "enfermagem-oficina-de-atendimento-a-ovace-e-atendimento-a-crise-convulsiva", "title": "Oficina de atendimento a OVACE e atendimento à crise convulsiva", "sessions": [{"startTime": "08:30", "endTime": "21:00", "location": "Bloco Lab. 01 - Sala 109 e 110 -Enfermagem"}], "link": null}, {"id": "enfermagem-afericao-de-pressao-arterial", "title": "Aferição de pressão arterial", "sessions": [{"startTime": "08:30", "endTime": "21:00", "location": "Bloco B - Sala 109"}], "link": null}]}, {"id": "engenharia-ambiental", "title": "ENGENHARIA AMBIENTAL", "knowledgeAxis": "engineering-manufacturing-and-construction", "items": [{"id": "engenharia-ambiental-apresentacao-do-curso-de-engenharia-ambiental", "title": "Apresentação do curso de Engenharia Ambiental", "description": "Apresentação do curso com vídeos e quiz", "sessions": [{"startTime": "08:30", "endTime": "21:00", "location": "Bloco A - Sala 201"}], "link": null}, {"id": "engenharia-ambiental-experimentos-exposicao", "title": "Experimentos/\nExposição", "description": "Serão realizados experimentos: Ensaio de \"Jar Test\"; Bioindicadores de qualidade do solo; Ensaio de Eletrocoagulação; Titulação de água contaminada com ácido; Calha Parshall; Reciclagem de resíduos.", "sessions": [{"startTime": "08:30", "endTime": "21:00", "location": "Bloco A - Sala 202"}], "link": null}]}, {"id": "engenharia-civil", "title": "ENGENHARIA CIVIL", "knowledgeAxis": "engineering-manufacturing-and-construction", "items": [{"id": "engenharia-civil-apresentacao-do-curso-de-engenharia-civil", "title": "Apresentação do curso de Engenharia Civil", "description": "Exposição de materiais e equipamentos; \nConstrução da Ponte de Da Vinci;\nPonte de Palito de Picolés.", "sessions": [{"startTime": "08:30", "endTime": "21:00", "location": "Hall do Bloco A"}], "link": null}]}, {"id": "filosofia", "title": "FILOSOFIA", "knowledgeAxis": "arts-and-humanities", "items": [{"id": "filosofia-apresentacao-do-curso-de-filosofia", "title": "Apresentação do curso de Filosofia", "sessions": [{"startTime": "08:30", "endTime": "21:00", "location": "Bloco A - Hall"}], "link": null}]}, {"id": "geografia", "title": "GEOGRAFIA", "knowledgeAxis": "social-sciences-communication-and-information", "items": [{"id": "geografia-experiencias-geografia-2025", "title": "Experiências Geografia 2025", "description": "Apresentação do curso de Geografia", "sessions": [{"startTime": "08:30", "endTime": "21:00", "location": "Bloco B - Sala 105"}], "link": null}]}, {"id": "historia", "title": "HISTÓRIA", "knowledgeAxis": "arts-and-humanities", "items": [{"id": "historia-exposicao-historia-em-movimento", "title": "Exposição “História em Movimento.", "description": "Produções dos laboratórios, projetos de ensino, pesquisa e extensão, PIBID, Residência Pedagógica, iniciação científica, eventos acadêmicos, publicações e memória institucional do curso.", "sessions": [{"startTime": "08:30", "endTime": "21:00", "location": "Bloco A - Sala 205"}], "link": null}, {"id": "historia-oficina-sobre-fontes-historicas-detetives-do-passado-rastros-da-historia-do-oeste-catarinense", "title": "Oficina sobre fontes históricas: \nDetetives do Passado - Rastros da História do Oeste Catarinense.", "description": "Apresentar a importância das fontes históricas para compreender a formação territorial da região onde vivem. Análise de diferentes tipos de documentos como: mapas antigos e contratos de terras, discutindo o que cada fonte revela e o que silencia o processo histórico.", "sessions": [{"startTime": "08:30", "endTime": "21:00", "location": "Bloco A - Sala 208"}], "link": null}, {"id": "historia-oficina-fronteiras-quando-a-historia-deixa-pegadas-na-natureza", "title": "Oficina Fronteiras: quando a História deixa pegadas na natureza", "description": "A atividade inicia com uma breve introdução sobre o que é a História Ambiental, destacando como ela estuda as relações entre sociedade e natureza ao longo do tempo. Em seguida, os alunos serão desafiados a analisar diferentes acontecimentos históricos e identificar de que maneira esses eventos impactaram o meio ambiente. A partir dessa reflexão, deverão elaborar uma pequena narrativa que mostre como a natureza também faz parte da história e como os processos históricos deixam suas marcas no ambiente.", "sessions": [{"startTime": "09:30", "endTime": "21:00", "location": "Bloco LAB 2  - Sala 103-3"}, {"startTime": "15:00", "endTime": "21:00", "location": "Bloco LAB 2  - Sala 103-3"}], "link": null}, {"id": "historia-visita-laboratorio-universitario-de-patrimonio-e-arqueologia-lupa", "title": "VISITA \nLaboratório Universitário de Patrimônio e Arqueologia (LUPA)", "description": "Equipamentos e materiais utilizados em pesquisas arqueológicas;\nO acervo de objetos e vestígios arqueológicos estudados pelo laboratório;\nAs etapas de trabalho arqueológico, desde a coleta em campo até a análise e a conservação;", "sessions": [{"startTime": "08:30", "endTime": "12:00", "location": "Sala 103 - LAB 1"}, {"startTime": "13:00", "endTime": "18:00", "location": "Sala 103 - LAB 1"}, {"startTime": "19:00", "endTime": "21:00", "location": "Sala 103 - LAB 1"}], "link": null}]}, {"id": "letras", "title": "LETRAS", "knowledgeAxis": "arts-and-humanities", "items": [{"id": "letras-exposicao-do-curso-de-letras", "title": "Exposição do curso de Letras", "description": "Apresentação do curso", "sessions": [{"startTime": "08:30", "endTime": "21:00", "location": "Bloco B - Sala 206"}], "link": null}, {"id": "letras-micro-aula-heterosemanticos", "title": "Micro-aula: Heterosemânticos", "description": "Confusões que as semelhanças (e as diferenças) podem ocasionar aos falantes de português e espanhol.", "sessions": [{"startTime": "09:00", "endTime": "09:20", "location": "Bloco B - Sala 204"}], "link": null}, {"id": "letras-experiencia-dom-quixote", "title": "Experiência Dom Quixote", "description": "Quiz a respeito de Don Quixote com possibilidade de fotografar com armadura de cavaleiro andante e premiação.", "sessions": [{"startTime": "14:00", "endTime": "17:00", "location": "Bloco B - Hall"}, {"startTime": "19:00", "endTime": "21:00", "location": "Bloco B - Hall"}], "link": null}, {"id": "letras-musica-e-jogos-em-ple-e-ele", "title": "Música e jogos em PLE e ELE", "sessions": [{"startTime": "09:30", "endTime": "10:00", "location": "Bloco B - Sala 110"}, {"startTime": "10:30", "endTime": "11:00", "location": "Bloco B - Sala 110"}, {"startTime": "15:00", "endTime": "15:30", "location": "Bloco B - Sala 110"}, {"startTime": "16:00", "endTime": "16:30", "location": "Bloco B - Sala 110"}], "link": null}, {"id": "letras-leitura-e-interpretacao-de-poesia", "title": "Leitura e interpretação de poesia", "description": "Leitura e interpretação de textos poéticos. Compreensão de como um poema se estrutura; que elementos são utlizados para dar o ritmo e sonoridade ao texto; como o conjunto desses elementos contribui paraos sentidos possíveis da obra.", "sessions": [{"startTime": "11:00", "endTime": "11:30", "location": "Bloco B - Lab 2 - Sala 111"}, {"startTime": "16:00", "endTime": "16:30", "location": "Bloco B - Lab 2 - Sala 111"}, {"startTime": "19:30", "endTime": "21:00", "location": "Bloco B - Lab 2 - Sala 111"}], "link": null}, {"id": "letras-clube-de-leitura-travessia-narrativas-de-misterio", "title": "Clube de leitura: Travessia - Narrativas de mistério", "sessions": [{"startTime": "10:00", "endTime": "11:00", "location": "Bloco B - Sala 205"}, {"startTime": "15:00", "endTime": "16:00", "location": "Bloco B - Sala 205"}, {"startTime": "19:30", "endTime": "20:30", "location": "Bloco B - Sala 205"}], "link": null}, {"id": "letras-oficina-de-microconto", "title": "Oficina de microconto", "description": "Leitura, discussão e criação de microcontos.", "sessions": [{"startTime": "13:30", "endTime": "13:50", "location": "Bloco B - Lab 2 - Sala 110"}, {"startTime": "14:00", "endTime": "14:20", "location": "Bloco B - Lab 2 - Sala 110"}, {"startTime": "14:30", "endTime": "14:50", "location": "Bloco B - Lab 2 - Sala 110"}, {"startTime": "15:00", "endTime": "15:20", "location": "Bloco B - Lab 2 - Sala 110"}, {"startTime": "15:30", "endTime": "15:50", "location": "Bloco B - Lab 2 - Sala 110"}, {"startTime": "16:00", "endTime": "16:20", "location": "Bloco B - Lab 2 - Sala 110"}], "link": null}, {"id": "letras-musica-e-jogos-em-ple-e-ele-2", "title": "Música e jogos em PLE e ELE", "sessions": [{"startTime": "09:30", "endTime": "10:00", "location": "Bloco B - Sala 110"}, {"startTime": "10:30", "endTime": "11:00", "location": "Bloco B - Sala 110"}, {"startTime": "15:00", "endTime": "15:30", "location": "Bloco B - Sala 110"}, {"startTime": "16:00", "endTime": "16:30", "location": "Bloco B - Sala 110"}], "link": null}, {"id": "letras-oficina-de-elaboracao-de-prompts", "title": "Oficina de elaboração de prompts", "description": "Elaboração de prompts e interpretação de respostas do chatbot Compreensão de como um prompt se estrutura; alucinações de IA; constribuições para o uso crítico da IA.", "sessions": [{"startTime": "09:00", "endTime": "09:20", "location": "Bloco B - Sala 110 CELUFFS"}, {"startTime": "14:00", "endTime": "14:20", "location": "Bloco B - Sala 110 CELUFFS"}, {"startTime": "19:20", "endTime": "19:40", "location": "Bloco B - Sala 110 CELUFFS"}], "link": null}, {"id": "letras-jogos-sintaticos", "title": "Jogos sintáticos", "description": "Desafios em atividades lúdicas a respeito funcionamento da sintaxe do português brasileiro.", "sessions": [{"startTime": "19:30", "endTime": "20:00", "location": "Bloco B - Sala 207"}, {"startTime": "20:00", "endTime": "20:30", "location": "Bloco B - Sala 207"}, {"startTime": "20:30", "endTime": "21:00", "location": "Bloco B - Sala 207"}, {"startTime": "21:00", "endTime": "21:30", "location": "Bloco B - Sala 207"}], "link": null}]}, {"id": "matematica", "title": "MATEMÁTICA", "knowledgeAxis": "natural-sciences-mathematics-and-statistics", "items": [{"id": "matematica-apresentacao-do-curso-de-matematica", "title": "Apresentação do curso de Matemática", "description": "Encontro no Laboratório de Educação Matemática", "sessions": [{"startTime": "08:30", "endTime": "12:00", "location": "Bloco A - Sala 401"}, {"startTime": "13:00", "endTime": "18:00", "location": "Bloco A - Sala 401"}, {"startTime": "19:00", "endTime": "21:30", "location": "Bloco A - Sala 401"}], "link": null}]}, {"id": "medicina", "title": "MEDICINA", "knowledgeAxis": "health-and-welfare", "items": [{"id": "medicina-apresentacao-do-curso-de-medicina", "title": "Apresentação do curso de Medicina", "description": "Oficina: Conhecendo o corpo humano", "sessions": [{"startTime": "08:30", "endTime": "12:00", "location": "Bloco Lab. 01 - Salas 112 e 113\nLoratório de Anatomia"}, {"startTime": "19:00", "endTime": "21:30", "location": "Bloco Lab. 01 - Salas 112 e 113\nLoratório de Anatomia"}], "link": null}, {"id": "medicina-oficina-entendendo-a-constituicao-histologica-dos-tecidos", "title": "Oficina: Entendendo a constituição histológica dos tecidos", "description": "Proporcionar aos participantes uma compreensão prática e visual da organização microscópica dos principais tecidos do corpo humano.", "sessions": [{"startTime": "08:30", "endTime": "12:00", "location": "Bloco Lab. 01 - Sala 106\nLaboratório de Histologia"}, {"startTime": "19:00", "endTime": "21:30", "location": "Bloco Lab. 01 - Sala 106\nLaboratório de Histologia"}], "link": null}, {"id": "medicina-oficina-tecnica-de-desengasgo", "title": "Oficina: Técnica de desengasgo", "description": "Capacitar os estudantes a reconhecerem situações de obstrução das vias aéreas e aplicar corretamente as técnicas de desengasgo em ambientes simulados.", "sessions": [{"startTime": "08:30", "endTime": "12:00", "location": "Bloco B - Sala 109"}], "link": null}, {"id": "medicina-projeto-viva-bem-cardiologia", "title": "Projeto Viva Bem Cardiologia", "description": "Aferição de pressão arterial e auscuta cardíaca, pulmonar e mostrar para os estudantes o som do coração.", "sessions": [{"startTime": "15:00", "endTime": "18:00", "location": "Bloco B - Sala 109"}], "link": null}]}, {"id": "pedagogia", "title": "PEDAGOGIA", "knowledgeAxis": "education", "items": [{"id": "pedagogia-visitacao-e-vivencia-com-fantasias-e-aderecos-contacao-de-historias-oficina-de-pintura-no-rosto", "title": "Visitação e vivência com fantasias e adereços. \nContação de histórias.\nOficina de pintura no rosto.", "description": "Atividades lúdicas e pedagógicas que apresentam \nparte da atuação profissional.", "sessions": [{"startTime": "08:30", "endTime": "21:30", "location": "Bloco Lab. 2 - Sala 109 - LUDOBRINC"}], "link": null}]}]}};

const KNOWLEDGE_AXES = Object.freeze({
  general: "Atividades gerais",
  education: "Educação",
  "arts-and-humanities": "Artes e humanidades",
  "social-sciences-communication-and-information":
    "Ciências sociais, comunicação e informação",
  "business-administration-and-law": "Negócios, administração e direito",
  "natural-sciences-mathematics-and-statistics":
    "Ciências naturais, matemática e estatística",
  "computing-and-ict": "Computação e Tecnologias da Informação e Comunicação",
  "engineering-manufacturing-and-construction":
    "Engenharia, produção e construção",
  "agriculture-forestry-fisheries-and-veterinary":
    "Agricultura, silvicultura, pesca e veterinária",
  "health-and-welfare": "Saúde e bem-estar",
});

const SHIFTS = Object.freeze([
  { id: "morning", label: "Manhã", startMinutes: 0, endMinutes: 12 * 60 },
  { id: "afternoon", label: "Tarde", startMinutes: 12 * 60, endMinutes: 18 * 60 },
  { id: "evening", label: "Noite", startMinutes: 18 * 60, endMinutes: 21 * 60 + 1 },
]);

function timeToMinutes(value) {
  if (!value) return 0;
  const [hours, minutes] = value.split(":").map(Number);
  return hours * 60 + (minutes || 0);
}

function formatTime(value) {
  if (!value) return "";
  const [hours, minutes] = value.split(":");
  const hour = Number.parseInt(hours, 10);
  return minutes === "00" || !minutes ? `${hour}h` : `${hour}h${minutes}`;
}

function localDateAndMinutes(now, timeZone) {
  try {
    const parts = Object.fromEntries(
      new Intl.DateTimeFormat("en-GB", {
        timeZone,
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        hourCycle: "h23",
      })
        .formatToParts(now)
        .filter(({ type }) => type !== "literal")
        .map(({ type, value }) => [type, value]),
    );

    return {
      date: `${parts.year}-${parts.month}-${parts.day}`,
      minutes: Number(parts.hour) * 60 + Number(parts.minute),
    };
  } catch {
    return {
      date: new Date().toISOString().slice(0, 10),
      minutes: now.getHours() * 60 + now.getMinutes(),
    };
  }
}

function sessionInterval(session) {
  return {
    startMinutes: timeToMinutes(session.startTime),
    endMinutes: timeToMinutes(session.endTime || "21:00"),
  };
}

function overlapsShift(session, shift) {
  const interval = sessionInterval(session);
  return (
    interval.startMinutes < shift.endMinutes &&
    interval.endMinutes > shift.startMinutes
  );
}

function isFinalized(sessions, eventDate, localNow) {
  if (!eventDate || localNow.date < eventDate) return false;
  if (localNow.date > eventDate || localNow.minutes >= 21 * 60) return true;
  if (!sessions || sessions.length === 0) return false;
  return sessions.every(
    (session) =>
      session.endTime && timeToMinutes(session.endTime) <= localNow.minutes,
  );
}

function appendText(parent, tagName, text) {
  const el = document.createElement(tagName);
  el.textContent = text;
  parent.appendChild(el);
  return el;
}

function renderSession(parent, session) {
  const p = document.createElement("p");
  p.classList.add("schedule-session");

  if (session.startTime) {
    const start = document.createElement("time");
    start.setAttribute("datetime", session.startTime);
    start.textContent = formatTime(session.startTime);
    p.appendChild(start);
  }

  if (session.endTime) {
    if (p.childNodes.length) appendText(p, "span", " às ");
    const end = document.createElement("time");
    end.setAttribute("datetime", session.endTime);
    end.textContent = formatTime(session.endTime);
    p.appendChild(end);
  }

  if (session.location) {
    if (p.childNodes.length) p.appendChild(document.createElement("br"));
    const loc = document.createElement("span");
    loc.classList.add("schedule-session__location");
    loc.textContent = session.location;
    p.appendChild(loc);
  }

  parent.appendChild(p);
}

function renderItemCard(item, courseTitle, sessions, finalized, idPrefix) {
  const li = document.createElement("li");
  li.className = "schedule-item schedule-view-item";
  if (finalized) li.classList.add("schedule-item--finalized");
  li.setAttribute("data-schedule-item", item.id);
  li.setAttribute("data-schedule-finalized", String(finalized));

  if (finalized) {
    const badge = appendText(li, "span", "Finalizado");
    badge.className = "schedule-item__status";
  }

  if (courseTitle) {
    const courseEl = appendText(li, "p", courseTitle);
    courseEl.className = "schedule-item__course";
    courseEl.setAttribute("data-schedule-item-course", "");
  }

  const title = appendText(li, "h5", item.title);
  title.className = "schedule-item__title";

  if (item.description) {
    const desc = appendText(li, "p", item.description);
    desc.className = "schedule-item__description";
  }

  for (const session of sessions) {
    renderSession(li, session);
  }

  if (item.link) {
    const a = document.createElement("a");
    a.href = item.link;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.className = "schedule-item__link";
    a.textContent = "Mais informações";
    li.appendChild(a);
  }

  return li;
}

/**
 * Derive Shift groups view model
 */
function deriveShiftView(section, eventDate, now, timeZone) {
  const localNow = localDateAndMinutes(now, timeZone);
  return SHIFTS.map((shift) => {
    const courses = [];
    for (const sourceGroup of section.groups || []) {
      const items = [];
      for (const item of sourceGroup.items || []) {
        const matchingSessions = (item.sessions || []).filter((s) =>
          overlapsShift(s, shift),
        );
        if (matchingSessions.length === 0) continue;
        items.push({
          item,
          courseTitle: sourceGroup.title,
          sessions: matchingSessions,
          finalized: isFinalized(matchingSessions, eventDate, localNow),
        });
      }
      if (items.length > 0) {
        courses.push({
          id: sourceGroup.id,
          title: sourceGroup.title,
          items,
        });
      }
    }
    return { id: shift.id, label: shift.label, courses };
  });
}

/**
 * Derive Knowledge Axis groups view model
 */
function deriveAxisView(section, eventDate, now, timeZone) {
  const localNow = localDateAndMinutes(now, timeZone);
  const groups = [];

  for (const [axisId, label] of Object.entries(KNOWLEDGE_AXES)) {
    const courses = (section.groups || [])
      .filter((g) => g.knowledgeAxis === axisId)
      .map((sourceGroup) => ({
        id: sourceGroup.id,
        title: sourceGroup.title,
        items: (sourceGroup.items || []).map((item) => ({
          item,
          courseTitle: null,
          sessions: item.sessions || [],
          finalized: isFinalized(item.sessions || [], eventDate, localNow),
        })),
      }));

    if (courses.length > 0) {
      groups.push({ id: axisId, label, courses });
    }
  }
  return groups;
}

/**
 * Render groups into container element
 */
function renderGroups(container, groups) {
  container.innerHTML = "";
  let headingId = 100;

  for (const group of groups) {
    const details = document.createElement("details");
    details.className = "schedule-view-group";
    details.setAttribute("data-schedule-group", group.id);

    const summary = document.createElement("summary");
    summary.className = "schedule-view-group__summary";

    const h3 = document.createElement("h3");
    h3.className = "schedule-group__title";
    h3.id = `schedule-heading-${++headingId}`;
    h3.textContent = group.label;

    const totalItems = group.courses.reduce((acc, c) => acc + c.items.length, 0);
    const countSpan = appendText(
      h3,
      "span",
      ` ${totalItems} ${totalItems === 1 ? "atividade" : "atividades"}`,
    );
    countSpan.className = "schedule-view-group__count";

    summary.appendChild(h3);
    details.appendChild(summary);

    const content = document.createElement("div");
    content.className = "schedule-view-group__content";

    if (totalItems === 0) {
      const empty = appendText(content, "p", "Nenhuma atividade disponível.");
      empty.className = "schedule-view-group__empty";
    }

    for (const course of group.courses) {
      const courseSec = document.createElement("section");
      courseSec.className = "schedule-course";
      courseSec.setAttribute("data-schedule-course", course.id);

      const courseH4 = appendText(courseSec, "h4", course.title);
      courseH4.className = "schedule-course__title";
      courseH4.id = `schedule-heading-${++headingId}`;
      courseSec.setAttribute("aria-labelledby", courseH4.id);

      const ul = document.createElement("ul");
      ul.className = "schedule-list";

      for (const entry of course.items) {
        const card = renderItemCard(
          entry.item,
          entry.courseTitle,
          entry.sessions,
          entry.finalized,
          group.id,
        );
        ul.appendChild(card);
      }

      courseSec.appendChild(ul);
      content.appendChild(courseSec);
    }

    details.appendChild(content);
    container.appendChild(details);
  }
}

/**
 * Initialize schedule view selector interactivity
 */
function setupViewSelector({
  selectorEl,
  groupsContainerEl,
  sectionData,
  eventDate = "2026-10-26",
  timeZone = "America/Sao_Paulo",
  defaultMode = "shift",
  initialShiftHtml = null,
}) {
  if (!selectorEl || !groupsContainerEl) return;

  const buttons = Array.from(
    selectorEl.querySelectorAll('[role="radio"][data-schedule-view]'),
  );
  let currentMode = defaultMode;

  function switchMode(mode) {
    currentMode = mode;
    buttons.forEach((btn) => {
      const active = btn.getAttribute("data-schedule-view") === mode;
      btn.setAttribute("aria-checked", String(active));
      btn.tabIndex = active ? 0 : -1;
    });

    if (mode === "shift" && initialShiftHtml) {
      groupsContainerEl.innerHTML = initialShiftHtml;
      return;
    }

    if (sectionData) {
      const now = new Date();
      const groups =
        mode === "knowledge-axis"
          ? deriveAxisView(sectionData, eventDate, now, timeZone)
          : deriveShiftView(sectionData, eventDate, now, timeZone);

      renderGroups(groupsContainerEl, groups);
    }
  }

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const mode = btn.getAttribute("data-schedule-view");
      if (mode && mode !== currentMode) switchMode(mode);
    });

    btn.addEventListener("keydown", (e) => {
      const index = buttons.indexOf(btn);
      let target = null;
      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        target = buttons[(index + 1) % buttons.length];
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        target = buttons[(index - 1 + buttons.length) % buttons.length];
      } else if (e.key === "Home") {
        target = buttons[0];
      } else if (e.key === "End") {
        target = buttons[buttons.length - 1];
      }

      if (target) {
        e.preventDefault();
        target.focus();
        target.click();
      }
    });
  });

  return { switchMode };
}

/**
 * Auto-initialize if present in DOM
 */
function initCompleteProgram() {
  const section = document.getElementById("complete-program");
  if (!section) return;

  const selector = section.querySelector(".schedule-view-selector");
  const groupsContainer = section.querySelector(".schedule-view-groups");
  if (!selector || !groupsContainer) return;

  // Preserve pre-rendered HTML for instant fallback
  const initialShiftHtml = groupsContainer.innerHTML;

  let sectionData = DEFAULT_SCHEDULE_DATA.section || DEFAULT_SCHEDULE_DATA;
  let eventDate = DEFAULT_SCHEDULE_DATA.eventDate || "2026-10-26";
  let timeZone = DEFAULT_SCHEDULE_DATA.timeZone || "America/Sao_Paulo";

  // Check inline script element if any
  const inlineDataEl = document.getElementById("complete-program-data");
  if (inlineDataEl && inlineDataEl.textContent) {
    try {
      const json = JSON.parse(inlineDataEl.textContent);
      if (json.section || json.groups) sectionData = json.section || json;
      if (json.eventDate) eventDate = json.eventDate;
      if (json.timeZone) timeZone = json.timeZone;
    } catch (e) {}
  }

  setupViewSelector({
    selectorEl: selector,
    groupsContainerEl: groupsContainer,
    sectionData,
    eventDate,
    timeZone,
    defaultMode: "shift",
    initialShiftHtml,
  });

  // Background fetch to refresh if server has updated schedule
  (async () => {
    try {
      let dataUrl = "./static/data/schedule-data.json";
      if (typeof document !== "undefined" && document.currentScript && document.currentScript.src) {
        dataUrl = new URL("../data/schedule-data.json", document.currentScript.src).href;
      }
      const res = await fetch(dataUrl);
      if (res.ok) {
        const json = await res.json();
        const updatedSection = json.section || json;
        if (json.eventDate) eventDate = json.eventDate;
        if (json.timeZone) timeZone = json.timeZone;
        setupViewSelector({
          selectorEl: selector,
          groupsContainerEl: groupsContainer,
          sectionData: updatedSection,
          eventDate,
          timeZone,
          defaultMode: selector.querySelector('[aria-checked="true"]')?.getAttribute("data-schedule-view") || "shift",
          initialShiftHtml,
        });
      }
    } catch (e) {}
  })();
}

// Robust execution whether script is deferred, loaded after DOM, or as module
if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initCompleteProgram);
  } else {
    initCompleteProgram();
  }
}

// Expose exports globally and to CommonJS if present
if (typeof window !== "undefined") {
  window.CompleteProgram = {
    DEFAULT_SCHEDULE_DATA,
    KNOWLEDGE_AXES,
    SHIFTS,
    deriveShiftView,
    deriveAxisView,
    renderGroups,
    setupViewSelector,
    initCompleteProgram,
  };
}
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    DEFAULT_SCHEDULE_DATA,
    KNOWLEDGE_AXES,
    SHIFTS,
    deriveShiftView,
    deriveAxisView,
    renderGroups,
    setupViewSelector,
    initCompleteProgram,
  };
}
