# 🚀 Briefing IA

Transforme qualquer vídeo em um **briefing profissional de edição**, automaticamente.

O sistema analisa áudio, imagens e contexto do vídeo para gerar **roteiros, cortes e sugestões criativas** — reduzindo drasticamente o tempo de produção de conteúdo.

---

## 🎯 Problema

Criadores, editores e agências perdem tempo analisando vídeos manualmente para:

* definir estrutura
* identificar pontos de corte
* pensar em narrativa
* gerar ideias de melhoria

---

## 💡 Solução

O **Briefing IA** automatiza esse processo com um pipeline completo de IA:

1. Upload de vídeo
2. Extração de áudio com FFmpeg
3. Transcrição automática (OpenAI / Whisper)
4. Captura de frames (snapshots)
5. Análise multimodal (texto + imagem)
6. Geração de recomendações estruturadas

---

## 🧠 Saída gerada

* Estrutura de roteiro (hook, intro, desenvolvimento, CTA)
* Sugestões de cortes e ritmo
* Ideias de B-roll e elementos visuais
* Recomendações estratégicas de melhoria

---

## ⚙️ Stack

* **Backend:** FastAPI
* **Banco/Auth/Storage:** Supabase
* **Processamento de vídeo:** FFmpeg
* **IA:** OpenAI (transcrição + análise)
* **Linguagem:** Python

---

## 🏗️ Arquitetura

```bash
app/
├── routers/       # Endpoints da API
├── services/      # Regras de negócio (IA, FFmpeg, Supabase)
├── models/        # Schemas e validações
├── core/          # Configurações e inicialização
├── utils/         # Funções auxiliares
```

---

## ⚡ Pipeline (visão técnica)

```text
Upload → Storage → FFmpeg → Transcription → Snapshots → IA → Recommendations → Persistência
```

* Processamento assíncrono
* Integração com storage via signed URL
* Separação por usuário (RLS)
* Fallbacks para compatibilidade de schema

---

## ▶️ Como rodar localmente

```bash
python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

A API estará disponível em:

```
http://127.0.0.1:8000/docs
```

---

## 🔐 Variáveis de ambiente

Crie um arquivo `.env`:

```env
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
OPENAI_API_KEY=
```

---

## 📌 Diferenciais técnicos

* Pipeline completo de vídeo + IA
* Processamento assíncrono em background
* Análise multimodal (imagem + texto)
* Integração com storage externo (Supabase)
* Arquitetura organizada em camadas
* Sistema pronto para escalar para SaaS

---

## 🚧 Roadmap

* [ ] WebSocket para status em tempo real
* [ ] Export para Premiere / CapCut
* [ ] Fila distribuída (Redis / Celery)
* [ ] Dashboard analítico
* [ ] Upload direto do frontend

---

## 📸 Preview (em breve)

> Adicione aqui screenshots ou GIF do sistema rodando

---

## 👨‍💻 Autor

Projeto desenvolvido como MVP de produto SaaS com foco em automação de criação de conteúdo.
