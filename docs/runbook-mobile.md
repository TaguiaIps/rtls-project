# RTLS Analytics Platform - Mobile Runbook

Este documento fornece instruções passo a passo para construir, testar e distribuir o aplicativo móvel RTLS usando as ferramentas mais modernas do ecossistema Expo.

## 📱 Tecnologias Principais
- **Framework:** Expo (React Native SDK 50+)
- **Build & Cloud:** EAS (Expo Application Services)
- **Scanner:** Expo Camera (v2)
- **Contratos:** `@rtls/contracts` (TypeScript)

---

## 🏗️ 1. Preparação do Ambiente

### 🖥️ Pré-requisitos
- **Node.js:** Versão LTS recomendada (>= 20.x).
- **NPM:** Instalado globalmente.
- **EAS CLI (Obrigatório para build/deploy):**
  ```bash
  npm install -g eas-cli
  ```
  > **Nota:** Não instale o `expo-cli` globalmente. Ele é obsoleto e gera conflitos. Sempre use `npx expo`.

### 📦 Instalação de Dependências
Na raiz do monorepo, execute:
```bash
make js-install
```

---

## 🧪 2. Testes e Validação

### 🔍 Linting e Typechecking
Para verificar a qualidade do código antes de qualquer build:
```bash
npm run lint --workspace apps/mobile
npm run build --workspace apps/mobile
```

### 🧪 Executar Testes Unitários
Para executar os testes automatizados do aplicativo:
```bash
npm run test --workspace apps/mobile
```

---

## 🚀 3. Desenvolvimento Local

### 🛠️ Iniciar Servidor de Desenvolvimento
Para rodar o aplicativo localmente com o **Expo Go**:
```bash
npm run start --workspace apps/mobile
```
ou, se preferir entrar na pasta:
```bash
cd apps/mobile && npx expo start
```
- Pressione `r` para recarregar o bundle.
- Pressione `j` para abrir o menu do debugger.

---

## 📦 4. Build de Distribuição e Deploy

Agora utilizamos scripts facilitadores para garantir consistência:

### ⚡ Deploy Interno (Preview)
Gera um build que pode ser instalado via QR Code no dispositivo para testes:
```bash
./tools/mobile-deploy.sh preview
```

### 🚀 Atualizações OTA (Over-The-Air)
Envia correções de JavaScript sem precisar reinstalar o app no celular:
```bash
./tools/mobile-deploy.sh update "Conserto de bug no scanner"
```

### 💎 Build de Produção
Gera o pacote final (AAB para Android, IPA para iOS) pronto para as lojas:
```bash
./tools/mobile-deploy.sh production
```

---

## 🛠️ 5. Troubleshooting (Resolução de Problemas)

- **Erro de Porta 8081 em uso:** Se você encontrar esse erro, use:
  ```bash
  npm run start --workspace apps/mobile -- --port 8082
  ```
- **Conflito com Docker:** Se o Docker estiver rodando serviços de mapa ou API, execute:
  ```bash
  docker compose stop
  ```
- **Erro de Resolução (Metro/Monorepo):** Se encontrar `Cannot find module 'metro-runtime/package.json'`, certifique-se de que o pacote `metro-runtime` está listado nas dependências do `apps/mobile/package.json` (isso força a resolução correta dentro da estrutura de workspaces).

---

*Última atualização: Abril 2026*
