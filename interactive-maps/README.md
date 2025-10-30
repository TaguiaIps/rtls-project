
# Exibir-mapas-interativos-com-POIs-personalizados

## Análise de algumas telas de aplicativos - Introdução

Com base na análise de alguns aplicativos que utilizam mapas interativos RTLS, como Midmark RTLS BLE Setup, ZAPT, NOVIDA e MINEW, foi possível observar diferentes formas de exibir e personalizar Pontos de Interesse (POIs). Cada um desses aplicativos utiliza recursos visuais e funcionais específicos para destacar locais relevantes ao usuário, como shoppings, indústrias, aeropórtos, entre outros. Essas referências foram fundamentais para entender um pouco e começar a pensar em mapas para restaurantes. 

## CCSQ da Zapt Tech
### Sobre o aplicativo

Trata-se de um aplicativo para se geolocalizar dentro do Centro Cultural Sesc Quitandinha(CCSQ), localizado em Petrópolis - Município no Rio de Janeiro. Através desta geolocalização, o aplicativo consegue auxiliar o usuário a se locomover pelo Centro Cultural, auxiliando-os com rotas mais rápidas entre os diversos ambientes, apresenta um mapa realístico para ajudar o usuário e adicionando descrições detalhadas e informativas sobre o ambiente para promover a curiosidade do local ao usuário.

### Descrição dos ambientes

<img src="imgs/Descricao-CCSQ.webp" alt="DescricaoCCSQ" width="250"/>

### Rotas entre os ambientes

<img src="imgs/Rotas2-CCSQ.webp" alt="RotasCCSQ" width="250"/>
<img src="imgs/Rota1-CCSQ.webp" alt="RotasCCSQ" width="250"/>

### Mapa realístico

<img src="imgs/Mapa-CCSQ.webp" alt="MapaCCSQ" width="250"/>

### Tela Inicial

<img src="imgs/TelaInicial-CCQS.webp" alt="TelaInicialCCSQ" width="250"/>


## YoGuide da Zapt Tech
### Sobre o aplicativo
Trata-se de um aplicativo para se geolocalizar dentro de um centro comercial. Através desta geolocalização, o aplicativo consegue auxiliar o usuário a se locomover dentro do local, auxiliando-os com rotas mais rápidas para determinada loja, apresenta um mapa com o nome das lojas para ajudar o usuário, 
possui uma assistente de inteligência artificial que auxilia o usuário com informações básicas, indicações de lojas, onde localizar determinado produto, sugerindo promoções, etc, e adicionando descrições sobre cada loja.

### Assistencia IA
<img src="imgs/AssistenciaIA-YouGuide.webp" alt="AssistenciaIa" width="250"/>


### Lojas
<img src="imgs/Lojas-YouGuide.webp" alt="LojasYouGuide" width="250"/>


### Mapa
<img src="imgs/Mapa-YouGuide.webp" alt="MapaYouGuide" width="250"/>


## Viracopos Maps da Zapt Tech
### Sobre o aplicativo
Aplicativo com o mapa realista de um aeroporto que ajuda o usuário a se geolocalizar. Caso o usuário deseje saber a localização do banheiro, basta abrir o aplicativo e procurar o banheiro mais perto de acordo com sua localização no mapa.

<img src="imgs/Aeroporto-Viracopos.webp" alt="AeroportoViracopos" width="250"/>

## Outras telas de Referência
### Midmark RTLS BLE Setup
<img src="imgs/TelaReferencia-Midmark.jpeg" alt="TelaReferencia1" width="250"/>
<!--![Tela de Referencia1](imgs/TelaReferencia-Midmark.jpeg) -->

### ZAPT Aplicativo Aeroporto
<img src="imgs/TelaReferencia-ZAPT_AEROPORTO.png" alt="TelaReferencia2" width="250"/>
<!--![Tela de Referencia2](imgs/TelaReferencia-ZAPT_AEROPORTO.png) -->

### ZAPT Aplicativo Localização de Objetos
<img src="imgs/TelaReferencia-ZAPT_LocalizacaoObjetos.png" alt="TelaReferencia3" width="250"/>
<!--![Tela de Referencia3](imgs/TelaReferencia-ZAPT_LocalizacaoObjetos.png)-->

### ZAPT Aplicativo Shopping
<img src="imgs/TelaReferencia-ZAPT_SHOPPING.png" alt="TelaReferencia4" width="250"/>
<!--![Tela de Referencia4](imgs/TelaReferencia-ZAPT_SHOPPING.png)-->

### Conferência da Amazonia
<img src="imgs/TelaPrincipal-ConferenciaAmazonia.webp" alt="TelaReferencia5" width="250"/>


## Outros aplicativos

Também foram encontrados alguns aplicativos que apesar de não serem exatamente o que buscamos, possa ser de grande ajuda. Estes aplicativos consistem na configuração dos GATEWAYS, BEACONS, celulares, etc.

### GatewayConfig

"O Gateway Assistant é um aplicativo de configuração de gateway leve que pode configurar facilmente a rede de gateway, as configurações do servidor de dados de relatório e as configurações de verificação de dados do gateway;"

<img src="imgs/gateways-GatewayConfig.webp" alt="GatewayConfig" width="250"/>
<img src="imgs/config-GatewayConfig.webp" alt="GatewayConfig" width="250"/>

### BeaconSET Plus

"Este aplicativo é uma ferramenta para dispositivos BeaconPlus, você pode fazer o seguinte enquanto usa o BeaconSET Plus:

1.scan dispositivos BeaconPlus;
2.conecte-se ao seu BeaconPlus;
3.ler informações do seu BeaconPlus;
4.modifique seu BeaconPlus;"

<img src="imgs/scan-BeaconSETPlus.webp" alt="GatewayConfig" width="250"/>
<img src="imgs/setUp-BeaconSETPlus.webp" alt="GatewayConfig" width="250"/>

## Análise de comparação de requisitos

### Requisitos semelhantes

- Permitir rastreamento em tempo real de pessoas
- Exibir a localização em tempo real de pessoas
- Permitir a navegação em tempo real com rotas otimizadas para usuários em ambientes indoor
- Exibir mapas interativos com POIs personalizados
- Implementar busca por locais específicos com rota mais curta
- Implementar mapas interativos 2D/3D para navegação indoor/outdoor
- Fornecer rotas detalhadas até POIs específicos
- Integrar funcionalidade de acessibilidade para mobilidade reduzida

### Requisitos que não temos

- Assistente por IA
- Descrição dos ambientes/lojas
- Os destaques(que seriam os locais do ambiente) na tela inicial do aplicativo - No nosso contexto poderia ser aplicado como uma amostra das promoções do restaurante
- Opção de favoritar lojas
- Opção de buscar loja ou ambiente(com a opção por voz)
- Tela de notícias
- Tela para se informar das visitas guiadas
- Filtros de mapa - Servindo também para filtrar objetos definidos por categoria. Ex: Eletrônicos

### Requisitos diferentes ou que não consegui identicar

- Permitir localização de ativos
- Exibir a localização em tempo real de ativos
- Enviar notificações automáticas sobre localização
- Gerenciar cadastro e configuração dos beacons
- Autenticar usuários com métodos seguros (OAuth2/JWT)
- Definir alertas de movimento inesperado ou perda de sinal de ativos
- Fornecer notificações contextuais baseadas na localização do usuário
- Permitir o compartilhamento de localização em tempo real entre usuários 
- Implementar navegação por voz com integração à sinalização física
- Permitir acesso aos mapas via QR Code e múltiplos canais
- Implementar busca avançada com autocompletar e busca por voz

# Guia de Estilo 

## Logotipo

<img src="imgs/restaurante-logo2.webp" alt="restauranteLogo" width="250"/>

### Espaço protegido e tamanho mínimo

O espaço protegido da Logo refere-se ao espaço livre que circunda a Logo em sua totalidade. Este espaço livre garante a colocação desobstruída e visível da Logo do Restaurante. Textos e imagens não podem violar o espaço protegido da Insígnia.

<img src="imgs/centralizado1.png" alt="GatewayConfig" width="250"/>
<img src="imgs/centralizado2.png" alt="GatewayConfig" width="250"/>
<img src="imgs/naoCentralizado1.png" alt="GatewayConfig" width="250"/>
<img src="imgs/naoCentralizado2.png" alt="GatewayConfig" width="250"/>

### Centralização a Insígnia 

A insígnia não é simétrica e deve ser centralizada usando sua esfera branca (centrada na esfera), não centrada no objeto (alinhada como um todo).

## Paleta de Cores
<h2 align="center">Cores Principais</h2>

<div align="center">
  <table>
    <tr>
      <td>
        <h3>Blue</h3>
        <img src="imgs/blocoAzul.png" alt="blocoAzul" width="200"/>
        <p>RGB 0/0/255</p>
        <p>HEX #0000ff</p>
        <p>CMYK 1/1/0/0</p>
      </td>
      <td>
        <h3>White</h3>
        <img src="imgs/blocoBranco.png" alt="blocoBranco" width="200"/>
        <p>RGB 255/255/255</p>
        <p>HEX #ffffff</p>
        <p>CMYK 0/0/0/0</p>
      </td>
      <td>
        <h3>Black</h3>
        <img src="imgs/blocoPreto.png" alt="blocoPreto" width="200"/>
        <p>RGB 0/0/0</p>
        <p>HEX #000000</p>
        <p>CMYK 0/0/0/1</p>
      </td>
    </tr>
  </table>
</div>


<h2 align="center">Tons de Azul</h2>

<div align="center">
<table>
<tr>
    <td>
    <h3>Byzantine Blue</h3>
    <img src="imgs/blocoByzantine.png" alt="blocoByzantine" width="200"/>
    <!--<span style="display:inline-block;width:200px;height:200px;background-color:#0054E9;border:1px solid #ccc;"></span> -->
    <p>RGB 0/84/233 </p>
    <p>HEX #0054E9</p>
    <p>CMYK 1.00/0.64/0/0.09</p>
      </td>
        <td>
    <h3>Sky Dancer</h3>
    <img src="imgs/blocoSky.png" alt="blocoSky" width="200"/>
       <!-- <span style="display:inline-block;width:200px;height:200px;background-color:#3B82F6;border:1px solid #ccc;"></span> -->
        <p>HEX #3B82F6</p>
        <p>RGB 59/130/246</p>
        <p>CMYK	0.76/0.47/0/0.04</p>
      </td>
        <td>
    <h3>Olympic Blue</h3>
    <img src="imgs/blocoOlympic.png" alt="blocoOlympic" width="200"/>
       <!-- <span style="display:inline-block;width:200px;height:200px;background-color:#3788ed;border:1px solid #ccc;"></span> -->
        <p>HEX #3788ed</p>
        <p>RGB 55/136/237</p>
        <p>CMYK	0.77/0.43/0/0.07</p>
  </td>
</tr>
</table>
</div>


<h2 align="center">Cores da Logo</h2>
<div align="center">
<img src="imgs/restaurante-logo2.webp" alt="GatewayConfig" width="250"/>


<table>
<tr>
  <td>

  <h3>White</h3>
  <img src="imgs/blocoBranco.png" alt="blocoBranco" width="200"/>
   <!-- <span style="display:inline-block;width:200px;height:200px;background-color:#FFFFFF;border:1px solid #ccc;"></span> -->
    <p>HEX #FFFFFF</p>
    <p>RGB 255/255/255</p>
    <p>CMYK	0/0/0/0</p>
</td>
<td>
    <h3>Olympic Blue</h3>
    <img src="imgs/blocoOlympic.png" alt="blocoOlympic" width="200"/>
        <!--<span style="display:inline-block;width:200px;height:200px;background-color:#3788ed;border:1px solid #ccc;"></span> -->
        <p>HEX #3788ed</p>
        <p>RGB 55/136/237</p>
        <p>CMYK	0.77/0.43/0/0.07</p>
</td>
</tr>
</table>
</div>


<h2 align="center">Body</h2>

<div align="center">
<table>
<tr>
  <td>
  <h3>White</h3>
  <img src="imgs/blocoBranco.png" alt="blocoBranco" width="200"/>
    <!--<span style="display:inline-block;width:200px;height:200px;background-color:#FFFFFF;border:1px solid #ccc;"></span> -->
    <p>HEX #FFFFFF</p>
    <p>RGB 255/255/255</p>
    <p>CMYK	0/0/0/0</p>
</td>
</tr>
</table>
</div>

<h2 align="center">Cores dos Textos</h2>
<div align="center">
<table>
<tr>
  <td>
    <h3>Black</h3>
    <img src="imgs/blocoPreto.png" alt="blocoPreto" width="200"/>
    <!--<span style="display:inline-block;width:200px;height:200px;background-color:#000000;border:1px solid #ccc;"></span>-->
    <p> RGB 0/0/0</p>
    <p> HEX #000000</p>
    <p>CMYK	0/0/0/1</p>
</td>
</tr>
</table>
</div>

<h2 align="center">Títulos (H1)</h2>

<div align="center">
<table>
<tr>
  <td>
    <h3>Black</h3>
    <img src="imgs/blocoPreto.png" alt="blocoPreto" width="200"/>
    <!--<span style="display:inline-block;width:200px;height:200px;background-color:#000000;border:1px solid #ccc;"></span>-->
    <p> RGB 0/0/0</p>
    <p> HEX #000000</p>
    <p>CMYK	0/0/0/1</p>
</td>
</tr>
</table>
</div>

<h2 align="center">SubTítulos (H2)</h2>

<div align="center">
<table>
<tr>
  <td>
  <h3>White</h3>
  <img src="imgs/blocoBranco.png" alt="blocoBranco" width="200"/>
    <!--<span style="display:inline-block;width:200px;height:200px;background-color:#FFFFFF;border:1px solid #ccc;"></span> -->
    <p>HEX #FFFFFF</p>
    <p>RGB 255/255/255</p>
    <p>CMYK	0/0/0/0</p>
</td>
</tr>
</table>
</div>


<h2 align="center">Cores dos Botões</h2>

<h3 align="center"><strong>BackGround</strong></h3>

<div align="center">
<table>
<tr>
  <td>
    <h3>Byzantine Blue</h3>
    <img src="imgs/blocoByzantine.png" alt="blocoByzantine" width="200"/>
    <!--<span style="display:inline-block;width:200px;height:200px;background-color:#0054E9;border:1px solid #ccc;"></span> -->
    <p>RGB 0/84/233 </p>
    <p>HEX #0054E9</p>
    <p>CMYK 1.00/0.64/0/0.09</p>
</td>

<td>
        <h3>Sky Dancer</h3>
        <img src="imgs/blocoSky.png" alt="blocoSky" width="200"/>
        <!--<span style="display:inline-block;width:200px;height:200px;background-color:#3B82F6;border:1px solid #ccc;"></span> -->
        <p>HEX #3B82F6</p>
        <p>RGB 59/130/246</p>
        <p>CMYK	0.76/0.47/0/0.04</p>
</td>
</tr>
</table>
</div>

<h3 align="center"><strong>Textos</strong></h3>

<div align="center">
<table>
<tr>
  <td>
    <h3>Black</h3>
    <img src="imgs/blocoPreto.png" alt="blocoPreto" width="200"/>
    <!--<span style="display:inline-block;width:200px;height:200px;background-color:#000000;border:1px solid #ccc;"></span>-->
    <p> RGB 0/0/0</p>
    <p> HEX #000000</p>
    <p>CMYK	0/0/0/1</p>

</td>
</tr>
</table>
</div>

<h2 align="center">Cores da NavBar</h2>

<div align="center">
<table>
<tr>
  <td>
        <h3>Sky Dancer</h3>
        <img src="imgs/blocoSky.png" alt="blocoSky" width="200"/>
        <!--<span style="display:inline-block;width:200px;height:200px;background-color:#3B82F6;border:1px solid #ccc;"></span> -->
        <p>HEX #3B82F6</p>
        <p>RGB 59/130/246</p>
        <p>CMYK	0.76/0.47/0/0.04</p>
</td>
</tr>
</table>
</div>


<h2 align="center">Cores dos Inputs</h2>

<div align="center">
<table>
<tr>
  <td>
  <h3>Placebo</h3>
  <img src="imgs/blocoPlacebo.png" alt="blocoPlacebo" width="200"/>
   <!-- <span style="display:inline-block;width:200px;height:200px;background-color:#E6E6E6;border:1px solid #ccc;"></span> -->
    <p>HEX #E6E6E6</p>
    <p>RGB 230/230/230</p>
    <p>CMYK	0/0/0/0.10</p>

</td>
</tr>
</table>
</div>


<h2 align="center">Cores da SideBar</h2>

<h3 align="center"><strong>Tittle</strong></h3>

<div align="center">
<table>
<tr>
  <td>

  <h3>White</h3>
  <img src="imgs/blocoBranco.png" alt="blocoBranco" width="200"/>
    <!--<span style="display:inline-block;width:200px;height:200px;background-color:#FFFFFF;border:1px solid #ccc;"></span> -->
    <p>HEX #FFFFFF</p>
    <p>RGB 255/255/255</p>
    <p>CMYK	0/0/0/0</p>

</td>
</tr>
</table>
</div>

<h3 align="center"><strong>Cores dos textos dos botões e ícones</strong></h3>

<div align="center">
<table>
<tr>
  <td>
    <h3>Black</h3>
    <img src="imgs/blocoPreto.png" alt="blocoPreto" width="200"/>
    <!--<span style="display:inline-block;width:200px;height:200px;background-color:#000000;border:1px solid #ccc;"></span>-->
    <p> RGB 0/0/0</p>
    <p> HEX #000000</p>
    <p>CMYK	0/0/0/1</p>

</td>
</tr>
</table>
</div>

<h3 align="center"><strong>Cor de Fundo</strong></h3>

<div align="center">
<table>
<tr>
  <td>
        <h3>Sky Dancer</h3>
        <img src="imgs/blocoSky.png" alt="blocoSky" width="200"/>
        <!--<span style="display:inline-block;width:200px;height:200px;background-color:#3B82F6;border:1px solid #ccc;"></span> -->
        <p>HEX #3B82F6</p>
        <p>RGB 59/130/246</p>
        <p>CMYK	0.76/0.47/0/0.04</p>
</td>
</tr>
</table>
</div>


<h2 align="center">Mapa</h2>

<h3 align="center"><strong>Cor de Fundo</strong></h3>

<div align="center">
<table>
<tr>
  <td>
    <h3>Desired Dawn</h3>
    <img src="imgs/blocoDawn.png" alt="blocoPDawn" width="200"/>
    <!--<span style="display:inline-block;width:200px;height:200px;background-color:#000000;border:1px solid #ccc;"></span>-->
    <p> RGB 217/217/217</p>
    <p> HEX #d9d9d9</p>
    <p>CMYK	0/0/0/0.15</p>
</td>
</tr>
</table>
</div>

<h3 align="center"><strong>Moveis</strong></h3>

<div align="center">
<table>
<tr>
  <td>
    <h3>Paris Paving</h3>
    <img src="imgs/blocoParis.png" alt="blocoParis" width="200"/>
    <!--<span style="display:inline-block;width:200px;height:200px;background-color:#000000;border:1px solid #ccc;"></span>-->
    <p> RGB 114/114/114</p>
    <p> HEX #727272</p>
    <p>CMYK	0/0/0/0.55</p>
</td>
</tr>
</table>
</div>

<h3 align="center"><strong>Paredes</strong></h3>

<div align="center">
<table>
<tr>
  <td>
    <h3>Black</h3>
    <img src="imgs/blocoPreto.png" alt="blocoPreto" width="200"/>
    <!--<span style="display:inline-block;width:200px;height:200px;background-color:#000000;border:1px solid #ccc;"></span>-->
    <p> RGB 0/0/0</p>
    <p> HEX #000000</p>
    <p>CMYK	0/0/0/1</p>
</td>
</tr>
</table>
</div>

<h3 align="center"><strong>Rastreador Profissionais</strong></h3>

<div align="center">
<table>
<tr>
  <td>
    <h3>Neon Blue</h3>
    <img src="imgs/blocoNeonBlue.png" alt="blocoNeonBlue" width="200"/>
    <!--<span style="display:inline-block;width:200px;height:200px;background-color:#000000;border:1px solid #ccc;"></span>-->
    <p> RGB 0/217/255</p>
    <p> HEX #00d9ff</p>
    <p>CMYK	1/0.15/0/0</p>
</td>
</tr>
</table>
</div>

<h3 align="center"><strong>Rastreador Mesas</strong></h3>

<div align="center">
<table>
<tr>
  <td>
    <h3>Shocking Pink</h3>
    <img src="imgs/blocoPink.png" alt="blocoPink" width="200"/>
    <!--<span style="display:inline-block;width:200px;height:200px;background-color:#000000;border:1px solid #ccc;"></span>-->
    <p> RGB 255/0/161</p>
    <p> HEX #ff00a1</p>
    <p>CMYK	0/1/0.37/0</p>
</td>
</tr>
</table>
</div>

## Tipografia / Fontes

Combinando personalidade tipográfica e clareza funcional, a dupla de fontes Cutive e Arimo oferece uma experiência visual marcante e consistente. Dos títulos aos campos de entrada, cada aplicação dessas fontes contribui para uma comunicação envolvente, que valoriza tanto o estilo quanto a legibilidade. O contraste entre a serifa clássica da Cutive e a modernidade limpa da Arimo cria uma hierarquia visual elegante, ideal para marcas que desejam se expressar com sofisticação e personalidade.

Essa combinação não apenas organiza a informação com precisão, mas também transmite valores de confiança, criatividade e foco no detalhe, essenciais para qualquer projeto com ambição estética e funcional.

As fontes podem ser aplicadas em preto ou branco, garantindo alto contraste e legibilidade em diferentes superfícies. Tons de cinza também são permitidos em ambientes digitais, especialmente para indicar estados secundários ou desativados. Tamanhos, espaçamentos e relações entre hierarquias tipográficas podem ser ajustados livremente, desde que respeitem a clareza visual e mantenham a harmonia entre Cutive e Arimo.

### Cutive
A Cutive, aplicada em títulos e subtítulos, evoca uma estética editorial com um toque clássico, garantindo presença visual forte e elegante em cada seção de destaque.    

<img src="imgs/Cutive.png" alt="blocoPreto" width="800"/>

### Arimo
A Arimo, por sua vez, é otimizada para leitura contínua e interatividade. Usada em campos de entrada e botões de texto, proporciona uma experiência fluida, funcional e moderna.    

<img src="imgs/Arimo.png" alt="blocoPreto" width="800"/>

## Interface de Usuário

<!--### Layout -->


### Mapa do Restaurante
1ª Opção

O mapa foi desenvolvido para monitorar as atividades dos profissionais do restaurante, permitindo o envio de notificações com base em suas localizações, além de possibilitar a geolocalização individual sempre que necessário. Ele também auxilia na identificação das mesas e na organização do espaço interno.

Além do uso interno, o mapa também pode ser acessado pelos clientes, oferecendo uma experiência mais intuitiva. Os clientes conseguem se localizar dentro do restaurante, encontrar garçons com mais facilidade e identificar a localização de ambientes como os banheiros.

 
<img src="imgs/prototicoTela-mapa2.png" alt="protótipoTelaMapa2" width="250"/>    

Este mapa está presente na tela principal do aplicativo e exibe uma representação estática da planta do restaurante, incluindo esboços das mesas (identificadas por pontos rosas e com um localizador único), cadeiras, banheiros, cozinha e paredes.

Já os profissionais do restaurante, por estarem em constante movimentação, são representados por pontos azuis, indicando sua posição em tempo real.

Além disso, o mapa conta com ícones que ajudam na identificação visual dos ambientes, como a cozinha e os banheiros, tornando a navegação mais intuitiva tanto para colaboradores quanto para clientes.

2ª Opção

🎛️ Guia de Estilo – Seção: Layout do Mapa de Monitoramento

📍 Objetivo do Mapa

O mapa tem como função principal representar, de forma visual e intuitiva, a disposição geográfica do restaurante e a localização em tempo real dos profissionais. Ele também oferece suporte à navegação dos usuários (clientes e colaboradores), promovendo eficiência no atendimento e autonomia na experiência.

🧭 Localização no App
Tela: Página inicial do aplicativo - Primeira tela pós Login (Home)

Visibilidade: Sempre visível para colaboradores e clientes

Posição na tela: Ocupa toda a proporção da tela com rolagem ou redimensionamento responsivo conforme o dispositivo

🧩 Elementos do Mapa

| Elemento                      | Representação visual     | Comportamento                           |    
| Mesas                         | Pontos rosa (estáticos)  | Exibem identificador único (ID visual)  |    
| Profissionais                 | Pontos azuis (dinâmicos) | Movimentam-se conforme a geolocalização |    
| Cadeiras e moveis da cozinha  | Contorno cinza escuro    | Estáticos, ajudam na orientação visual  |    
| Banheiro e paredes            | Ícones temáticos         | Ícones personalizados com legenda       |    


🎨 Estilo Visual
Cores:

Profissionais: Azul (#00D9FF)

Mesas: Rosa (#FF00A1)

Fundo do mapa: Cinza-claro (#D9D9D9)

Ícones de ambiente: Cinza-escuro (#727272), alguns com contornos

Ícones: Fundo Branco (#FFFFFF), com desenho preto(#000000)

Texto: Identificadores de ambientes, legíveis em tamanho mínimo de 12px e cor preta(#000000)

🧑‍💼 Uso pelos Colaboradores
Monitoramento em tempo real da equipe

- Envio de notificações baseadas na localização

- Visualização rápida da ocupação e movimentação no salão

🧑‍🍳 Uso pelos Clientes
- Autolocalização no espaço do restaurante

- Localização de garçons e espaços como banheiros

🕹️ Interações

- Zoom com dois dedos 


### Ícones

Icone para identificar banheiro no mapa do restaurante:  

<img src="imgs/banheiro-logo.jpg" alt="banehiroIcone" width="150"/>

Icone para identificar cozinha no mapa do restaurante:    

<img src="imgs/icone-cozinha.png" alt="cozinhaIcone" width="150"/>

#### Icones SideBar
Icone para identificar tela de Ajuda na SideBar:   

<img src="imgs/icone-ajuda-branco.png" alt="ajudaBIcone" width="150"/>

Icone para identificar tela de Ajuda na SideBar:    

<img src="imgs/icone-ajuda-preto.png" alt="ajudaPIcone" width="150"/>

Icone para identificar tela de Configurações na SideBar:  

<img src="imgs/icone-configuracoes.png" alt="configIcone" width="150"/>

Icone para identificar tela de Monitoramento na SideBar:    

<img src="imgs/icone-monitoramento.png" alt="monitoramentoIcone" width="150"/>

Icone para sair da conta logada e retornar para tela de login:  

<img src="imgs/icone-sair.png" alt="sairIcone" width="150"/>

<!-- ### Imagens -->

## Componentes da Interface de Usuário

### Botões

Os botões no aplicativo têm a função principal de guiar o usuário na navegação entre páginas. Para garantir clareza e consistência visual, todos os botões utilizam a coloração Azul Bizantino ou fundo Azul Dançarina do Céu, uma escolha que se destaca na interface sem comprometer a harmonia visual do layout. A tipografia aplicada é a fonte Arimo, com peso e tamanho variando conforme a hierarquia da ação: 40pt para ações primárias e 20pt para ações secundárias.

#### Botão de Login 

O botão de login deve permanecer com opacidade reduzida até que todos os campos obrigatórios sejam corretamente preenchidos pelo usuário.

<img src="imgs/button-img2.png" alt="botao" width="150"/>

<img src="imgs/button-img.png" alt="botao" width="150"/>

#### Botões da SideBar
Abrir ou Fechar SideBar:

<img src="imgs/button-abrirSideBar.png" alt="botaoSideBar" width="51"/>

Botões para acessar outras telas:
 
<img src="imgs/button-upSideBar.png" alt="botaoSideBar" width="150"/>

### Side Bar

A Sidebar estará presente em todas as telas após o login, servindo como o principal meio de navegação dentro do aplicativo. Ao ser aberta, ela sobrepõe o conteúdo da tela com opacidade reduzida ao fundo, destacando o menu lateral e direcionando o foco do usuário para a navegação. Com fundo em Azul Bizantino, os ícones e botões em preto ganham destaque, garantindo contraste visual adequado e facilitando a identificação das opções disponíveis.

<img src="imgs/sidebar.png" alt="SideBar" width="250"/>

### Inputs

Os campos de input estão localizados na Tela de Login do sistema e são responsáveis por receber as informações inseridas pelo usuário para acesso ao aplicativo. Eles possuem fundo em cinza escuro, oferecendo um contraste suave com o restante da interface. Cada campo apresenta um texto placeholder com visibilidade reduzida, servindo como indicação do conteúdo esperado (e-mail e senha), sem causar distração visual. Esse recurso auxilia na orientação do usuário de forma discreta e eficaz.

<img src="imgs/input.png" alt="input" width="150"/>

<img src="imgs/input1.png" alt="inputPreenchido" width="150"/>

<!-- ### NavBar -->

## Resumo SDKs / Bibliotecas para gerenciar os Mapas, Conexões BlueTooth, Gerar Rotas Otimizadas

### Flutter Map (Baseado em Leaflet para Web)

**Propósito:** Exibição de mapas interativos.

**Integração Flutter:** Extremamente bem integrado com Flutter, pois é uma biblioteca nativa do Dart/Flutter que replica a funcionalidade do Leaflet (uma biblioteca JavaScript popular para mapas interativos).

**Funcionalidades:** Permite exibir mapas do **OpenStreetMap** (OSM) ou de outros provedores de tiles, adicionar marcadores (POIs personalizados), desenhar polilinhas para rotas e polígonos, e lidar com interações do usuário (zoom, pan).

**Limitações:** Por si só, não oferece roteamento nem funcionalidades 3D avançadas, e não tem suporte nativo para navegação indoor complexa ou beacons. Você precisará complementar.

**FeedBack:** 
- Consegui utilizar. 
- No mapa, utilizado pelo OpenStreetMap, não consegui localizar uma opção para importar imagem. Pesquisando descobri que através de ferramentas externas isso é possível.
- Não necessita de mensalidade e não é necessário solicitar uma Demo.

Links: https://pub.dev/packages/flutter_map | https://docs.fleaflet.dev/ | https://www.openstreetmap.org/

### Flutter OSM (Pacote para OpenStreetMap)

**Propósito:** Oferecer um conjunto de funcionalidades baseadas no OpenStreetMap para Flutter.

**Integração Flutter:** É um pacote Flutter que visa simplificar a interação com dados e serviços do OSM.

**Funcionalidades:** Inclui funcionalidades básicas de mapa, talvez algumas operações de pesquisa e desenho. É mais uma abstração para usar OSM no Flutter.

**FeedBack:** 
- Consegui utilizar. 
- No mapa, utilizado pelo OpenStreetMap, não consegui localizar uma opção para importar imagem. Pesquisando descobri que através de ferramentas externas isso é possível.
- Não necessita de mensalidade e não é necessário solicitar uma Demo.

Links: https://pub.dev/packages/flutter_osm_plugin | https://www.openstreetmap.org/

### Packages de Roteamento (Para Navegação Indoor/Outdoor)

**Propósito:** Gerar rotas otimizadas.

**Integração Flutter:** Não há um SDK de roteamento open source diretamente integrado ao Flutter no sentido de uma biblioteca UI. Em vez disso, você consumiria APIs de servidores de roteamento open source.

**Servidores de Roteamento Open Source:**

- OSRM (Open Source Routing Machine): Você pode configurar seu próprio servidor OSRM e consumir sua API HTTP REST no seu aplicativo Flutter. Isso é ideal para roteamento outdoor.

- GraphHopper: Similar ao OSRM, você pode configurar seu próprio servidor GraphHopper e consumir sua API. Também é excelente para roteamento outdoor.

**Para Navegação Indoor:** Para rotas otimizadas em ambientes indoor, você precisará de uma solução customizada. Isso envolve:

- Definir sua própria rede de navegação indoor (nós e arestas representando corredores, portas, etc.).

- Implementar um algoritmo de busca de caminho (como A* ou Dijkstra) em Dart no seu aplicativo Flutter, ou ter um servidor customizado que receba a posição e o destino indoor, calcule a rota e retorne os pontos para serem desenhados no flutter_map.

### MapLibre GL

**Tipo:** Open Source

**Plataforma:** iOS, Android, Web (pode ser usado via Flutter wrapper)

**Requisitos atendidos:**
- Mapas interativos com POIs personalizados
- Suporte a mapas 2D/3D (via estilo)
- Compatível com dados customizados indoor/outdoor (ex: GeoJSON, MBTiles)

**Observações:** Alternativa totalmente gratuita e de código aberto, MapLibre GL JS é um "fork" (ramificação) do Mapbox GL JS v1 e é uma boa opção. Para indoor, precisa de dados próprios.

<img src="imgs/MapLibreGL.png" alt="MapLibreGL" width="400"/>

Flutter plugin: maplibre_gl (https://pub.dev/packages/maplibre_gl)

### Mapbox GL JS

**Gratuito até certo ponto:** O Mapbox oferece um nível gratuito generoso. Para SDKs de mapas para dispositivos móveis (iOS/Android), são até 25.000 MAUs (usuários ativos mensais) gratuitos por mês.

**Custos:** Após exceder o nível gratuito, você começa a ser cobrado por unidade (geralmente por 1.000 usos). As taxas variam de acordo com o serviço. Por exemplo, para Mapbox GL JS, após os 50.000 carregamentos gratuitos, você pagaria cerca de US$ 5,00 por cada 1.000 carregamentos adicionais.

**Carregamentos de mapa:** No Mapbox GL JS v2.0 e superior, um "carregamento de mapa" é contado sempre que um objeto Mapbox GL JS Map é inicializado em uma página da web. Uma sessão de 12 horas onde o usuário interage com o mapa é contada como um carregamento.

### IndoorAtlas SDK (plano gratuito limitado)

**Tipo:** SDK proprietário com plano gratuito para testes(30 dias)

**Plataforma:** iOS, Android

**Requisitos atendidos:**
- Navegação indoor com beacons (usa Bluetooth + magnetômetro)
- POIs personalizados
- Rotas otimizadas indoor

**Observações:** 

**Plano Gratuito (Teste):**

- **Preço:** Gratuito por 30 dias.

- **Recursos:**

- Crie uma conta de desenvolvedor gratuita.

- "Fingerprint" (mapeie) seu local indoor usando a ferramenta IndoorAtlas MapCreator.

- Tenha uma licença não-produção.

- Trabalhe com um limite de até 5.000 m² de área de local.

- **Observações:** Pude observar pelo período de teste gratis que a plataforma é bem explicativa. Mostrando o passo a passo para começar a utilizar, vídeos explicativos de como adicionar seu mapa de planta baixa, coletar os dados para gerar o mapa no seu app, documentação muito explicativa, exemplos no GitHub para Android e IOS, etc. Para utilizar o plano gratuito de 30 dias basta solicitar no próprio site.

Links: https://app.indooratlas.com/ | https://www.indooratlas.com/ | https://indooratlas.freshdesk.com/support/solutions/articles/36000088440-example-projects-utilizing-indooratlas-sdk?utm_campaign=onboarding-jan24&utm_medium=email&utm_source=indooratlas-onboarding&utm_id=indooratlas-boarding | https://docs.indooratlas.com/?utm_campaign=onboarding-jan24&utm_medium=email&utm_source=indooratlas-onboarding&utm_id=indooratlas-boarding | https://www.youtube.com/@IndoorAtlasLtd/videos |

**Develop Lite (Desenvolvimento Leve):**

- Preço: €59 / mês (preço sem impostos).

- Ideal para: Desenvolvedores de aplicativos que estão explorando a plataforma IndoorAtlas.

**Develop (Desenvolvimento):**

- Preço: €400 / mês (preço sem impostos).

- Recursos: Plano de desenvolvimento completo, incluindo suporte à integração e sem limitações de recursos ou locais.

- Ideal para: Equipes que precisam de acesso total aos recursos e suporte.

**Pro (Profissional):**

- Preço: €349 / local / mês (preço sem impostos).

- Ideal para: Implantações em produção de até 10.000 m², com um conjunto de recursos simplificado.

**Enterprise (Empresarial):**

- Preço: Varia com base no volume, recursos e nível de suporte.

- Recursos: Soluções personalizadas para uso comercial em múltiplos locais, escopo de recursos definido e Acordo de Nível de Serviço (SLA).

- Ideal para: Grandes empresas com necessidades específicas.

**Além dos planos base, há recursos adicionais que podem ser adicionados com custos extras, como:**

- Heatmap: +€25 / mês

- Augmented Reality (Realidade Aumentada): +€50 / mês

- Positioning REST API: +€25 / mês

- Data REST API: +€25 / mês

### Navigine SDK (Open API com plano gratuito)

**Tipo:** SDK com plano gratuito

**Plataforma:** iOS, Android, Web

**Requisitos atendidos:**
- Navegação indoor via Bluetooth beacons
- POIs personalizados
- Roteamento indoor
- Mapas customizáveis (2D/3D via WebView ou nativo)

**Observações:** Possui dashboard online e API REST; open API, mas não é 100% open source. Não consegui uma demo ou um período de testes. Para uma demonstração ou solicitar uma demo é necessário marcar uma conversa.

Links: https://navigine.com/ | 

**Plano Gratuito (Free Tier):**

- Mapbox SDKs para Mobile (iOS/Android): Oferece até 25.000 MAUs (usuários ativos mensais) por mês gratuitamente.

- Outros serviços Mapbox (como Directions API, Geocoding API) também possuem seus próprios níveis gratuitos.

**Planos Pagos (Após o Free Tier):**

- Após exceder os limites do nível gratuito, o uso é cobrado por unidade (geralmente por 1.000 usos).

- Mapbox SDKs para Mobile: A partir de aproximadamente US$ 4,00 por cada 1.000 MAUs adicionais (após os 25.000 MAUs gratuitos).

- As taxas variam para outros serviços e volumes de uso.

### Mapwize (by Mappedin)

**Tipo:** SDK gratuito com limitação de uso

**Plataforma:** Web, iOS, Android

**Requisitos atendidos:**
- Navegação indoor
- POIs personalizados
- Mapas interativos indoor
- Compatível com localização via beacons

**Recursos Comuns (Mappedin):**

- Mapas interativos

- Wayfinding (orientação)

- Editor de mapas

- Atualizações em tempo real

- UI personalizável

- Análises

- SDKs para Mobile e Web

- Integração com quiosques

- Posicionamento indoor

- Funcionalidade de busca

- Navegação multi-andar

- Geofencing

- Modo offline

- Mapas 3D

- Acesso à API

- Gerenciamento de usuários

- Exportação de mapas

- Localização

- Recursos de acessibilidade

Links: https://app.mappedin.com/ | https://www.mappedin.com/ |

**Mappedin-vs-Mapwize:**  Link do Blog: https://www.mappedin.com/resources/blog/mappedin-vs-mapwize/ 

**Observações:** Precisa de cadastro no sistema. Parte do sistema é open (como plugins). A Mappedin também lançou uma ferramenta de mapeamento indoor gratuita chamada Mappedin Maker, focada em segurança em escolas e espaços públicos, permitindo a criação de mapas vetoriais de edifícios.
Para criar seu mapa ou upar uma imagem de planta baixa basta acessar o site https://app.mappedin.com/

**Plano Gratuito (Free Tier):**

- A Mappedin oferece um plano Gratuito que permite criar o seu primeiro mapa digital.

- Navegação interna

- Ajude os visitantes a encontrar o caminho mais rapidamente com a navegação interna intuitiva
Mapeamento de IA

- Transforme plantas baixas em mapas interativos em segundos
Colaboração em tempo real

- Colabore em mapas com acesso compartilhado, edições em tempo real e controles baseados em funções
Compartilhe e incorpore

- Publique seu mapa instantaneamente compartilhando um link ou incorporando-o em seu site — sem necessidade de código
Exportar para PDF e MS Places

- Exporte mapas para acesso offline, backups ou integração com plataformas como o Microsoft Places
Aplicativo iOS Mappedin Scan

**Planos Pagos (Assinaturas da Mappedin):** A precificação da Mappedin é baseada por mapa, e não por espaço de trabalho ou usuário. Cada mapa atualizado adiciona à sua assinatura.

**Plus:** 
- US$ 25 por mapa/mês (faturado anualmente).

- Para mapas ricos em conteúdo.

**Advanced:** 
- US$ 85 por mapa/mês (faturado anualmente).

- Para gerenciar locais complexos com precisão e flexibilidade. Mapas podem incluir vários edifícios.

**Pro:** 
- US$ 165 por mapa/mês (faturado anualmente).

- Acesso total a API e SDK para construir funcionalidades avançadas sobre seus mapas. Mapas podem incluir vários edifícios.

**Enterprise:** 
- Preço sob consulta (faturado anualmente).

- Para grandes empresas e necessidades específicas, com preços baseados em volume.

### PathGuide (Microsoft Research)

**Tipo:** Open source

**Plataforma:** Android

**Requisitos atendidos:**
- Navegação indoor
- Mapas customizados
- Roteamento offline indoor

**Observações:** Não usa beacons, mas pode ser adaptado. Projeto acadêmico, foco em ambientes internos com detecção baseada em sensores do celular.

## Como funciona a importação de imagens como planta baixa(OpenStreetMap):

Georreferenciamento da Imagem:

Este é o passo mais crucial. Sua imagem de planta baixa precisa ser georreferenciada. Isso significa que você precisa associar coordenadas geográficas (latitude e longitude) aos pixels da sua imagem. Ferramentas de SIG (Sistema de Informação Geográfica) como o QGIS (open source e gratuito) são ideais para isso. No QGIS, você carregaria sua imagem e, em seguida, selecionaria pontos conhecidos na imagem e os correlacionaria com pontos correspondentes em um mapa real (por exemplo, a esquina de um prédio que você vê tanto na planta quanto no mapa).

Geração de Tiles (Opcional, mas recomendado para performance):

Uma vez georreferenciada, a imagem pode ser grande. Para um bom desempenho em aplicações web ou móveis, é altamente recomendado dividir essa imagem em "tiles" (pequenas imagens quadradas em diferentes níveis de zoom). Ferramentas como GDAL2Tiles (parte do GDAL, um conjunto de ferramentas open source para dados geoespaciais) ou funções em QGIS podem fazer isso. Isso permite que a aplicação carregue apenas as partes da imagem que estão visíveis na tela, melhorando a fluidez da navegação.

Exibição no Mapa:

As bibliotecas de mapeamento (como Leaflet ou OpenLayers para web, ou Flutter Map para Flutter, que são frequentemente usadas com OSM) permitem que você adicione uma "camada de imagem" ou uma "camada de tiles" personalizada sobre o mapa base do OSM.

Se você gerou tiles, você especificaria o diretório onde os tiles estão armazenados, e a biblioteca de mapa faria o resto, exibindo sua planta baixa no local correto e nos níveis de zoom apropriados.

Se for uma única imagem georreferenciada (menos comum para grandes áreas ou para performance), você forneceria a imagem e suas coordenadas de canto, e a biblioteca a posicionaria.

### Exemplo de Fluxo de Trabalho (com QGIS e Flutter):

No QGIS:

Carregue um mapa base do OpenStreetMap.

Carregue sua imagem da planta baixa.

Use a ferramenta "Georreferenciador" para alinhar sua planta baixa com o mapa base, marcando pontos de controle.

Exporte a imagem georreferenciada (por exemplo, como um GeoTIFF).

(Opcional, mas recomendado para performance) Use o GDAL para gerar tiles a partir do seu GeoTIFF georreferenciado.

No seu aplicativo Flutter (com flutter_map):

Configure seu Flutter Map para exibir o mapa base do OpenStreetMap.

Adicione uma TileLayer (se você gerou tiles da sua planta baixa) ou uma ImageOverlay (se for uma única imagem georreferenciada) apontando para os dados da sua planta baixa.

### Dart

// Exemplo simplificado de como adicionar uma camada de imagem ou tiles no flutter_map// Isso assume que você já tem seus tiles ou imagem georreferenciada servida em uma URL

FlutterMap(

  options: MapOptions(

    initialCenter: LatLng(-19.9167, -43.9333), // Belo Horizonte

    initialZoom: 17.0, // Zoom adequado para ver a planta baixa

  ),

  children: [

    // Camada base do OpenStreetMap

    TileLayer(

      urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',

      userAgentPackageName: 'com.example.app',

    ),

    // Sua camada de planta baixa (se for uma única imagem georreferenciada)

    // ImageOverlay(

    //   imageUrl: 'https://seuservidor.com/sua_planta_baixa_georreferenciada.png',

    //   bounds: LatLngBounds(

    //     LatLng(lat_min, lon_min),

    //     LatLng(lat_max, lon_max),

    //   ),

    // ),

    // Ou, se você gerou tiles da sua planta baixa

    TileLayer(

      urlTemplate: 'https://seuservidor.com/tiles_da_planta_baixa/{z}/{x}/{y}.png',

      maxZoom: 22, // Ajuste para o zoom máximo dos seus tiles

      minZoom: 16, // Ajuste para o zoom mínimo dos seus tiles

      // Adicione a opção 'tms: true' se seus tiles seguem o esquema TMS

    ),

    // Outros marcadores, rotas, etc.

  ],

);

### Limitações e Considerações:

Navegação Semântica: A imagem da planta baixa é apenas uma "foto" do local. Para que a navegação indoor funcione com rotas otimizadas, você precisará digitalizar os elementos navegáveis (corredores, portas, escadas) dessa planta baixa como dados vetoriais (pontos e linhas) e construir uma rede de navegação sobre ela.

Atualização: Se a planta baixa mudar, você precisará repetir o processo de georreferenciamento e re-geração de tiles/imagens.

Serviço de Imagens: Você precisará de um local para hospedar suas imagens georreferenciadas ou tiles (um servidor web ou um serviço de armazenamento de objetos) para que seu aplicativo possa acessá-las.

Em resumo, o OpenStreetMap fornece a base de dados global, e as bibliotecas de mapeamento no Flutter permitem que você sobreponha suas próprias imagens georreferenciadas (como plantas baixas) para criar uma experiência de mapa personalizada e rica.

<!--## SDKs Pagos

### Google Maps (Indoor Maps + AI Positioning)

Não consegui utilizar, provavelmente pago.

### Mapwize

Necessário entrar em contato para utilizar, provavelmente pago. 

Também achei um projeto no GitHub de 7 anos atras explicando sobre como utilizar(Documentação), porém todos os links estão desatualizados. 
Link do Repositorio: https://github.com/lightcomms/mapwize-app-android

Necessário uma imagem de planta baixa em formato PNG ou CAT.

### Mappedin 
 
Apesar de complicado é possível criar um mapa de planta baixa pelo aplicativo do navegador: https://app.mappedin.com/

Com este mapa é possível carregar o mapa criado ou upado, porém não encontrei seu SDK para flutter.

SDK pago.
 
### Mapwize X Mappedin

Link do Blog: https://www.mappedin.com/resources/blog/mappedin-vs-mapwize/

### IndoorAtlas

Compatível com Flutter, com um período de 30 dias gratis para utilização

## SDKs/ Bibliotecas / Plug-ins Gratis 

### FlutterBlue

FlutterBlue é um plugin bluetooth para Flutter, um novo SDK de aplicativo para ajudar desenvolvedores a criar aplicativos multiplataforma modernos.

DESATUALIZADO!!!! VERSÃO ATUALIZADA flutter_blue_plus

Documentação: https://pub.dev/documentation/flutter_blue/latest/

Feedbacks: https://news.ycombinator.com/item?id=18726927

### flutter_blue_plus 1.35.5

Versão atualizada do FlutterBlue

### flutter_beacon

Plugin Flutter para trabalhar com iBeacons.

Um SDK híbrido de scanner e transmissor iBeacon para o plugin Flutter. Compatível com Android API 18+ e iOS 8+.

Características:

- Gerenciamento automático de permissões
- iBeacons de alcance
- Monitoramento de iBeacons
- Transmitir como iBeacon

Documentação: https://pub.dev/documentation/flutter_beacon/latest/

### flutter_ai_indoor_navigation

Este plugin é um wrapper para o SDK de navegação Combinain Indoor AI. Ele oferece uma maneira simples de integrar o SDK ao seu aplicativo Flutter.

Documentação: https://pub.dev/packages/flutter_ai_indoor_navigation -->

## Protótico das Telas

https://www.figma.com/design/W0plh8cuBi3uZzoExPJ3hp/Prototico-Telas-RLTS-Restaurante?node-id=4-12&t=O6n1W7R0CxlQVtlf-1

### GIF IPHONE

![COMPILER IPHONE](imgs/PrototicoTelas(IPHONE16).gif)

### GIF ANDROID

![COMPILER ANDROID](imgs/PrototicoTelas(ANDROID).gif)


#### Referências
https://colorkit.co/color/3788ed/  
https://www.color-hex.com/color/3b82f6  
http://styleguides.io/  
