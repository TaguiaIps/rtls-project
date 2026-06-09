# Plano de Implantação e Testes Contínuos (RTLS Analytics Platform)

Este documento detalha a estratégia de CI/CD, as ferramentas de automação e as recomendações futuras para garantir a entrega contínua e a estabilidade da plataforma.

## 🏗️ Estrutura de Automação Atual

Foram criados os seguintes scripts em `tools/` para facilitar o ciclo de vida local e em produção:

- **`tools/build.sh`**: Orquestra a instalação de dependências, build do frontend, linting do backend e geração de imagens Docker.
- **`tools/migrate.sh`**: Garante que o banco de dados esteja pronto, aplica o schema automaticamente e permite o bootstrap do administrador inicial.
- **`tools/deploy.sh`**: O ponto de entrada principal para subir a stack completa usando Docker Compose, garantindo que o banco de dados esteja inicializado corretamente.

## 🚀 Estratégia de CI/CD Sugerida

Para habilitar a entrega contínua, recomenda-se a configuração de um pipeline no GitHub Actions (já iniciado em `.github/workflows/ci.yml`):

### 1. Pipeline de Integração Contínua (CI)
- **Gatilho:** Push ou Pull Request para a branch `main`.
- **Etapas:**
  - Linting (Ruff para Python, ESLint/Prettier para JS/TS).
  - Testes Unitários e de Integração (Pytest para API, Vitest para Web/Mobile).
  - Build de Contêineres (Verificar se os Dockerfiles continuam válidos).

### 2. Pipeline de Entrega Contínua (CD)
- **Gatilho:** Merge bem-sucedido na branch `main`.
- **Etapas:**
  - Build e Push de imagens para um Registro de Imagens (ex: GitHub Container Registry - GHCR).
  - Deploy em ambiente de Staging (usando `tools/deploy.sh` remotamente via SSH ou Runner).
  - Notificação de sucesso no Slack/Discord.

---

## 🛠️ Recomendações Adicionais

### 1. Gerenciamento de Migrações (Alembic)
Embora o sistema atual use `Base.metadata.create_all()`, para produção recomenda-se migrar para **Alembic**.
- **Por que:** Permite alterações de schema sem perda de dados e rastreamento de histórico de mudanças no banco.
- **Ação:** Atualizar `tools/migrate.sh` para rodar `alembic upgrade head`.

### 2. Ambiente de Staging vs. Produção
Utilize arquivos `.env` específicos para cada ambiente.
- O arquivo `.env.example` deve ser atualizado com as variáveis mínimas necessárias para produção (ex: `RTLS_DATABASE_URL` externo, segredos JWT).

### 3. Monitoramento e Observabilidade
- **Logs:** Centralizar logs usando ELK Stack ou serviços como Datadog/Sentry.
- **Métricas:** Aproveitar o endpoint `/api/metrics` (Prometheus) já previsto na arquitetura para monitorar a saúde da API.

### 4. Testes End-to-End (E2E)
- Implementar testes E2E com **Playwright** ou **Cypress** para validar os fluxos críticos (ex: visualização do Live Map, criação de regras de alerta).
- Adicionar um script `tools/test-e2e.sh`.

### 5. Segurança no Pipeline
- Adicionar scanners de vulnerabilidades em dependências (ex: `npm audit`, `safety` para Python).
- Verificar segredos expostos usando ferramentas como `git-secrets` ou o scanner nativo do GitHub.

---

## 📋 Próximos Passos Imediatos

1. **Configurar Segredos do GitHub:** Adicionar as chaves de acesso ao registro de imagens e chaves SSH de deploy.
2. **Validar Localmente:** Rodar `./tools/deploy.sh` em uma máquina limpa para garantir que a orquestração está 100% funcional.
3. **Documentar Configuração de Hardware:** Adicionar um runbook específico para o comissionamento físico dos Gateways e Beacons.

---

*Gerado em: Março 2026*
