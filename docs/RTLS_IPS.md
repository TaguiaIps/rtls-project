# RTLS/IPS para restaurantes e grandes operações de catering com aplicabilidade horizontal

## Resumo executivo

Você está tentando construir uma plataforma de **localização indoor em tempo real** (RTLS/IPS) que atenda **restaurantes e grandes operações de catering** (dinâmica de movimento intensa, ambientes com muita gente/metal/umidade/calor, necessidade de insights operacionais) e que também escale para **indústria**. Os benchmarks que você citou mostram um padrão consistente: o “produto vencedor” não é só um motor de posicionamento; é uma **plataforma de operação** com **mapas**, **alertas**, **analytics**, **integrações** e um **playbook de implantação**. Zapt enfatiza posicionamento/navegação em mapa, multi-sinalizadores e operação online/offline; também comunica acurácia de ~3 m para “blue-dot” e uso de beacons+reuso de infraestrutura (APs), além de baterias “até 5 anos”. [\[1\]](https://zapt.tech/solucoes/indoor-positioning/) Já a Novidá enfatiza **gestão operacional** com tracking e ganhos mensuráveis; em um case relata **leituras a cada 10 s** e “erro de menos de 1 metro” em ambiente complexo (hospital), apontando que o valor está em **processo + dashboard + análise**. [\[2\]](https://conteudo.novida.com.br/hcorcase)

Para o seu alvo (restaurantes/catering), a recomendação mais robusta é **uma arquitetura em camadas e agnóstica de hardware** com **dois tiers de precisão/custo**, mantendo o mesmo produto de software:

*   **Tier econômico (SMB / restaurantes pequenos)**: **BLE** com **RSSI + fingerprinting** (e/ou “zone-level”), gateways/anchors simples, atualização típica **0,5–2 Hz** por pessoa/ativo (configurável), visando **1–2 m em condições favoráveis** e **2–4 m em condições difíceis**, com boa UX e confiança estatística (confidence score) em vez de prometer “centímetros”.
*   **Tier premium (catering grande / indústria / requisitos de segurança)**: **BLE AoA (Bluetooth Direction Finding)** para sub‑metro quando bem implantado (com locators e antenas) [\[3\]](https://www.bluetooth.com/wp-content/uploads/Files/developer/RDF_Technical_Overview.pdf) e/ou **UWB** para precisão centimétrica via time-of-flight [\[4\]](https://www.qorvo.com/innovation/ultra-wideband/technology), com edge processing e alta taxa de atualização (p.ex. 5–20 Hz quando necessário, com duty-cycling para bateria).
*   **Cenários com smartphone como “tag”**: suportar, mas com ressalvas fortes. iOS até permite transformar o aparelho em iBeacon, porém a própria Apple recomenda isso para apps que já rodam em foreground; caso contrário, prefira hardware dedicado. [\[5\]](https://developer.apple.com/documentation/corelocation/turning-an-ios-device-into-an-ibeacon-device) No Android, comunicação BLE no background tem requisitos/limitações e geralmente exige foreground service para operação contínua. [\[6\]](https://developer.android.com/develop/connectivity/bluetooth/ble/background)

Tecnicamente, a plataforma deve tratar “localização” como **um stream de eventos** (observações → posição estimada → eventos/insights) com mensageria (ex.: **MQTT** e **WebSocket**) e armazenamento orientado a séries temporais + analytics. MQTT é um padrão OASIS e é leve para IoT. [\[7\]](https://www.oasis-open.org/standard/mqtt-v5-0-os/) WebSocket é padronizado pela RFC 6455 e serve para push em dashboards em tempo real. [\[8\]](https://www.rfc-editor.org/rfc/rfc6455)

Há também dois pontos de “produto” que diferenciam muito em restaurantes/catering:

1) **“Workflows” e métricas prontas** (tempo de atendimento, heatmaps, gargalos, round trips, SLA de mesa/pedido) em vez de apenas “pontinhos no mapa”.
2) **Implantação previsível**: kit, app de comissionamento, auto-calibração, monitoramento de saúde da infraestrutura, e um roteiro de instalação (com estimativas por m²), inspirado em práticas de implantação (altura, espaçamento, blueprint prévio etc.). [\[9\]](https://kontakt.io/blog/best-practices-for-deploying-beacons-and-gateways/)

**Nota importante (lacuna de insumo):** você mencionou ter fornecido system-design.md, mas não há arquivos acessíveis nesta conversa para eu referenciar diretamente. Vou produzir um blueprint completo **com hipóteses explicitadas**; se você enviar o markdown, eu consigo fazer um “gap analysis” linha‑a‑linha e propor revisões pontuais.

## Escopo, requisitos e hipóteses

**Escopo mínimo do sistema (produto):** RTLS/IPS para acompanhar **pessoas (equipe)** e **ativos (itens críticos)** em ambientes indoor, com mapa, eventos, alertas e analytics. Em restaurantes/catering, os objetos típicos são: equipe (garçons, chefs, copeiros), carrinhos/bandejas, caixas térmicas, cilindros, equipamentos de limpeza/segurança e — em alguns projetos — o próprio cliente (via smartphone).

**Metas de performance (alvo restaurante):** - **Acurácia**: **1–2 m “útil”** (não só média), com indicação de confiança e estados (“em cozinha”, “em salão”, “em corredor”) quando a precisão degradar. - **Latência ponta a ponta** (tag → dashboard): tipicamente **<1–2 s** para “posição ao vivo” de equipe; alertas críticos podem precisar <500 ms no tier premium (edge). - **Taxa de atualização**: configurável por tipo de entidade (ex.: equipe 1–2 Hz; ativos 0,2–1 Hz; eventos 10 s pode bastar para alguns KPIs — como um case da Novidá usa leituras a cada 10 s — mas “ao vivo” em restaurante costuma pedir mais). [\[10\]](https://conteudo.novida.com.br/hcorcase) - **Bateria**: importante (mas não crítica) — então o sistema deve suportar perfis diferentes de advertising e “motion-based update”.

**Hipóteses (ajuste conforme sua realidade):** - A operação inicial é **single-tenant**, mas desejável manter compatibilidade futura com multi-tenant (principalmente na camada de dados e IAM). - Você quer **comprar hardware de terceiros** e oferecer **tiers** (BLE econômico; AoA/UWB premium). - Em muitos clientes haverá demanda por **implantação on‑prem/híbrida** (ex.: indústria ou redes com restrições), então a arquitetura precisa de “módulos deslocáveis” (broker, location engine, storage).

## Tecnologias de posicionamento e estratégia de seleção

Abaixo está um comparativo pragmático das tecnologias que você pediu, alinhado ao alvo **1–2 m** e à necessidade de **tiers**.

### Tabela comparativa de tecnologias de posicionamento

Tecnologia

Como funciona

Acurácia típica (prática)

Latência / taxa

Custo & complexidade

Vantagens

Limitações

Melhor encaixe

BLE RSSI “geométrico” (trilateração aproximada)

converte RSSI→distância via modelo de perda de percurso e estima posição

costuma sofrer com multipath/NLoS; tende a ser “instável” sem filtros (varia muito por ambiente) [\[11\]](https://www.sciencedirect.com/science/article/pii/S0045790624003823)

depende de advertising e scanning; mais rápido = mais consumo (intervalo 20 ms–10,24 s) [\[12\]](https://docs.silabs.com/bluetooth/6.2.0/bluetooth-fundamentals-system-performance/current-consumption)

baixo custo; baixa complexidade; alto tuning

rápido de colocar em pé; bom para “zonas”

difícil garantir 1–2 m de forma consistente; “saltos”

SMB, PoC, zona/heatmap, inventário

BLE Fingerprinting (radiomap)

coleta “assinaturas” (RSSI por beacon) por ponto/grade; classifica posição com KNN/WKNN etc.

pode chegar a ~1–3 m em projetos bem feitos, mas exige levantamento e manutenção quando o ambiente muda [\[13\]](https://www.sciencedirect.com/science/article/pii/S0957417422005012)

baixa a média; boa para 0,5–2 Hz

custo baixo-médio; esforço alto na fase de site survey

melhor que trilateração RSSI em ambientes complexos; escalável no software

“drift” com mudanças (layout, pessoas, metal); requer recalibração

seu Tier econômico para 1–2 m “bom o bastante”

BLE AoA (Direction Finding)

receiver com array de antenas mede fase/IQ em CTE e estima ângulo; cruza ângulos de múltiplos locators

Bluetooth SIG indica viabilizar **sub‑metro** para proximidade/posicionamento [\[3\]](https://www.bluetooth.com/wp-content/uploads/Files/developer/RDF_Technical_Overview.pdf)

pode suportar atualização mais alta; depende do pipeline

custo e complexidade altos (locators, calibração)

estabilidade superior ao RSSI em muitos cenários; bom custo vs UWB em algumas aplicações

exige hardware específico e calibração; sensível a instalação e multipath

Tier premium para catering grande e indústria (sub‑metro “real”)

UWB (802.15.4a/4z)

mede **Time of Flight** (ToF) com grande largura de banda; ranging muito preciso

“centímetros” é claim comum em referências industriais (Qorvo e FiRa mencionam precisão centimétrica) [\[4\]](https://www.qorvo.com/innovation/ultra-wideband/technology)

pode ser muito baixa e com alta taxa

custo alto (tags/anchors), planejamento e sincronização

melhor caminho para precisão e robustez; bom para segurança industrial

maior CAPEX; energia e densidade de tags precisam engenharia

Tier premium (segurança, industrial, grande área)

Wi‑Fi RTT (802.11mc/FTM)

mede distância a APs RTT-capable via round-trip-time; Android tem APIs

esperado “1–2 m” em boa infra (documentação/explicações técnicas) [\[14\]](https://people.csail.mit.edu/bkph/FTMRTT_intro)

bom para smartphones; depende de APs e permissões

custo: médio (APs compatíveis)

ótimo para “smartphone como tag” sem BLE infra dedicada

suporte varia por dispositivo; precisa APs FTM; permissões e foreground constraints [\[15\]](https://developer.android.com/develop/connectivity/wifi/wifi-rtt)

clientes/visitantes com app; staff com smartphone (Android)

Híbrido / Sensor fusion (BLE+IMU, BLE+Wi‑Fi RTT, UWB+IMU)

combina medições RF com movimento (IMU) e filtros (Kalman/partículas)

melhora estabilidade e “suaviza” ruído; KF é comum para RSSI ruidoso [\[16\]](https://pubs.aip.org/aip/acp/article/2968/1/040001/2922338/Kalman-filter-for-RSSI-based-indoor-positioning)

pode reduzir jitter sem aumentar advertising

custo: software/ML; complexidade maior

melhor “qualidade percebida”; reduz saltos; permite fallback

precisa tuning e ground truth; aumenta complexidade

sua estratégia principal para atingir 1–2 m com robustez

### O que eu recomendo para bater 1–2 m em restaurante (sem virar projeto de P&D infinito)

**Estratégia em camadas (com fallback):** 1) **Primário (Tier econômico)**: BLE fingerprinting **\+ filtros** (Kalman/mediana) para estabilidade. KF é citado como técnica para melhorar RSSI ruidoso e, portanto, a confiabilidade de IPS baseado em RSSI. [\[17\]](https://pubs.aip.org/aip/acp/article/2968/1/040001/2922338/Kalman-filter-for-RSSI-based-indoor-positioning)
2) **Fallback 1**: “zona” (geofencing por áreas) quando a confiança cair (ex.: cozinha vs salão).
3) **Fallback 2**: sensores inerciais/QR (para casos “sem infraestrutura”), semelhante ao que Zapt menciona como opção de baixo investimento (QR + algoritmos inerciais) [\[18\]](https://zapt.tech/), mas usando isso apenas como alternativa — não como core RTLS.

**Tier premium**: - **BLE AoA** quando você quer sub‑metro e melhor estabilidade do que RSSI, aceitando maior custo e exigência de instalação. O Direction Finding depende de **CTE + IQ sampling + array de antenas** (Bluetooth SIG descreve a base técnica). [\[19\]](https://www.bluetooth.com/wp-content/uploads/Files/developer/RDF_Technical_Overview.pdf)
\- **UWB** quando o cliente paga por maior precisão/robustez (e/ou precisa de segurança industrial). UWB é baseado em 802.15.4a/4z e mede ToF com precisão centimétrica em referências industriais. [\[4\]](https://www.qorvo.com/innovation/ultra-wideband/technology)

### Smartphone como dispositivo rastreado (cenários e riscos reais)

**Smartphone como “tag BLE” (advertising):** - iOS permite anunciar como iBeacon, mas a Apple diz explicitamente que isso é mais adequado para apps “que já rodam em foreground”; para outros casos, usar hardware dedicado de terceiros. [\[5\]](https://developer.apple.com/documentation/corelocation/turning-an-ios-device-into-an-ibeacon-device)
\- Implicação: para rastrear staff com iPhone como tag, você pode acabar exigindo app sempre aberto/Live Activity/foreground e isso vira problema de adoção/UX.

**Smartphone como “scanner” (recebe beacons) para navegação/experiência do cliente:** - iOS usa um processo em duas etapas (region monitoring → ranging) para reduzir consumo; ranging requer medições frequentes de RSSI (maior consumo). [\[20\]](https://developer.apple.com/documentation/corelocation/determining-the-proximity-to-an-ibeacon-device)
\- Android scanning/uso BLE no background tem regras e permissões que mudam por versão; há docs oficiais sobre comunicação BLE em background. [\[21\]](https://developer.android.com/develop/connectivity/bluetooth/ble/background)

**Smartphone via Wi‑Fi RTT (Android):** - A própria documentação do Android explica que Wi‑Fi RTT usa FTM e requer APs compatíveis com IEEE 802.11‑2016 FTM (ou 802.11az em Android 15+), além de permissões e restrições de execução (foreground/serviço). [\[22\]](https://developer.android.com/develop/connectivity/wifi/wifi-rtt)
\- Serve super bem para “cliente com app” ou “staff Android”, mas você precisa gerenciar suporte por device/AP.

## Arquitetura recomendada e stack tecnológico

A arquitetura precisa ser **hardware-agnóstica** e **orientada a eventos**. Pense em três domínios: **aquisição (RF)** → **estimativa (engine)** → **valor (eventos/analytics)**. Um padrão inspirado no que players fazem é: mapear localização física (campus→prédio→andar→sala) e associar infra a um floorplan (como Kontakt.io faz em sua “Smart Location”). [\[23\]](https://support.kontakt.io/hc/en-gb/articles/4413241303058-Getting-started-with-Smart-Location)

### Diagrama de arquitetura (alto nível)

flowchart LR
subgraph Devices\["Dispositivos rastreados"\]
TAG\["Tags BLE/UWB (crachá, ativo)"\]
PHONE\["Smartphone (cliente/staff)\\nBLE scan / Wi‑Fi RTT / (BLE advertise opcional)"\]
end
subgraph Infra\["Infraestrutura no local"\]
ANCHOR\["Anchors/Locators\\nBLE Scanner | BLE AoA Locator | UWB Anchor"\]
GW\["Gateway/Edge Node\\n(RPi/NUC/Industrial PC)\\nMQTT bridge + buffer + health checks"\]
MAP\["Floorplans + Geofencing\\n(salas, zonas, rotas)"\]
end
subgraph CloudOnPrem\["Plataforma (SaaS / on‑prem / híbrida)"\]
BROKER\["MQTT Broker\\n(Mosquitto/EMQX)"\]
INGEST\["Ingestão & Normalização\\n(Decoder + dedup + time sync)"\]
ENGINE\["Location Engine\\nFingerprinting/AoA/UWB\\n+ Fusion (KF/PF)"\]
EVENTS\["Motor de Regras\\nGeofences, alertas, SLA"\]
API\["API (REST/gRPC)\\n+ WebSocket para realtime"\]
STORE\["Storage\\nPostgres + Time-series (Timescale)\\n+ OLAP (ClickHouse opcional)"\]
OBS\["Observabilidade\\nOpenTelemetry + Prometheus + Grafana"\]
end
TAG --> ANCHOR
PHONE --> ANCHOR
ANCHOR --> GW
GW --> BROKER
BROKER --> INGEST --> ENGINE --> EVENTS
EVENTS --> API
ENGINE --> STORE
INGEST --> STORE
MAP --> ENGINE
API --> DASH\["Dashboards Web/Mobile\\nOperação + Analytics (tempo real)"\]
OBS --- BROKER
OBS --- INGEST
OBS --- ENGINE
OBS --- API

### Real-time messaging: MQTT e WebSocket (por que os dois)

*   **MQTT** como “backbone IoT”: padrão OASIS, leve, pub/sub, bom para gateways e links instáveis. [\[7\]](https://www.oasis-open.org/standard/mqtt-v5-0-os/)
*   Edge → cloud: publicar observações (observations/…) e receber comandos (commands/…) (config, OTA, reinício, ajuste de taxa).
*   **WebSocket** para dashboards e apps operacionais: protocolo padrão RFC 6455 para comunicação full‑duplex e push em tempo real (mapa ao vivo). [\[8\]](https://www.rfc-editor.org/rfc/rfc6455)

### Data model (modelo de dados) recomendado

O modelo precisa suportar “organizações” e “locais” mesmo sendo single-tenant agora, porque isso reduz retrabalho:

*   **Site**: unidade (restaurante / base de catering / planta industrial).
*   **Building/Floor** + **Floorplan** (imagem + escala + sistema de coordenadas).
*   **Zone/Room/Area**: polígonos (geofence), corredores, áreas virtuais (como “footfall”). (O conceito de rooms/virtual rooms/corridors é útil e aparece na modelagem da Kontakt.io Smart Location). [\[23\]](https://support.kontakt.io/hc/en-gb/articles/4413241303058-Getting-started-with-Smart-Location)
*   **InfrastructureDevice**: gateway, anchor, locator, AP RTT.
*   **Tag/Entity**: pessoa/ativo e seu tipo (perfil de update/bateria).
*   **Observation** (evento bruto): timestamp, receiver\_id, rssi/iq/ToF, canal, seq, bateria, payload.
*   **PositionEstimate**: x,y,z, confidence, method (fingerprint/AoA/UWB), smoothing state.
*   **BusinessEvent**: entrada/saída de zona, permanência, anomalia, SLA, alerta.

### Location engine: algoritmos e “qualidade percebida”

Para o Tier econômico (BLE fingerprinting), uma linha de implementação realista:

1) **Coleta** de RSSI por receptor/beacon/tempo. 2) **Pré-processamento**: remoção de outliers, média móvel/mediana. 3) **Filtro de estado**: Kalman para suavizar RSSI/posição (há literatura e exemplos de aplicação de Kalman para RSSI ruidoso). [\[16\]](https://pubs.aip.org/aip/acp/article/2968/1/040001/2922338/Kalman-filter-for-RSSI-based-indoor-positioning)
4) **Classificador** (baseline robusta): KNN/WKNN em radiomap (fingerprinting é amplamente usado; há comparações e análises de desempenho na literatura). [\[13\]](https://www.sciencedirect.com/science/article/pii/S0957417422005012)
5) **Confidence score**: entropia/score de vizinhos + consistência temporal. 6) **Regras de “snap”**: restringir posição ao corredor/área válida (map matching), reduzindo “atravessar parede”.

Para Tier premium: - **BLE AoA**: pipeline inclui coleta de IQ (CTE) e estimação angular (fase/IQ) via stack/hardware adequado; Bluetooth SIG descreve que a matéria-prima vem de CTE + IQ sampling. [\[19\]](https://www.bluetooth.com/wp-content/uploads/Files/developer/RDF_Technical_Overview.pdf)
\- **UWB**: ToF/TWR/TDoA, sincronização e geometria; UWB é destacado por permitir ToF com precisão centimétrica. [\[4\]](https://www.qorvo.com/innovation/ultra-wideband/technology)

### Armazenamento e analytics: “do realtime ao histórico”

*   **Operational DB**: Postgres (entidades, permissões, configurações, mapas, auditoria).
*   **Time-series**: TimescaleDB (extensão Postgres) é explicitamente posicionada como extensão para analytics em dados de séries temporais e eventos (ótimo para trajetórias, estados, telemetria). [\[24\]](https://github.com/timescale/timescaledb)
*   **OLAP (opcional, enterprise)**: ClickHouse para consultas analíticas pesadas (heatmaps em longos períodos, agregações massivas). [\[25\]](https://clickhouse.com/docs)

## Hardware, topologia e critérios de seleção de terceiros

Seu requisito de “comprar hardware” + “dois tiers” pede que o software tenha um **Hardware Abstraction Layer (HAL)** e **drivers** por vendor/protocolo.

### Critérios de seleção (terceiros) que evitam armadilhas

**Compliance Brasil (muito importante):** no Brasil, equipamentos só podem ser comercializados se tiverem certificação/homologação válida; a Anatel fornece consulta pública e indica a exigência conforme Resolução 715/2019. [\[26\]](https://www.anatel.gov.br/paineis/certificacao-de-produtos/consulta-de-produtos)
→ Ação: inclua no seu processo de “go-to-market” uma checagem de homologação para gateways/tags que você revender/instalar.

**Capacidades mínimas do hardware (BLE):** - Controle de **advertising interval** e TX power; isso impacta consumo vs responsividade. Documentação técnica aponta que advertising interval em BLE é ajustável de **20 ms a 10,24 s**, e aumentar o intervalo reduz consumo. [\[12\]](https://docs.silabs.com/bluetooth/6.2.0/bluetooth-fundamentals-system-performance/current-consumption)
\- Suporte a payloads e/ou formatos (iBeacon/AltBeacon/Eddystone). (Ex.: estrutura de iBeacon tem UUID/major/minor; base é conhecida e aparece em docs de terceiros; Kontakt descreve o layout e intervalos típicos nos devices deles). [\[27\]](https://support.kontakt.io/hc/en-gb/articles/4413251561106-iBeacon-packets)
\- Telemetria (bateria, sensor) e configuração remota.

**Capacidades mínimas do hardware (AoA):** - Locators com arrays de antenas e suporte a CTE/IQ; _direction finding_ em Bluetooth 5.1 usa Constant Tone Extension e medições de fase para determinar direção. [\[28\]](https://www.silabs.com/documents/public/quick-start-guides/qsg175-direction-finding-solution-quick-start-guide.pdf)

**Capacidades mínimas do hardware (UWB):** - Aderência a 802.15.4a/4z (ecossistema), e preferência por interoperabilidade/certificação (FiRa promove ecossistema e adoção de “secured fine ranging”). [\[29\]](https://www.firaconsortium.org/)

### Gateways e topologias

Há três topologias comuns:

1) **Anchors “IP-native”**: anchors já sobem via Ethernet/Wi‑Fi direto para broker/edge.
2) **Anchors BLE scanner → Gateway**: scanners BLE (ESP32/RPi) enviam observações para gateway local (buffer + MQTT).
3) **AoA/UWB com “location server” local**: alguns vendors calculam posição on‑prem e expõem API.

**Deployment best practices (referência prática):** - Kontakt.io recomenda mapear com blueprint e, como regra geral de montagem, beacons a **3–5 m** de altura e espaçamento **8–10 m**, e cita alcance típico “até 70 m” (variável por ambiente). [\[30\]](https://kontakt.io/blog/best-practices-for-deploying-beacons-and-gateways/)
→ Use isso como _baseline_ de playbook, mas valide em campo (cozinha/salão mudam muito).

### Exemplos de ecossistemas/hardwares (para seu “catálogo em tiers”)

Tier

Categoria

Exemplos de referência (mercado)

Observações

Econômico

Tags BLE + gateway

Minew vende kits com tag BLE conectável + gateway e cita recursos como “enterprise-level encryption”, “remote configuration” e OTA (além de informar scan coverage “~300 m raio em área aberta” para o gateway). [\[31\]](https://www.minewstore.com/product/cloud-configurable-ble-ibeacon)

Bom para SMB/PoC, mas seu software deve ser vendor-agnóstico.

Econômico

Broker + edge

Mosquitto é broker MQTT open source e implementa MQTT 5.0/3.1.1/3.1; é leve e adequado até para SBCs. [\[32\]](https://mosquitto.org/)

Ótimo para on‑prem e edge.

Premium

UWB kit/infra

Sewio vende kit UWB (cobertura ~400 m²) e destaca tags recarregáveis com bateria “até 5 anos”, além de geofencing e Open API no software. [\[33\]](https://www.sewio.net/indoor-tracking-rtls-uwb-wi-fi-kit/)

Bom para “pacote” enterprise e para aprender o padrão de deploy.

Premium

AoA BLE (ecosistema)

Quuppa é referência em AoA; Siemens descreve rastreamento preciso e inclusive de dispositivos Bluetooth como telefones. [\[34\]](https://www.siemens.com/pt-br/products/quuppa/)

AoA exige locators/infra específica e calibração.

## Operação industrializada: provisionamento, OTA, observabilidade, testes e custos

Aqui é onde muitos RTLS falham: não é o algoritmo; é o “operar e manter” em dezenas/centenas de sites.

### Provisionamento e comissionamento

Inspire-se no padrão “Smart Location” (Kontakt): mapa hierárquico, upload de floorplan, desenho de salas e atribuição de dispositivos a locais no mapa. [\[23\]](https://support.kontakt.io/hc/en-gb/articles/4413241303058-Getting-started-with-Smart-Location)

**Sugestão prática de fluxo (MVP+):** 1) Cadastrar site → prédio → andar; fazer upload do floorplan (imagem/PDF convertido).
2) Definir escala (dois pontos + distância real).
3) Desenhar zonas (cozinha, salão, bar, estoque, banheiros, doca etc.).
4) App de instalação (mobile): QR code do dispositivo → escolhe sala/zona → registra posição aproximada no mapa.
5) Rodar “assistente de calibração”: coleta automática por 10–30 min e calcula parâmetros iniciais (offsets, radiomap inicial se for fingerprinting).

### OTA firmware e device management

Mesmo comprando hardware, você vai lidar com: - atualização do firmware de gateways próprios (se existir), - atualização de “agentes” (collector) em edge, - e, dependendo do vendor, OTA de tags/gateways.

**Opções maduras:** - **Eclipse hawkBit**: framework back-end “domain independent” para rollout de updates em dispositivos edge e gateways. [\[35\]](https://hawkbit.eclipse.dev/)
\- **AWS IoT OTA/Jobs** (se você for para cloud AWS): docs mostram tarefas OTA e biblioteca OTA com verificação criptográfica e suporte a rollback/commit. [\[36\]](https://docs.aws.amazon.com/iot-mi/latest/devguide/ota-task-types-implementation.html)

### Observabilidade e monitoramento

Você precisa medir: - “anchors online?” (heartbeat), - “taxa de pacotes recebidos” por área, - “drift” do engine, - latência end-to-end, - perda de mensagens.

**Stack recomendado:** - **OpenTelemetry (OTel)** como framework vendor‑neutral de observabilidade para traces/metrics/logs. [\[37\]](https://opentelemetry.io/docs/)
\- **Prometheus** para coleta de métricas e alertas (toolkit open-source de monitoring/alerting). [\[38\]](https://prometheus.io/docs/introduction/overview/)
\- Grafana (dashboards) — integração comum com Prometheus. [\[39\]](https://grafana.com/docs/grafana/latest/fundamentals/getting-started/first-dashboards/get-started-grafana-prometheus/)

### Estimativas de custo e exemplos de BOM

**Aviso de transparência:** custos variam brutalmente por volume, homologação, impostos, instalação e suporte. Vou usar **valores públicos exemplificativos** para ilustrar ordens de grandeza, e deixo claro o que é “preço publicamente listado” vs “estimativa”.

**Exemplo A: PoC SMB (restaurante ~250–400 m²) – Tier econômico BLE** - 1–2 gateways BLE/Wi‑Fi/Ethernet (edge)
\- 15–40 tags (staff + alguns ativos críticos)
\- 10–30 “beacons de referência”/anchors scanners (dependendo da abordagem)

Referência de preço público: Minew Store lista um kit “Cloud-configurable BLE iBeacon” por **US$ 99** (no contexto de kit com gateway/tag e plataforma). [\[31\]](https://www.minewstore.com/product/cloud-configurable-ble-ibeacon)
→ Uso: isso dá uma ideia de preço de kit/PoC, não é custo final de produção.

**Exemplo B: catering grande / planta ~1000–2000 m² – Tier premium UWB** - Kits e anchors UWB: Sewio descreve kit cobrindo **400 m²** e inclui 5 anchors + 4 tags, com licença e ferramentas (geofencing, Open API, visualização 2D/3D). [\[33\]](https://www.sewio.net/indoor-tracking-rtls-uwb-wi-fi-kit/)
→ Uma regra “de bolso” para budgeting inicial: dimensionar por células de cobertura (p.ex., 400 m²/célula como referência de kit) e ajustar por obstáculos.

**Dica crucial de produto:** em vez de vender “tag por tag”, empacote por **capacidade operacional**: - “Starter (até 20 pessoas / 10 ativos / 1 site)” - “Growth (até 80 / 50 / 1–3 sites)” - “Enterprise (segurança + integrações + HA + on‑prem)”

### Deployment playbook específico para restaurantes

**Checklist antes da instalação:** - Plantas atualizadas (mudança de layout é frequente). - Áreas de sombra RF: cozinha (metal), câmara fria, estoque. - Rotas “críticas”: pass-through cozinha→salão, área de lavagem, doca.

**Dia da instalação (MVP):** 1) Instalar anchors/gateways (altura e espaçamento como baseline; validar onsite). [\[30\]](https://kontakt.io/blog/best-practices-for-deploying-beacons-and-gateways/)
2) Rodar teste de cobertura (mapa de RSSI/qualidade).
3) Fixar tags em staff e ativos; treinar uso (troca de bateria, carregamento, check-in/out).
4) Ligar painéis operacionais: mapa ao vivo + alertas básicos (geofence, permanência excessiva, ativo “sumido”).

**Dia 7–14 (pós-rampa):** - Ajustar parâmetros de advertising e smoothing conforme movimento real (advertising interval impacta consumo vs responsividade). [\[12\]](https://docs.silabs.com/bluetooth/6.2.0/bluetooth-fundamentals-system-performance/current-consumption)
\- Criar relatórios “de negócio”: tempos de ciclo, heatmaps, gargalos.

## Privacidade, consentimento, segurança e compliance

### LGPD e governança (Brasil)

A LGPD (Lei 13.709/2018) regula o tratamento de dados pessoais e visa proteger liberdade, privacidade e desenvolvimento da personalidade. [\[40\]](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
Como RTLS pode rastrear **pessoas identificadas/identificáveis**, você deve assumir que: - dados de localização **podem ser dados pessoais** quando associados a um colaborador/cliente (interpretação natural do conceito legal de “dado pessoal” como informação relacionada a pessoa identificada/identificável). [\[41\]](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)

Para operações que envolvem tracking de staff/cliente, recomendações práticas: - Definir base legal (consentimento vs legítimo interesse vs obrigação legal etc.). A ANPD publicou guia orientativo sobre **Legítimo Interesse** para esclarecer aplicação e parâmetros. [\[42\]](https://www.gov.br/anpd/pt-br/assuntos/noticias/anpd-lanca-guia-orientativo-sobre-legitimo-interesse)
\- Fazer **RIPD** quando houver potencial de alto risco; a ANPD define RIPD como documentação que descreve processos de tratamento que podem gerar alto risco e recomenda sua elaboração em contextos de risco elevado. [\[43\]](https://www.gov.br/anpd/pt-br/canais_atendimento/agente-de-tratamento/relatorio-de-impacto-a-protecao-de-dados-pessoais-ripd)

### Consentimento e “privacy by design” em cenários com smartphone

Em “cliente como tag” (app), você precisa ser muito conservador: - Opt-in claro, propósito específico (ex.: orientação, fila, atendimento), e minimização. - Respeitar constraints técnicas: iOS e Android impõem restrições a BLE em background; iOS sugere hardware dedicado para certos usos de iBeacon. [\[44\]](https://developer.apple.com/documentation/corelocation/turning-an-ios-device-into-an-ibeacon-device)

### Segurança técnica: do BLE ao backend

**Segurança BLE (quando há conexão):** - Bluetooth possui Security Manager que gerencia pairing/autenticação/cripto. [\[45\]](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Core-54/out/en/host/security-manager-specification.html)
\- Pacotes criptografados podem incluir MIC e contadores anti-replay (explicações técnicas em docs de fabricantes). [\[46\]](https://developerhelp.microchip.com/xwiki/bin/view/applications/ble/introduction/bluetooth-architecture/bluetooth-controller-layer/bluetooth-link-layer/Security/)

**Mas atenção:** grande parte de RTLS BLE usa **advertising** (broadcast). Beacon/pacote de advertising por si só não “protege” contra tracking/spoofing; então você precisa de medidas adicionais: - IDs rotativos/ephemerais (ex.: Eddystone‑EID define método criptográfico para broadcast seguro). [\[47\]](https://github.com/google/eddystone)
\- Minimizar o que vai no payload (não colocar “nome do colaborador” em advertising, por exemplo).

**Privacidade por endereços BLE:** - O Bluetooth SIG descreve mecanismos como Resolvable Private Address (RPA) e até melhorias recentes de randomização para aumentar privacidade e eficiência energética, incluindo a ideia de que RPA é resolvível apenas por dispositivos com IRK compartilhada. [\[48\]](https://www.bluetooth.com/blog/enhancing-device-privacy-and-energy-efficiency-with-bluetooth-randomized-rpa-updates/)
→ Mesmo que você não implemente isso agora, seu sistema deve evitar dependência de MAC fixo como identidade.

**Segurança do transporte (gateway → plataforma):** - MQTT over TLS e autenticação por certificado (mTLS) é o padrão ouro. Brokers como EMQX destacam TLS e mecanismos de autenticação, e clustering para HA. [\[49\]](https://docs.emqx.com/en/emqx/latest/deploy/cluster/introduction.html)

**Auditoria e trilhas:** - Configurações, comandos OTA, mudanças de mapa/zona devem ser auditáveis (especialmente em indústria).

## Roadmap, MVP recomendado e perguntas para você

### MVP recomendado (primeiros 60–90 dias, “vendável”)

**Produto operável (não só demo):** - Cadastro de site/floorplan + desenho de zonas. - Cadastro de tags/ativos/pessoas e associação a perfis (update rate/bateria). - Ingestão via MQTT (gateway/edge) + API + WebSocket para mapa ao vivo. [\[50\]](https://www.oasis-open.org/standard/mqtt-v5-0-os/)
\- Location engine **Tier econômico**: - fingerprinting básico (KNN/WKNN) + smoothing (Kalman/mediana) [\[51\]](https://www.sciencedirect.com/science/article/pii/S0957417422005012)
\- confidence score + fallback para zonas. - Motor de eventos: - entrada/saída de zona, tempo parado, permanência excessiva, item “fora de área”. - Painel operacional: - mapa ao vivo, lista de pessoas/ativos, histórico curto (últimas 24h), export CSV. - Observabilidade mínima: - health de gateways/anchors, taxa de pacotes, latência. (Stack: OTel + Prometheus) [\[52\]](https://opentelemetry.io/docs/)
\- Política de privacidade + consentimento + logs de auditoria (LGPD-ready). [\[53\]](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)

### Roadmap em fases (MVP → enterprise)

gantt
title Roadmap sugerido RTLS/IPS (MVP ao Enterprise)
dateFormat YYYY-MM-DD
axisFormat %b/%Y
section Fundação do produto
Modelagem (sites, floors, zonas, tags) :a1, 2026-03-15, 21d
Ingestão MQTT + API + WebSocket :a2, 2026-03-15, 30d
Dashboard operacional (mapa ao vivo) :a3, 2026-03-25, 35d
section Location Engine Tier econômico
Fingerprinting baseline + tooling de radiomap :b1, 2026-04-01, 45d
Smoothing (Kalman/mediana) + confidence :b2, 2026-04-10, 35d
Calibração guiada + validação em 1 restaurante :b3, 2026-05-01, 21d
section Produto restaurante/catering
KPIs (tempo de atendimento, heatmaps, gargalos) :c1, 2026-05-01, 45d
Motor de regras (alertas, SLA) :c2, 2026-05-10, 30d
Integrações (POS/KDS/ERP) :c3, 2026-06-01, 45d
section Tier premium + robustez
BLE AoA (piloto) :d1, 2026-06-15, 60d
UWB (piloto) :d2, 2026-06-15, 60d
Edge mode + store-and-forward :d3, 2026-06-20, 45d
section Enterprise e compliance
HA (cluster broker + deploy blue/green) :e1, 2026-07-15, 45d
OTA + device management (hawkBit/AWS IoT) :e2, 2026-07-15, 60d
LGPD hardening + RIPD templates :e3, 2026-07-20, 30d

### Diferenciação vs concorrentes (o que vira “killer application”)

Com base no que seus exemplos comunicam:

*   **Zapt**: forte em mapas, wayfinding, multi-sinalizadores e produto white‑label/SDK, acurácia comunicada ~3 m em IPS e uso de beacons + reuso de APs, além de baterias até 5 anos. [\[1\]](https://zapt.tech/solucoes/indoor-positioning/)
    **Diferencie** entregando **1–2 m com score de confiança**, e principalmente “operações” (KPIs de restaurante/catering) + playbook de deploy.
*   **Novidá**: narrativa de ROI (economias, produtividade), tracking + IA + checklists e dashboard; case com leitura 10 s e erro <1 m em hospital. [\[54\]](https://www.novida.com.br/)
    **Diferencie** sendo **hardware-agnóstico em tiers**, e oferecendo “operating system de restaurante” (workflow) + integrações nativas com POS/KDS + modo on‑prem/híbrido.
*   **Ztrax / integrações**: posicionamento RTLS para pessoas e ativos; integradores enfatizam recepção de eventos e localização em tempo real. [\[55\]](https://ztrax.com.br/)
    **Diferencie** com **APIs abertas + webhooks + modelo de eventos** e um pipeline de dados/analytics superior (heatmaps, espaguete, SLA, detecção de anomalias).

### Perguntas de clarificação para eu ajustar o blueprint ao seu contexto

1) **Ambiente e densidade**: qual é o “pior caso” esperado em restaurante/catering (m², nº de colaboradores simultâneos, nº de tags totais)?
2) **Tipo de tracking**: você quer **tracking contínuo** (trajetória) ou basta “presença por zona” para parte dos casos?
3) **Infra disponível**: normalmente há Wi‑Fi corporativo bom e APs gerenciáveis? Isso influencia muito Wi‑Fi RTT e até reuso de AP BLE (como alguns vendors citam). [\[56\]](https://kontakt.io/blog/best-practices-for-deploying-beacons-and-gateways/)
4) **Smartphone-as-tag**: em quais cenários é obrigatório (staff? cliente? ambos) e em qual SO (Android/iOS)? (iOS tem restrições e recomendações específicas para iBeacon). [\[57\]](https://developer.apple.com/documentation/corelocation/turning-an-ios-device-into-an-ibeacon-device)
5) **Privacidade**: o cliente quer rastrear funcionários “identificados” no mapa, ou prefere pseudonimização (ex.: “Equipe A”, “Runner 3”) com reversão apenas para gerentes?
6) **Modelo de implantação**: você quer começar com **SaaS** mesmo sendo single-tenant, ou prefere **on‑prem** por padrão (mais comum em indústria)?
7) **Integrações essenciais em restaurante**: quais sistemas você precisa integrar no MVP (POS, KDS, escala, folha, controle de acesso, CFTV)?
8) **Orçamento por site**: qual CAPEX alvo para “SMB” e para “premium”? (mesmo faixa ajuda a escolher AoA vs UWB e quantidade de anchors).

Se você enviar o system-design.md, eu faço uma revisão detalhada comparando o seu desenho atual com este blueprint (lacunas de produto, infraestrutura, segurança, dados e operação) e proponho um “delta” passo a passo, mantendo o que já está bom e modernizando o restante.

[\[1\]](https://zapt.tech/solucoes/indoor-positioning/) https://zapt.tech/solucoes/indoor-positioning/

[https://zapt.tech/solucoes/indoor-positioning/](https://zapt.tech/solucoes/indoor-positioning/)

[\[2\]](https://conteudo.novida.com.br/hcorcase) [\[10\]](https://conteudo.novida.com.br/hcorcase) https://conteudo.novida.com.br/hcorcase

[https://conteudo.novida.com.br/hcorcase](https://conteudo.novida.com.br/hcorcase)

[\[3\]](https://www.bluetooth.com/wp-content/uploads/Files/developer/RDF_Technical_Overview.pdf) [\[19\]](https://www.bluetooth.com/wp-content/uploads/Files/developer/RDF_Technical_Overview.pdf) https://www.bluetooth.com/wp-content/uploads/Files/developer/RDF\_Technical\_Overview.pdf

[https://www.bluetooth.com/wp-content/uploads/Files/developer/RDF\_Technical\_Overview.pdf](https://www.bluetooth.com/wp-content/uploads/Files/developer/RDF_Technical_Overview.pdf)

[\[4\]](https://www.qorvo.com/innovation/ultra-wideband/technology) https://www.qorvo.com/innovation/ultra-wideband/technology

[https://www.qorvo.com/innovation/ultra-wideband/technology](https://www.qorvo.com/innovation/ultra-wideband/technology)

[\[5\]](https://developer.apple.com/documentation/corelocation/turning-an-ios-device-into-an-ibeacon-device) [\[44\]](https://developer.apple.com/documentation/corelocation/turning-an-ios-device-into-an-ibeacon-device) [\[57\]](https://developer.apple.com/documentation/corelocation/turning-an-ios-device-into-an-ibeacon-device) https://developer.apple.com/documentation/corelocation/turning-an-ios-device-into-an-ibeacon-device

[https://developer.apple.com/documentation/corelocation/turning-an-ios-device-into-an-ibeacon-device](https://developer.apple.com/documentation/corelocation/turning-an-ios-device-into-an-ibeacon-device)

[\[6\]](https://developer.android.com/develop/connectivity/bluetooth/ble/background) [\[21\]](https://developer.android.com/develop/connectivity/bluetooth/ble/background) https://developer.android.com/develop/connectivity/bluetooth/ble/background

[https://developer.android.com/develop/connectivity/bluetooth/ble/background](https://developer.android.com/develop/connectivity/bluetooth/ble/background)

[\[7\]](https://www.oasis-open.org/standard/mqtt-v5-0-os/) [\[50\]](https://www.oasis-open.org/standard/mqtt-v5-0-os/) https://www.oasis-open.org/standard/mqtt-v5-0-os/

[https://www.oasis-open.org/standard/mqtt-v5-0-os/](https://www.oasis-open.org/standard/mqtt-v5-0-os/)

[\[8\]](https://www.rfc-editor.org/rfc/rfc6455) https://www.rfc-editor.org/rfc/rfc6455

[https://www.rfc-editor.org/rfc/rfc6455](https://www.rfc-editor.org/rfc/rfc6455)

[\[9\]](https://kontakt.io/blog/best-practices-for-deploying-beacons-and-gateways/) [\[30\]](https://kontakt.io/blog/best-practices-for-deploying-beacons-and-gateways/) [\[56\]](https://kontakt.io/blog/best-practices-for-deploying-beacons-and-gateways/) https://kontakt.io/blog/best-practices-for-deploying-beacons-and-gateways/

[https://kontakt.io/blog/best-practices-for-deploying-beacons-and-gateways/](https://kontakt.io/blog/best-practices-for-deploying-beacons-and-gateways/)

[\[11\]](https://www.sciencedirect.com/science/article/pii/S0045790624003823) https://www.sciencedirect.com/science/article/pii/S0045790624003823

[https://www.sciencedirect.com/science/article/pii/S0045790624003823](https://www.sciencedirect.com/science/article/pii/S0045790624003823)

[\[12\]](https://docs.silabs.com/bluetooth/6.2.0/bluetooth-fundamentals-system-performance/current-consumption) https://docs.silabs.com/bluetooth/6.2.0/bluetooth-fundamentals-system-performance/current-consumption

[https://docs.silabs.com/bluetooth/6.2.0/bluetooth-fundamentals-system-performance/current-consumption](https://docs.silabs.com/bluetooth/6.2.0/bluetooth-fundamentals-system-performance/current-consumption)

[\[13\]](https://www.sciencedirect.com/science/article/pii/S0957417422005012) [\[51\]](https://www.sciencedirect.com/science/article/pii/S0957417422005012) https://www.sciencedirect.com/science/article/pii/S0957417422005012

[https://www.sciencedirect.com/science/article/pii/S0957417422005012](https://www.sciencedirect.com/science/article/pii/S0957417422005012)

[\[14\]](https://people.csail.mit.edu/bkph/FTMRTT_intro) https://people.csail.mit.edu/bkph/FTMRTT\_intro

[https://people.csail.mit.edu/bkph/FTMRTT\_intro](https://people.csail.mit.edu/bkph/FTMRTT_intro)

[\[15\]](https://developer.android.com/develop/connectivity/wifi/wifi-rtt) [\[22\]](https://developer.android.com/develop/connectivity/wifi/wifi-rtt) https://developer.android.com/develop/connectivity/wifi/wifi-rtt

[https://developer.android.com/develop/connectivity/wifi/wifi-rtt](https://developer.android.com/develop/connectivity/wifi/wifi-rtt)

[\[16\]](https://pubs.aip.org/aip/acp/article/2968/1/040001/2922338/Kalman-filter-for-RSSI-based-indoor-positioning) [\[17\]](https://pubs.aip.org/aip/acp/article/2968/1/040001/2922338/Kalman-filter-for-RSSI-based-indoor-positioning) https://pubs.aip.org/aip/acp/article/2968/1/040001/2922338/Kalman-filter-for-RSSI-based-indoor-positioning

[https://pubs.aip.org/aip/acp/article/2968/1/040001/2922338/Kalman-filter-for-RSSI-based-indoor-positioning](https://pubs.aip.org/aip/acp/article/2968/1/040001/2922338/Kalman-filter-for-RSSI-based-indoor-positioning)

[\[18\]](https://zapt.tech/) https://zapt.tech/

[https://zapt.tech/](https://zapt.tech/)

[\[20\]](https://developer.apple.com/documentation/corelocation/determining-the-proximity-to-an-ibeacon-device) https://developer.apple.com/documentation/corelocation/determining-the-proximity-to-an-ibeacon-device

[https://developer.apple.com/documentation/corelocation/determining-the-proximity-to-an-ibeacon-device](https://developer.apple.com/documentation/corelocation/determining-the-proximity-to-an-ibeacon-device)

[\[23\]](https://support.kontakt.io/hc/en-gb/articles/4413241303058-Getting-started-with-Smart-Location) https://support.kontakt.io/hc/en-gb/articles/4413241303058-Getting-started-with-Smart-Location

[https://support.kontakt.io/hc/en-gb/articles/4413241303058-Getting-started-with-Smart-Location](https://support.kontakt.io/hc/en-gb/articles/4413241303058-Getting-started-with-Smart-Location)

[\[24\]](https://github.com/timescale/timescaledb) https://github.com/timescale/timescaledb

[https://github.com/timescale/timescaledb](https://github.com/timescale/timescaledb)

[\[25\]](https://clickhouse.com/docs) https://clickhouse.com/docs

[https://clickhouse.com/docs](https://clickhouse.com/docs)

[\[26\]](https://www.anatel.gov.br/paineis/certificacao-de-produtos/consulta-de-produtos) https://www.anatel.gov.br/paineis/certificacao-de-produtos/consulta-de-produtos

[https://www.anatel.gov.br/paineis/certificacao-de-produtos/consulta-de-produtos](https://www.anatel.gov.br/paineis/certificacao-de-produtos/consulta-de-produtos)

[\[27\]](https://support.kontakt.io/hc/en-gb/articles/4413251561106-iBeacon-packets) https://support.kontakt.io/hc/en-gb/articles/4413251561106-iBeacon-packets

[https://support.kontakt.io/hc/en-gb/articles/4413251561106-iBeacon-packets](https://support.kontakt.io/hc/en-gb/articles/4413251561106-iBeacon-packets)

[\[28\]](https://www.silabs.com/documents/public/quick-start-guides/qsg175-direction-finding-solution-quick-start-guide.pdf) https://www.silabs.com/documents/public/quick-start-guides/qsg175-direction-finding-solution-quick-start-guide.pdf

[https://www.silabs.com/documents/public/quick-start-guides/qsg175-direction-finding-solution-quick-start-guide.pdf](https://www.silabs.com/documents/public/quick-start-guides/qsg175-direction-finding-solution-quick-start-guide.pdf)

[\[29\]](https://www.firaconsortium.org/) https://www.firaconsortium.org/

[https://www.firaconsortium.org/](https://www.firaconsortium.org/)

[\[31\]](https://www.minewstore.com/product/cloud-configurable-ble-ibeacon) https://www.minewstore.com/product/cloud-configurable-ble-ibeacon

[https://www.minewstore.com/product/cloud-configurable-ble-ibeacon](https://www.minewstore.com/product/cloud-configurable-ble-ibeacon)

[\[32\]](https://mosquitto.org/) https://mosquitto.org/

[https://mosquitto.org/](https://mosquitto.org/)

[\[33\]](https://www.sewio.net/indoor-tracking-rtls-uwb-wi-fi-kit/) https://www.sewio.net/indoor-tracking-rtls-uwb-wi-fi-kit/

[https://www.sewio.net/indoor-tracking-rtls-uwb-wi-fi-kit/](https://www.sewio.net/indoor-tracking-rtls-uwb-wi-fi-kit/)

[\[34\]](https://www.siemens.com/pt-br/products/quuppa/) https://www.siemens.com/pt-br/products/quuppa/

[https://www.siemens.com/pt-br/products/quuppa/](https://www.siemens.com/pt-br/products/quuppa/)

[\[35\]](https://hawkbit.eclipse.dev/) https://hawkbit.eclipse.dev/

[https://hawkbit.eclipse.dev/](https://hawkbit.eclipse.dev/)

[\[36\]](https://docs.aws.amazon.com/iot-mi/latest/devguide/ota-task-types-implementation.html) https://docs.aws.amazon.com/iot-mi/latest/devguide/ota-task-types-implementation.html

[https://docs.aws.amazon.com/iot-mi/latest/devguide/ota-task-types-implementation.html](https://docs.aws.amazon.com/iot-mi/latest/devguide/ota-task-types-implementation.html)

[\[37\]](https://opentelemetry.io/docs/) [\[52\]](https://opentelemetry.io/docs/) https://opentelemetry.io/docs/

[https://opentelemetry.io/docs/](https://opentelemetry.io/docs/)

[\[38\]](https://prometheus.io/docs/introduction/overview/) https://prometheus.io/docs/introduction/overview/

[https://prometheus.io/docs/introduction/overview/](https://prometheus.io/docs/introduction/overview/)

[\[39\]](https://grafana.com/docs/grafana/latest/fundamentals/getting-started/first-dashboards/get-started-grafana-prometheus/) https://grafana.com/docs/grafana/latest/fundamentals/getting-started/first-dashboards/get-started-grafana-prometheus/

[https://grafana.com/docs/grafana/latest/fundamentals/getting-started/first-dashboards/get-started-grafana-prometheus/](https://grafana.com/docs/grafana/latest/fundamentals/getting-started/first-dashboards/get-started-grafana-prometheus/)

[\[40\]](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm) [\[41\]](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm) [\[53\]](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm) https://www.planalto.gov.br/ccivil\_03/\_ato2015-2018/2018/lei/l13709.htm

[https://www.planalto.gov.br/ccivil\_03/\_ato2015-2018/2018/lei/l13709.htm](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)

[\[42\]](https://www.gov.br/anpd/pt-br/assuntos/noticias/anpd-lanca-guia-orientativo-sobre-legitimo-interesse) https://www.gov.br/anpd/pt-br/assuntos/noticias/anpd-lanca-guia-orientativo-sobre-legitimo-interesse

[https://www.gov.br/anpd/pt-br/assuntos/noticias/anpd-lanca-guia-orientativo-sobre-legitimo-interesse](https://www.gov.br/anpd/pt-br/assuntos/noticias/anpd-lanca-guia-orientativo-sobre-legitimo-interesse)

[\[43\]](https://www.gov.br/anpd/pt-br/canais_atendimento/agente-de-tratamento/relatorio-de-impacto-a-protecao-de-dados-pessoais-ripd) https://www.gov.br/anpd/pt-br/canais\_atendimento/agente-de-tratamento/relatorio-de-impacto-a-protecao-de-dados-pessoais-ripd

[https://www.gov.br/anpd/pt-br/canais\_atendimento/agente-de-tratamento/relatorio-de-impacto-a-protecao-de-dados-pessoais-ripd](https://www.gov.br/anpd/pt-br/canais_atendimento/agente-de-tratamento/relatorio-de-impacto-a-protecao-de-dados-pessoais-ripd)

[\[45\]](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Core-54/out/en/host/security-manager-specification.html) https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Core-54/out/en/host/security-manager-specification.html

[https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Core-54/out/en/host/security-manager-specification.html](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Core-54/out/en/host/security-manager-specification.html)

[\[46\]](https://developerhelp.microchip.com/xwiki/bin/view/applications/ble/introduction/bluetooth-architecture/bluetooth-controller-layer/bluetooth-link-layer/Security/) https://developerhelp.microchip.com/xwiki/bin/view/applications/ble/introduction/bluetooth-architecture/bluetooth-controller-layer/bluetooth-link-layer/Security/

[https://developerhelp.microchip.com/xwiki/bin/view/applications/ble/introduction/bluetooth-architecture/bluetooth-controller-layer/bluetooth-link-layer/Security/](https://developerhelp.microchip.com/xwiki/bin/view/applications/ble/introduction/bluetooth-architecture/bluetooth-controller-layer/bluetooth-link-layer/Security/)

[\[47\]](https://github.com/google/eddystone) https://github.com/google/eddystone

[https://github.com/google/eddystone](https://github.com/google/eddystone)

[\[48\]](https://www.bluetooth.com/blog/enhancing-device-privacy-and-energy-efficiency-with-bluetooth-randomized-rpa-updates/) https://www.bluetooth.com/blog/enhancing-device-privacy-and-energy-efficiency-with-bluetooth-randomized-rpa-updates/

[https://www.bluetooth.com/blog/enhancing-device-privacy-and-energy-efficiency-with-bluetooth-randomized-rpa-updates/](https://www.bluetooth.com/blog/enhancing-device-privacy-and-energy-efficiency-with-bluetooth-randomized-rpa-updates/)

[\[49\]](https://docs.emqx.com/en/emqx/latest/deploy/cluster/introduction.html) https://docs.emqx.com/en/emqx/latest/deploy/cluster/introduction.html

[https://docs.emqx.com/en/emqx/latest/deploy/cluster/introduction.html](https://docs.emqx.com/en/emqx/latest/deploy/cluster/introduction.html)

[\[54\]](https://www.novida.com.br/) https://www.novida.com.br/

[https://www.novida.com.br/](https://www.novida.com.br/)

[\[55\]](https://ztrax.com.br/) https://ztrax.com.br/

[https://ztrax.com.br/](https://ztrax.com.br/)