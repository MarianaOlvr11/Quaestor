# Quaestor

Assistente educacional para identificar o perfil de investidor (conservador, moderado ou arrojado) e montar carteiras simuladas, usando o **Claude Haiku 5.5** com regras programadas.

> Projeto acadêmico — IFSP Pirituba, TADS 6º semestre. Não é recomendação de investimento e não movimenta dinheiro real.

## Estrutura

```
quaestor/
├── frontend/          # interface web (HTML, CSS e JS puros)
│   ├── index.html
│   ├── styles.css
│   ├── app.js         # chat, painel de perfil/carteira e modo demonstração
│   ├── icons/         # ícones Glass (withicons, MIT — ver icons/LICENSE)
│   └── img/           # ícone do app, favicon e moeda
└── backend/           # (próxima etapa) FastAPI + Claude Haiku 5.5 + regras
```

## Rodar o frontend

Sem backend, a interface entra em **modo demonstração** (respostas roteirizadas, sem chamar o modelo).

```bash
python -m http.server 5173 --directory frontend
```

Abra http://localhost:5173.

O contrato esperado da rota `POST /api/chat` está descrito no início de `frontend/app.js`.
