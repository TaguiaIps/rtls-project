# Real-Time Location System - rtls-project

## System Architecture Document

### Author: Hugo de Paula

### 2025-03-18

## Histórico de Revisões

| **Data**      | **Autor**      | **Descrição**                      | **Versão** |
|---------------|----------------|------------------------------------|------------|
| 2025-03-16    | Hugo de Paula  | Estrutura inicial do documento     | 1.0        |
| 2025-03-18    | Hugo de Paula  | Definição inicial do projeto IPS   | 1.1        |

## SUMÁRIO

1. [Produto](#produto "Produto")
    1. Definições e Abreviaturas  
    2. Personas  
    3. Histórias de Usuário  
2. [Requisitos](#requisitos "Requisitos")
    1. Requisitos Funcionais  
    2. Requisitos Não-Funcionais  
    3. Restrições Arquiteturais  
    4. Mecanismos Arquiteturais  

---

<a name="produto"></a>

## 1. Produto

Este documento apresenta a descrição arquitetural do sistema de posicionamento indoor (IPS) baseado em Bluetooth Low Energy (BLE), utilizando a abordagem Real-time Location Tracking (RTLS). Ambientes fechados como hospitais, centros comerciais, aeroportos e grandes empresas enfrentam dificuldades significativas em localizar rapidamente ativos e pessoas devido à limitação do GPS em espaços internos.

---

## 1.1. Definições e Abreviaturas

| Termo         | Definição                                             |
|---------------|-------------------------------------------------------|
| AES-256       | Advanced Encryption Standard com chave de 256 bits |
| BLE           | Bluetooth Low Energy                           |
| ELK Stack     | Conjunto de ferramentas Elasticsearch, Logstash e Kibana |
| IPS           | Indoor Positioning System                      |
| JWT           | JSON Web Token                                 |
| MFA           | Multi-Factor Authentication                    |
| OAuth2        | Protocolo de autenticação seguro               |
| ORM           | Object-Relational Mapping                      |
| RBAC          | Role-Based Access Control                      |
| RSSI          | Received Signal Strength Indicator             |
| RTLS          | Real-time Location System                      |
| SPA           | Single Page Application                        |
| TLS           | Transport Layer Security                       |
| Trilateração  | Método matemático para determinar posição baseado na distância entre pontos conhecidos |
| WCL           | Weighted Centroid Localization                 |

---

## 1.2. Personas

### Persona 1

| Nome           | Carlos Mendes                                |
|----------------|----------------------------------------------|
| Idade          | 48 anos                                      |
| Hobby          | Corrida                                      |
| Trabalho       | Gerente operacional hospitalar               |
| Personalidade  | Organizado, prático, exigente                |
| Sonho          | Otimizar processos da empresa                |
| Dores          | Dificuldade em localizar rapidamente equipamentos e pessoas |

## 1.3. Histórias de Usuário

| EU COMO... `PERSONA`      | QUERO/PRECISO ... `FUNCIONALIDADE`                           | PARA ... `MOTIVO/VALOR`                                 |
|---------------------------|--------------------------------------------------------------|---------------------------------------------------------|
| Carlos Mendes             | Visualizar rapidamente localização dos colegas no escritório.| Facilitar reuniões presenciais rápidas                  |
| Carlos Mendes             | Receber notificações sobre localização dos equipamentos.     | Reduzir tempo gasto na busca dos equipamentos           |
| Administrador do Sistema  | Gerenciar cadastro dos beacons instalados no ambiente indoor.| Garantir cobertura adequada e manutenção preventiva     |

---

<a name="requisitos"></a>

## 2. Requisitos

## 2.1 Requisitos Funcionais (RF)

**Status: | ✅ = Implementado | ❌ = Não Implementado | 🔄 = Em Andamento |**

| ID    | Descrição                                                       | Prioridade   | Plataforma    | Sprint     | Status |
|-------|-----------------------------------------------------------------|--------------|---------------|------------|--------|
| RF001 | Permitir rastreamento em tempo real dos ativos e pessoas        | Essencial    | Web e Mobile  | Sprint 1   | ❌    |
| RF002 | Exibir a localização em tempo real dos ativos e pessoas         | Essencial    | Web e Mobile  | Sprint 1   | ❌    |
| RF003 | Enviar notificações automáticas sobre localização               | Essencial    | Mobile        | Sprint 1   | ❌    |
| RF004 | Gerenciar cadastro e configuração dos beacons                   | Essencial    | Web e Mobile  | Sprint 1   | ❌    |
| RF005 | Implementar algoritmos de posicionamento, como trilateração ou Weighted Centroid Localization (WCL) | Essencial      | Backend              | Sprint 2   | ❌          |
| RF006 | Autenticar usuários com métodos seguros (OAuth2/JWT)            | Essencial    | Web e Mobile  | Sprint 3   | ❌    |
| RF007 | Permitir controle tipo RBAC - _Role-Based Access Control_       | Essencial    | Web           | Sprint 3   | ❌    |
| RF008 | Registrar logs estruturados das operações dos usuários          | Essencial    | Web e Backend | Sprint 4   | ❌    |
| RF009 | Registrar logs estruturados das operações dos dispositivos      | Essencial    | Web e Backend | Sprint 4   | ❌    |
| RF010 | Exibir histórico das localizações dos ativos                    | Desejável    | Web           | Sprint 5   | ❌    |
| RF011 | Realizar backups criptografados periódicos                      | Desejável    | Backend       | Sprint 5   | ❌    |
| RF012 | Fornecer monitoramento em tempo real de eventos e incidentes de segurança | Desejável   | Web          | Sprint 5     | ❌    |
| RF013 | Definir alertas de movimento inesperado ou perda de sinal de ativos  | Desejável      | Mobile               | Sprint 5     | ❌          |

---

## 2.2 Requisitos Não-Funcionais (RNF)

| ID     | Descrição                                                                                           |
|--------|-----------------------------------------------------------------------------------------------------|
| RNF001 | Precisão mínima na localização: ±2 metros                                                           |
| RNF002 | Tempo máximo atualização das posições: até 5 segundos                                               |
| RNF003 | Vida útil mínima das baterias dos beacons: ≥2 anos                                                  |
| RNF004 | Escalabilidade para suportar até 500 beacons simultaneamente                                        |
| RNF004 | As comunicações entre dispositivos móveis, beacons e backend devem utilizar criptografia forte (TLS v1.3 ou superior) |
| RNF005 | Armazenar os dados criptografados utilizando AES-256                                                |
| RNF006 | Garantir autenticação multifatorial (MFA) para acessos administrativos e críticos                   |
| RNF007 | Anonimização ou pseudonimização dos dados pessoais coletados, garantindo privacidade por padrão ("Privacy by Design") |
| RNF008 | Realizar testes automatizados de segurança (análise estática, testes de penetração) antes de cada release em produção |
| RNF009 | O tempo máximo para detecção e notificação automática de incidentes ou tentativas suspeitas de acesso não autorizado ao sistema não pode ultrapassar 5 minutos após o evento |
| RNF010 | Os backups realizados devem ser armazenados em local seguro, isolado fisicamente do ambiente principal, com retenção mínima de 30 dias |

## 2.3 Restrições Arquiteturais

- O sistema deve utilizar BLE (Bluetooth Low Energy) como tecnologia principal.
- A comunicação entre os dispositivos móveis e os beacons deve ser baseada no protocolo padrão BLE Advertising.
- A aplicação web deve seguir arquitetura RESTful para comunicação com o backend.
- O backend deve ser desenvolvido utilizando Python/Django.

## 2.4 Mecanismos Arquiteturais

### Aplicação web

| **Análise**                  | **Design**                         | **Implementação**                           |
|------------------------------|------------------------------------|---------------------------------------------|
| Persistência                 | ORM                                | Django ORM                                  |
| Front end                    | SPA Framework                      | React.js                                    |
| Back end                     | Framework Web                      | Django REST Framework                       |
| Integração                   | API RESTful                        | Django REST Framework                       |
| Log do sistema               | Logging estruturado                | ELK Stack (Elasticsearch, Logstash, Kibana) |
| Teste de Software            | Testes automatizados               | PyTest                                      |
| Deploy                       | Containerização                    | Docker/Kubernetes                           |

### Aplicação móvel

O mecanismo arquitetural para a aplicação mobile do sistema IPS baseado em BLE será projetado para garantir eficiência, precisão e segurança na coleta e processamento dos dados de localização. A arquitetura será composta por componentes e tecnologias que suportem o rastreamento em tempo real, com foco na integração entre os dispositivos móveis e os beacons BLE. Abaixo está uma descrição detalhada do mecanismo arquitetural:

## **Mecanismo Arquitetural para Aplicação Mobile**

| **Análise**                  | **Design**                         | **Implementação**                            |
|------------------------------|------------------------------------|----------------------------------------------|
| **Captura de Sinais BLE**    | API Bluetooth nativa               | Android API Bluetooth ou CoreBluetooth (iOS) |
| **Filtragem de RSSI**        | Mediana ou Média Móvel             | Flutter                                      |
| **Estimativa de Distância**  | Modelo de perda de caminho logarítmico (Log-Distance Path Loss) | Biblioteca matemática local no app para cálculo em tempo real |
| **Posicionamento**           | Trilateração ou Weighted Centroid Localization (WCL) | Algoritmo embutido no aplicativo para cálculo local |
| **Interface do Usuário**     | Mapas interativos com posição em tempo real | Frameworks como Google Maps SDK ou Mapbox SDK |
| **Segurança**                | Autenticação OAuth2/JWT e criptografia TLS v1.3 | Integração com backend seguro via API RESTful |
| **Notificações**             | Sistema de alertas push baseado na localização | Firebase Cloud Messaging ou Apple Push Notification Service |

### **Descrição dos Componentes**

1. **Captura de Sinais BLE:**
   - O aplicativo móvel será responsável por escanear os sinais BLE transmitidos pelos beacons próximos.
   - A captura será feita utilizando APIs nativas da plataforma, como Android Bluetooth API ou CoreBluetooth no iOS.

2. **Filtragem de RSSI:**
   - Para reduzir variações nos valores RSSI, o aplicativo aplicará algoritmos como mediana ou média móvel.
   - Essa filtragem melhora a precisão na estimativa da distância.

3. **Estimativa de Distância:**
   - O modelo logarítmico de perda de caminho será usado para calcular a distância entre o smartphone e os beacons com base nos valores RSSI filtrados.

4. **Posicionamento:**
   - Métodos como trilateração ou WCL serão implementados diretamente no aplicativo para calcular a posição do usuário.
   - Esses algoritmos utilizam as distâncias estimadas dos beacons mais próximos.

5. **Interface do Usuário:**
   - O aplicativo exibirá um mapa interativo mostrando a localização do usuário em tempo real.
   - Frameworks como Google Maps SDK ou Mapbox SDK serão utilizados para renderizar mapas indoor.

6. **Segurança:**
   - Todo tráfego entre o aplicativo e o backend será protegido por TLS v1.3.
   - Autenticação segura será implementada usando OAuth2 ou JWT.

7. **Notificações:**
   - O sistema enviará notificações automáticas ao usuário sobre eventos relevantes (ex.: movimento inesperado ou perda de sinal).
   - Serviços como Firebase Cloud Messaging ou Apple Push Notification Service serão integrados.
