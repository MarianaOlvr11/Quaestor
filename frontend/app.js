/* =========================================================
   Quaestor — lógica da interface
   ---------------------------------------------------------
   Contrato esperado do backend (a implementar em Python):

   POST /api/chat
     { "session_id": "...", "message": "texto do usuário" }
   200 →
     {
       "reply": "texto do assistente",
       "citations": [{ "titulo": "Tesouro Direto", "url": "https://..." }],
       "perfil": {
         "campos": { "objetivo": "...", "horizonte": "...", ... },   // null = ainda não coletado
         "classificacao": "conservador" | "moderado" | "arrojado" | null
       },
       "carteira": {
         "itens": [{ "produto": "...", "pct": 40, "justificativa": "..." }],
         "bloqueados": [{ "produto": "...", "motivo": "..." }]
       } | null
     }

   Enquanto o backend não existir, a interface entra em
   "Modo demonstração" com respostas roteirizadas (sem LLM).
   ========================================================= */

const FIELDS = [
  { key: "objetivo", label: "Objetivo" },
  { key: "horizonte", label: "Horizonte de investimento" },
  { key: "experiencia", label: "Experiência" },
  { key: "liquidez", label: "Necessidade de liquidez" },
  { key: "perdas", label: "Capacidade de suportar perdas" },
  { key: "tolerancia", label: "Tolerância ao risco" },
];
const COLORS = ["#c08a2a", "#e5bd68", "#3a3833", "#9a968f", "#8a5f1c"];

const $ = (s) => document.querySelector(s);
const app = $("#app");
const chat = $("#chat");
const input = $("#input");
const form = $("#composer");
const sendBtn = $("#sendBtn");

const state = {
  sessionId: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
  busy: false,
  demo: false,
  perfil: { campos: {}, classificacao: null },
  carteira: null,
};

let chatInner = null;

/* ---------------- views ---------------- */
function setView(view) {
  app.dataset.view = view;
  if (view === "chat" && !chatInner) {
    chatInner = document.createElement("div");
    chatInner.className = "chat-inner";
    chat.appendChild(chatInner);
  }
  // em telas largas o painel abre sozinho quando a conversa começa
  if (view === "chat" && window.matchMedia("(min-width: 1281px)").matches) setPanel(true);
}
function setPanel(open) {
  if (open) app.dataset.panel = "open";
  else delete app.dataset.panel;
}
function setDrawer(open) {
  if (open) app.dataset.drawer = "open";
  else delete app.dataset.drawer;
  $("#scrim").hidden = !open;
}
function resetChat() {
  // nova sessão no servidor: a conversa anterior não é reaproveitada
  state.sessionId = crypto.randomUUID ? crypto.randomUUID() : String(Date.now());
  chat.innerHTML = "";
  chatInner = null;
  state.perfil = { campos: {}, classificacao: null };
  state.carteira = null;
  demo.step = 0;
  renderPanel();
  setPanel(false);
  app.dataset.view = "home";
  input.value = "";
  autosize();
}

/* ---------------- mensagens ---------------- */
function addMessage(role, text, opts = {}) {
  const msg = document.createElement("div");
  msg.className = `msg ${role}`;
  if (role === "bot") {
    const av = document.createElement("div");
    av.className = "avatar";
    av.innerHTML = '<img class="coin" src="img/quaestor-coin.webp" alt="">';
    msg.appendChild(av);
  }
  const wrap = document.createElement("div");
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text; // textContent: nunca interpreta HTML vindo do modelo
  wrap.appendChild(bubble);

  if (opts.citations?.length) {
    const cites = document.createElement("div");
    cites.className = "cites";
    for (const c of opts.citations) {
      const a = document.createElement("a");
      a.className = "cite";
      a.href = c.url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.innerHTML = '<svg viewBox="0 0 24 24"><path d="M2 5.5C4.5 4 8 4 12 6c4-2 7.5-2 10-.5V19c-2.5-1.5-6-1.5-10 .5-4-2-7.5-2-10-.5z"/><path d="M12 6v13.5"/></svg>';
      a.append(`Fonte: ${c.titulo}`);
      cites.appendChild(a);
    }
    wrap.appendChild(cites);
  }
  if (opts.showPanelBtn) {
    const b = document.createElement("button");
    b.className = "pill-btn";
    b.style.marginTop = "10px";
    b.textContent = "Ver perfil e carteira";
    b.addEventListener("click", () => setPanel(true));
    wrap.appendChild(b);
  }
  msg.appendChild(wrap);
  chatInner.appendChild(msg);
  requestAnimationFrame(() => chat.scrollTo({ top: chat.scrollHeight }));
}
function showStatus() {
  const s = document.createElement("div");
  s.className = "status";
  s.id = "status";
  s.innerHTML = '<img class="coin spinning" src="img/quaestor-coin.webp" alt=""> Quaestor está analisando<span class="dots"><i></i><i></i><i></i></span>';
  chatInner.appendChild(s);
  chat.scrollTop = chat.scrollHeight;
}
function hideStatus() { $("#status")?.remove(); }

/* ---------------- envio ---------------- */
async function send(text) {
  text = text.trim();
  if (!text || state.busy) return;
  setView("chat");
  addMessage("user", text);
  input.value = "";
  autosize();
  state.busy = true;
  sendBtn.disabled = true;
  showStatus();

  let res;
  try {
    res = await callApi(text);
  } catch {
    // sem backend (site estático): usa o modo demonstração roteirizado
    state.demo = true;
    $("#demoBadge").hidden = false;
    await new Promise((r) => setTimeout(r, 700 + Math.random() * 600));
    res = demo.respond(text);
  }

  hideStatus();
  if (res.erro) {
    // falha real do backend/modelo: avisa, sem inventar resposta
    addMessage("bot", `Não consegui responder agora (${res.erro}). Sua mensagem não foi registrada; tente enviar de novo em instantes.`);
  } else {
    const primeiraCarteira = !state.carteira && !!res.carteira;
    if (res.perfil) state.perfil = res.perfil;
    if (res.carteira) state.carteira = res.carteira;
    addMessage("bot", res.reply, { citations: res.citations, showPanelBtn: res.showPanelBtn ?? primeiraCarteira });
  }
  renderPanel();
  state.busy = false;
  sendBtn.disabled = false;
  input.focus();
}

async function callApi(text) {
  if (state.demo) throw new Error("demo");
  const r = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: state.sessionId, message: text }),
  });
  // 404/405/501: não há backend (ex.: servidor estático) → modo demonstração
  if ([404, 405, 501].includes(r.status)) throw new Error(`sem backend (HTTP ${r.status})`);
  if (!r.ok) {
    const corpo = await r.json().catch(() => ({}));
    return { erro: corpo.erro || (r.status === 422 ? "mensagem inválida ou longa demais" : `erro ${r.status}`) };
  }
  return r.json();
}

/* ---------------- painel ---------------- */
function renderPanel() {
  const { campos, classificacao } = state.perfil;
  const filled = FIELDS.filter((f) => campos[f.key]).length;
  $("#progressBar").style.width = `${(filled / FIELDS.length) * 100}%`;

  const pv = $("#profileValue");
  pv.textContent = classificacao ? cap(classificacao) : filled ? `Em análise · ${filled}/${FIELDS.length}` : "Em análise…";
  pv.classList.toggle("done", !!classificacao);

  const ul = $("#fields");
  ul.innerHTML = "";
  for (const f of FIELDS) {
    const li = document.createElement("li");
    const ok = !!campos[f.key];
    li.className = ok ? "ok" : "";
    li.innerHTML = `<span class="chk">${ok ? '<svg viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>' : ""}</span>`;
    const t = document.createElement("div");
    t.textContent = f.label;
    if (ok) {
      const v = document.createElement("span");
      v.className = "val";
      v.textContent = campos[f.key];
      t.appendChild(v);
    }
    li.appendChild(t);
    ul.appendChild(li);
  }

  const c = state.carteira;
  const has = !!c?.itens?.length;
  $("#portfolioEmpty").hidden = has;
  $("#donutWrap").hidden = !has;
  const alloc = $("#alloc");
  alloc.innerHTML = "";
  const donut = $("#donut");
  donut.innerHTML = '<circle cx="21" cy="21" r="15.915" stroke="rgba(40,36,30,0.07)"></circle>';
  if (has) {
    let acc = 0;
    c.itens.forEach((it, i) => {
      const color = COLORS[i % COLORS.length];
      const circ = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circ.setAttribute("cx", "21");
      circ.setAttribute("cy", "21");
      circ.setAttribute("r", "15.915");
      circ.setAttribute("stroke", color);
      circ.setAttribute("stroke-dasharray", `${Math.max(it.pct - 0.8, 0)} ${100 - it.pct + 0.8}`);
      circ.setAttribute("stroke-dashoffset", String(-acc));
      donut.appendChild(circ);
      acc += it.pct;

      const li = document.createElement("li");
      li.innerHTML = `<span class="dot" style="background:${color}"></span>`;
      const name = document.createElement("span");
      name.textContent = it.produto;
      const pct = document.createElement("span");
      pct.className = "pct";
      pct.textContent = `${it.pct}%`;
      const why = document.createElement("span");
      why.className = "why";
      why.textContent = it.justificativa;
      li.append(name, pct, why);
      alloc.appendChild(li);
    });
  }

  const blk = c?.bloqueados || [];
  $("#blockedCard").hidden = !blk.length;
  const bl = $("#blocked");
  bl.innerHTML = "";
  for (const b of blk) {
    const li = document.createElement("li");
    li.textContent = b.produto;
    const s = document.createElement("span");
    s.textContent = b.motivo;
    li.appendChild(s);
    bl.appendChild(li);
  }
}
const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);

/* ---------------- modo demonstração (sem LLM) ---------------- */
const SRC = {
  cvm: { titulo: "Portal do Investidor (CVM)", url: "https://www.gov.br/investidor/pt-br" },
  tesouro: { titulo: "Tesouro Direto", url: "https://www.tesourodireto.com.br" },
  anbima: { titulo: "ANBIMA – Como Investir", url: "https://comoinvestir.anbima.com.br" },
  fgc: { titulo: "FGC", url: "https://www.fgc.org.br" },
};
const QUESTIONS = [
  "Vamos lá! Para começar: qual é o principal objetivo desse dinheiro? (ex.: reserva de emergência, comprar um imóvel, aposentadoria)",
  "Entendi. Em quanto tempo você pretende usar esse dinheiro?",
  "Você já investiu antes? Em quê?",
  "Você pode precisar resgatar parte desse valor de repente, antes do prazo?",
  "Se seus investimentos caíssem 15% em um mês, como isso afetaria sua vida financeira?",
  "Última pergunta: diante dessa queda, o que você faria — resgataria tudo, esperaria ou investiria mais?",
];
const demo = {
  step: 0,
  respond(text) {
    const t = text.toLowerCase();
    const campos = { ...state.perfil.campos };

    if (t.includes("liquidez")) {
      return {
        reply: "Liquidez é a facilidade de transformar um investimento em dinheiro disponível, sem perder valor por isso.\n\nUm Tesouro Selic, por exemplo, pode ser resgatado em qualquer dia útil. Já um CDB com carência só pode ser resgatado após a data combinada.\n\nPor isso, a reserva de emergência costuma ficar em aplicações de alta liquidez.",
        citations: [SRC.cvm, SRC.tesouro],
      };
    }
    if (t.includes("renda fixa") || t.includes("variável") || t.includes("variavel")) {
      return {
        reply: "Na renda fixa, as regras de remuneração são definidas na aplicação (ex.: um percentual do CDI ou IPCA + taxa). Na renda variável, como ações, o retorno depende do mercado e pode ser negativo.\n\n“Fixa” não significa sem risco: títulos prefixados oscilam de preço se vendidos antes do vencimento.",
        citations: [SRC.anbima],
      };
    }
    if (t.includes("carteira") && !state.perfil.classificacao) {
      this.step = 1;
      return {
        reply: "Para montar uma carteira simulada eu preciso primeiro conhecer seu perfil — é uma regra do simulador.\n\n" + QUESTIONS[0],
        perfil: { campos, classificacao: null },
      };
    }

    if (this.step === 0) {
      this.step = 1;
      return { reply: QUESTIONS[0], perfil: { campos, classificacao: null } };
    }
    if (this.step <= FIELDS.length) {
      campos[FIELDS[this.step - 1].key] = text.length > 60 ? text.slice(0, 57) + "…" : text;
      this.step++;
      if (this.step <= FIELDS.length) {
        return { reply: QUESTIONS[this.step - 1], perfil: { campos, classificacao: null } };
      }
      return {
        reply: "Pronto! Pelas regras do simulador, seu perfil é Moderado: você tem prazo médio, aceita alguma oscilação, mas ainda precisa de parte do dinheiro disponível.\n\nMontei uma carteira simulada com produtos compatíveis. Ações de empresas pequenas ficaram de fora porque não combinam com seu prazo e sua tolerância a perdas.",
        citations: [SRC.cvm],
        showPanelBtn: true,
        perfil: { campos, classificacao: "moderado" },
        carteira: {
          itens: [
            { produto: "Tesouro Selic", pct: 35, justificativa: "Alta liquidez para a parte que você pode precisar resgatar." },
            { produto: "CDB liquidez diária", pct: 20, justificativa: "Renda fixa coberta pelo FGC, dentro dos limites." },
            { produto: "Tesouro IPCA+", pct: 25, justificativa: "Protege do aumento de preços no médio prazo." },
            { produto: "Fundo multimercado", pct: 12, justificativa: "Diversificação com risco moderado." },
            { produto: "ETF de ações (Ibovespa)", pct: 8, justificativa: "Pequena exposição à renda variável, diversificada." },
          ],
          bloqueados: [
            { produto: "Ações small caps", motivo: "Risco alto, incompatível com perfil moderado e prazo informado." },
            { produto: "Criptoativos", motivo: "Fora do catálogo revisado do simulador." },
          ],
        },
      };
    }
    if (t.includes("ignore") || t.includes("libera") || t.includes("quero ações") || t.includes("small")) {
      return { reply: "Não posso incluir esse produto: as regras do simulador bloqueiam itens incompatíveis com o seu perfil. Se suas informações mudaram, você pode revisar suas respostas e eu recalculo o perfil." };
    }
    return { reply: "Este é o modo demonstração, com respostas roteirizadas. Quando o backend estiver conectado, as respostas virão do Claude Haiku 5.5 com base no conteúdo revisado." };
  },
};

/* ---------------- eventos ---------------- */
function autosize() {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 160) + "px";
  // barra de rolagem só quando o texto passa da altura máxima
  input.style.overflowY = input.scrollHeight > 160 ? "auto" : "hidden";
}
input.addEventListener("input", autosize);
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    form.requestSubmit();
  }
});
form.addEventListener("submit", (e) => {
  e.preventDefault();
  send(input.value);
});
document.querySelectorAll(".suggestion").forEach((b) =>
  b.addEventListener("click", () => send(b.dataset.prompt))
);
document.querySelectorAll("[data-action]").forEach((b) =>
  b.addEventListener("click", () => {
    const a = b.dataset.action;
    setDrawer(false);
    if (a === "new-chat") resetChat();
    if (a === "open-panel") setPanel(true);
    if (a === "about") $("#aboutModal").showModal();
  })
);
$("#newChatTop").addEventListener("click", resetChat);
$("#togglePanel").addEventListener("click", () => setPanel(app.dataset.panel !== "open"));
$("#closePanel").addEventListener("click", () => setPanel(false));
$("#openDrawer").addEventListener("click", () => setDrawer(true));
$("#closeDrawer").addEventListener("click", () => setDrawer(false));
$("#scrim").addEventListener("click", () => setDrawer(false));
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") { setDrawer(false); setPanel(false); }
});

if (window.matchMedia("(max-width: 820px)").matches) input.placeholder = "Pergunte algo ao Quaestor…";

/* ---------------- liquid glass ---------------- */
// brilho que acompanha o cursor dentro das superfícies de vidro
document.addEventListener("pointermove", (e) => {
  const el = e.target.closest?.(".suggestion, .composer, .icon-btn, .pill-btn, .nav-item, .card");
  if (!el) return;
  const r = el.getBoundingClientRect();
  el.style.setProperty("--mx", `${e.clientX - r.left}px`);
  el.style.setProperty("--my", `${e.clientY - r.top}px`);
});
// refração real só onde o navegador suporta filtro SVG em backdrop-filter (Chrome/Edge)
const isChromium = !!navigator.userAgentData?.brands?.some((b) => /Chromium/i.test(b.brand));
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
if (isChromium && !reduceMotion) document.documentElement.classList.add("refract");
renderPanel();
