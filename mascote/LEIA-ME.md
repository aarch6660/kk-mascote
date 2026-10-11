# Bonecas — mascote do Hyprland

Implementado em 2026-10-08 para Godot 4.7.2 / Hyprland 0.56.2. **Funciona como mascote; ainda exige teste humano de clique nas bordas e do seletor de janelas.** A fidelidade ao shader original do Koikatsu continua com as limitações do visualizador.

```bash
~/Games/kk-mascote/mascote/iniciar.sh               # liga; repetir desliga
~/Games/kk-mascote/mascote/iniciar.sh --retrato     # inicia cabeça e ombros
~/Games/kk-mascote/mascote/iniciar.sh --parar       # somente desliga
~/Games/kk-mascote/mascote/iniciar.sh --status      # PIDs da instância
~/Games/kk-mascote/mascote/iniciar.sh --teste-clique
```

Uma instância de Godot, acompanhada por um supervisor Python que também faz a ponte IPC. `flock` impede duplicatas. O supervisor guarda PID + starttime no runtime, sinaliza exclusivamente seu processo e encerra seu filho. Menu Sair também encerra o supervisor e desfaz os recursos temporários. Godot portátil padrão: `~/.local/opt/godot/godot`; pode ser substituído com `GODOT=/caminho`.

Clique esquerdo alterna defesa/alegria; arrastar pega, soltar deixa cair. Rodinha altera o tamanho entre 0,3 e 3,0, limitado pela altura disponível; clique direito oferece modo retrato/passeio, moldura, dormir/acordar, tamanhos P (0,5), M/padrão (0,75), G (1,5), escolha de boneca e sair. Boneca ativa, posição do apoio e escala ficam em `~/.cache/forja/kk-mascote.json`, gravadas atomicamente nas interações, a cada cinco segundos e no desligamento. Sono pelo menu persiste até acordar pelo menu ou cutucar. Sono automático ocorre após três minutos sem movimento do mouse nem atividade de teclado; movimento próximo acorda.

A personagem respira, anda, faz gestos, senta na extremidade de uma janela e dorme. Transições de clipes usam blend de 0,35 s. A física trabalha em pixels lógicos: gravidade, colisão por cruzamento do topo, salto balístico para janela próxima e apoio identificado pelo endereço IPC. A janela de apoio arrasta a personagem consigo; fechar, ocultar ou trocar de workspace remove o apoio. Topos muito altos para caber a personagem são ignorados. A base desconta a reserva inferior do monitor; nesta sessão a barra reserva 42 px no topo, não embaixo.

Cabeça e dois ossos dos olhos seguem o cursor próximo, com limites; oito malhas usam o shape `piscar`. A cabeça também se orienta brevemente para janela nova próxima ou mudança de foco. Os **73 GLBs** atualmente presentes em `animacoes/exportados/` foram copiados, importados e conferidos contra os três esqueletos: nenhuma pista ausente. O app aplica os mesmos materiais KK do visualizador, com manifesto próprio de cada boneca; não depende do jogo durante a execução.

## Janela e clique

Padrão: **XWayland (`--driver x11`), OpenGL/Intel**, viewport 3D com resolução adaptativa dentro de uma janela transparente do tamanho lógico do monitor. A janela fica flutuante, fixada aos workspaces e acima das outras. `--gpu inherit` usa o ambiente gráfico herdado e Forward+/Vulkan, podendo ativar a NVIDIA; não foi medido como padrão de desktop.

`DisplayServer.window_set_mouse_passthrough` recebe o contorno do alfa renderizado a cada três frames (10 Hz na animação; 30 Hz por meio segundo após interação), acompanhando os ossos e shape keys. A posição e a região se atualizam a cada frame. O Godot permite apenas um polígono: usa-se o maior contorno conectado por área; detalhes separados e a simplificação de 0,75 px merecem teste humano. Com menu aberto, a região também abrange o menu. Não usar polígono vazio para liberar tudo: no Godot isso **captura a janela inteira**.

**A API sozinha não resolveu esta sessão.** No Wayland, o polígono não é implementado nesta versão. No XWayland, o Hyprland continua testando a caixa da janela para escolher foco/encaminhamento a clientes Wayland. Por isso, o supervisor consulta cursor/contorno a 60 Hz com mouse em movimento, 20 Hz parado e 10 Hz dormindo e altera apenas `no_focus` de sua regra temporária: fora libera o desktop, dentro permite mouse. A ponte considera separadamente a silhueta e o retângulo do menu, liberando o vazio entre ambos. Estado com PID errado ou sem atualização por dois segundos libera o desktop; o botão pressionado mantém a captura até soltar. Uma assinatura temporária `hl.on("window.active")` restaura o foco anterior no mesmo callback quando a Chika é escolhida. Godot também desativa seu próprio pedido de foco após criar a janela, evitando a janela override-redirect que perdeu toda a interação no primeiro ensaio.

Com essa combinação, **os dois drivers passaram no receptor automático**: vazio recebido pelo receptor, Chika recebendo sem vazamento, foco preservado e zero cliques fora no Godot. XWayland foi escolhido porque mantém também a máscara de entrada do Godot. Houve perda ocasional de cliques perto da cabeça em movimento durante ensaios posteriores. O controle depende de IPC e de snapshots: perto do contorno/transições pode haver atraso; **não considerar o clique perfeito ou definitivamente encerrado antes do teste humano**.

A barra desta sessão só exibe o aplicativo focado; a restauração evita a Chika ali. **Exclusão universal de barra/Alt-Tab não foi resolvida:** o Hyprland removeu `_NET_WM_STATE_SKIP_TASKBAR/SKIP_PAGER`, e a Chika continua em `hyprctl clients`. O seletor atual **SUPER+TAB**, em `~/.config/hypr/scripts/menu.sh`, enumera todos os clientes e precisa filtrar a classe `kk-mascote`: adicionar `if c["class"] == "kk-mascote": continue` no laço da opção `janelas`. Essa alteração fica para aprovação; a configuração do usuário não foi alterada. As regras de não foco reduzem sua seleção quando o cursor está fora, mas não substituem esse filtro.

O ambiente desta sessão tinha `DISPLAY=:1` com o socket `X1` ausente e listener `X1_` vivo. Quando isso ocorre, o supervisor cria um alias exclusivo e temporário em `/tmp/.X11-unix/X190..249`, usa o display correspondente e remove o alias ao fechar. Não altera os sockets existentes. Se Godot cair para outro driver, o supervisor encerra e registra o erro.

## Hyprland e regras

Nada em `~/.config/hypr` é editado. `regras-mascote.lua` é a proposta para revisão, **não instalada**. O lançador aplica a regra com nome exclusivo via `hyprctl eval`, cria as assinaturas de foco/atividade, desativa a regra e remove as assinaturas ao terminar. Reaplica após `configreloaded`, necessário quando o modo jogo faz reload. Mesmo com o trecho definitivo instalado, a ponte do supervisor continua necessária para entrada/foco.

Tela cheia real (`fullscreen & 2`) e `animations:enabled=false` ocultam a Chika e liberam o mouse; voltar ao normal restaura. A detecção de modo jogo segue o efeito de `~/.config/hypr/scripts/modo-jogo.sh`, sem executá-lo nem modificá-lo. **O script existente lê `["int"]`, mas este Hyprland devolve `["bool"]`; SUPER+G pode falhar antes de mudar o modo.** O detector do mascote foi validado mudando a opção temporariamente via Lua e restaurando o valor original. A correção do atalho existente fica pendente de aprovação fora deste projeto.

A ponte usa socket IPC e socket2, consulta geometria a cada 300 ms e antecipa a consulta quando chegam eventos. Registra só geometria/classe/endereço, nunca títulos nem teclas. Monitores são convertidos para coordenadas lógicas, incluindo escala/transformação; apenas eDP-1, 1920×1080, escala 1 foi testado realmente. A lista de chãos considera janelas mapeadas do workspace/scratchpad e fixadas; **não reconstrói oclusão pixel a pixel entre janelas sobrepostas**.

## Provas e desempenho

`evidencias/cliques.json`: comparação real Wayland/XWayland com a ponte. `headless-fisica-estados.json`: queda, apoio móvel, remoção, salto, base, arrasto e estados. `headless-ponte.json`: dez casos de região de entrada, menu, grab, validade do estado e PID. `headless-rig.json`: 40 clipes, ossos, piscar e limite da cabeça após 600 atualizações sem acumular rotação. `interacoes.json` guarda a sequência final; falhas anteriores estão nos diretórios de histórico; `menu.json` é o reteste específico após corrigir o menu — resultados negativos antigos não foram apagados. A sequência final de interações passou; o menu com mira no torso passou. `menu-borda.json` preserva uma rodinha perdida ao mirar a cabeça depois de acordar.

Capturas `em-cima-janela.png`, `sentada.png`, `dormindo.png` foram feitas via **grim na sessão real**; `capturas-status.json` guarda pose/apoio no instante. Os testes encerram seus processos, retiram regras/assinaturas e restauram cursor/foco; a prova não altera a preferência salva.

`desempenho.json` mede CPU por PID (100% = um núcleo lógico), RSS e ocupação acumulada da Intel pelo DRM fdinfo. Respiração no reteste: aproximadamente 40–45% de um núcleo no Godot + 6% no supervisor e 5% da engine de renderização da Intel. Os percentuais de CPU são por núcleo, e a GPU é somente a engine usada pelo processo. Dormindo a animação e a renderização param após 4 s, com GPU do Godot em 0% na amostra. Na última amostra: Godot ~13% de um núcleo e supervisor ~3%, lógica a 10 Hz. A lógica continua em frequência reduzida para detectar acordar/movimento. Amostras de 3 s são curtas; medição longa em uso normal permanece útil.

```bash
cd ~/Games/kk-mascote/mascote
~/.local/opt/godot/godot --headless --path . --script testes/fisica_estados.gd
~/.local/opt/godot/godot --headless --path . --script testes/rig.gd
```

Para repetir ensaios na tela, use `testes/testar.sh --tela` (abre janelas receptoras temporárias; somente monitor 1920×1080, origem 0, escala 1). Sem argumento executa somente importação/validações headless. Requer Python com GTK4/gi, grim, compilador C, wayland-scanner e libwayland-client. Os controles finais precisam de teste humano: clicar em volta/cabeça/pés, arrastar rapidamente, repetir menu, sobrepor/mover/fechar janelas, trocar workspace, tela cheia, SUPER+G e o seletor de janelas que você usa.

Logs da execução normal: `$XDG_RUNTIME_DIR/kk-mascote/{godot.log,runner.log,status.json}`. Não executar a cena diretamente na sessão sem supervisor: a máscara sozinha não resolve o encaminhamento no compositor.

Referências técnicas: [DisplayServer e a região de entrada](https://docs.godotengine.org/en/latest/classes/class_displayserver.html#class-displayserver-method-window-set-mouse-passthrough), [regras de janela](https://wiki.hypr.land/configuring/core/rules/window-rules/), [eventos Lua](https://wiki.hypr.land/configuring/core/advanced-configuration/events/), [dispatchers Lua](https://wiki.hypr.land/configuring/core/dispatchers/).

Reteste desta tarefa: lançador só anuncia sucesso depois de receber a silhueta do PID correto, e pede encerramento ao seu supervisor se a inicialização falhar. Os ensaios de tela agora retornam erro quando alguma verificação falha; resultados anteriores ficam em `evidencias/ensaio-anterior/` e `ensaio-intermediario/`. O diagnóstico `fullscreen-falha.json` conserva a falha da plataforma antiga (fixada, portanto não entrou em fullscreen); o ensaio corrigido declara `pin=false`. `reuso-recursos.json` confirma 111 recursos idênticos às fontes.

## Adicionar e trocar bonecas

Use `./adicionar-boneca.sh '/caminho/do/card.png'` na raiz do projeto. Gera, valida os 40 clipes e captura em Xvnc privado. Recursos e comparações ficam em `bonecas/<nome>/`; [documentação das bonecas](../bonecas/LEIA-ME.md). Chika Haruno, Sawai Hinata (cabelo rosa, presilha e acessório no pulso) e Mizuno Ayaka (cabelo lilás, óculos) foram geradas e inspecionadas.

No clique direito, escolha **Boneca: nome**. A escolha é salva junto com posição e escala em `~/.cache/forja/kk-mascote.json` (versão 2; cache antigo continua aceito; agora versão 3 com modo, moldura e posição do retrato). A troca reconecta os 40 clipes, olhar e piscar sem reiniciar a física/estado. `evidencias/troca-bonecas.json` verifica menu, animação, persistência e preservação de posição/escala com um arquivo temporário, sem mexer no cache do usuário. Os testes headless usuais agora incluem todas as bonecas e a troca.

## Graduação do editor Koikatsu

O sprite aplica a LUT original `bonecas/visual_comum/Lut_Amount.png` depois da iluminação, em sRGB e preservando alfa. O visualizador usa a mesma graduação; shader de cabelo, manifesto e intensidade global são compartilhados. As sombras próprias estão ativadas. Chika, Hinata e Ayaka tiveram as cores corrigidas sem constantes por pessoa; face/olhos/pose e iluminação integral do Unity continuam com diferenças.

Prova visual da cena real, sem abrir nada na sessão ou tocar no cache salvo: `~/Games/samabake-mascote/.venv/bin/python personagem/provar_cor_apps.py` a partir da raiz. Vulkan e OpenGL passaram, com diferença máxima de ΔE76 1,126 na franja em relação ao visualizador. [Medições e auditoria](../bonecas/LEIA-ME.md) e `bonecas/provas_cor_apps/validacao.json` registram os resultados.

## Retrato / busto e ampliação nítida — 2026-10-08

Clique direito → **Modo retrato**; volte com **Modo passeio**. Para iniciar diretamente: `./mascote/iniciar.sh --retrato`. O lançador conserva o comportamento liga/desliga: executá-lo com uma instância já ligada a encerra. A instância antiga que estava na sessão durante esta implementação foi preservada; as novidades entram no próximo lançamento.

O retrato enquadra cabeça e ombros da boneca ativa no canto inferior direito, com 24 px de margem e respeitando a reserva inferior da barra. Sua posição é independente da posição do passeio. Arraste qualquer ponto do quadrado do retrato; solte sem queda. Fora desse quadrado o desktop recebe o mouse, exceto o menu aberto. **Moldura: ligada/desligada** alterna a linha âmbar de 2 px; não adiciona fundo opaco. A moldura começa ligada.

Respiração, piscar, cabeça e olhos continuam ativos. Gestos cotidianos e sorriso aparecem periodicamente; clique produz sorriso e gesto de alegria. Depois de três minutos ociosa, fecha os olhos mantendo o busto; movimento próximo acorda. Sono manual exige cutucar ou menu. A câmera acompanha a altura da cabeça durante os gestos. A ocultação por fullscreen/modo jogo usa a mesma ponte do passeio.

**B** percorre as bonecas nos dois modos. No desktop, funciona com o cursor sobre a região do mascote/menu: o supervisor registra um bind temporário não consumidor, encaminha somente quando a ponte permite entrada e remove o próprio bind ao encerrar/recarregar. Não rouba foco nem edita a configuração; a tecla também continua chegando ao aplicativo focado. Na cena isolada, o Godot recebe B diretamente. O menu continua sendo a alternativa para troca sem teclado.

O render acompanha o tamanho exibido e a escala do monitor: resolução em múltiplos de 64 px, entre 256 e 1536², aplicada **250 ms depois da última mudança de tamanho**. A posição, enquadramento e área de pegar usam coordenadas lógicas de 448², sem depender da resolução real. A silhueta do passeio é amostrada nessa resolução lógica para evitar aumentar o custo do casco; conserva a folga de 16 px e a parada quando o mouse se aproxima. Em 1920×1080, zoom 2,5 renderiza 1152² em vez de ampliar 448²; zoom 3 permite uma boneca quase da altura da tela. No retrato, o quadrado inteiro precisa caber na tela, portanto o máximo pode ser menor.

Cache versão 3 em `~/.cache/forja/kk-mascote.json`: boneca, escala, posição do passeio, `modo`, `moldura`, `posicao_retrato`. O supervisor também preserva esses campos ao encerrar; antes sobrescrevia o cache com versão 1 e perdia a escolha de boneca.

Provas repetíveis sem janelas na sessão:

```bash
python3 mascote/testes/provar_retrato.py  # a partir da raiz
bash mascote/testes/testar.sh            # regressões headless
```

O primeiro comando cria Xvnc privado, executa a cena com cache de prova próprio, encerra apenas seus filhos e apaga temporários. Capturas RGBA em `evidencias/retrato-zoom/`: `retrato-moldura.png`, `retrato-sem-moldura.png`, `retrato-hinata.png`, `passeio-zoom-2_5.png` e `passeio-zoom-2_5-antes.png`. Todas abertas e inspecionadas. O antes reproduz o render fixo antigo no mesmo clipe/instante/zoom; a diferença de nitidez é visível no cabelo, rosto e contornos. O preto no visualizador de PNG corresponde ao alfa transparente.

`validacao.json` registra arrasto/clique, persistência, sono/acordar, B nos dois modos, resolução após parar a rodinha (inclusive dormindo) e ocultação/restauração por dados de fullscreen/modo jogo. Os eventos de entrada são aplicados à cena pelo script; não houve ensaio de cliques reais no compositor do usuário nesta tarefa. Lua completa do supervisor (incluindo bind B e `no_warps`) passou em `Hyprland --verify-config` com arquivo temporário, log `verificar-lua.log`. O encaminhamento físico de B e clique na sessão ainda pede uso humano; as limitações anteriores da ponte, Alt-Tab e SUPER+G permanecem documentadas acima.

## Posicionar com o mouse — 2026-10-08

Segure o botão esquerdo sobre o mascote e arraste. A área de pegar cobre o retângulo da personagem com margem de 24 px; ela suspende o movimento assim que o botão é pressionado. Durante a captura, a máscara X11 abrange a janela inteira, e a ponte mantém a entrada até soltar. Ao soltar no modo passeio, fica fixada no ponto escolhido, sem gravidade ou caminhada; respiração, olhar, piscar e gestos continuam. A posição e a fixação são salvas (cache versão 4, compatível com versões anteriores). Clique direito → **Soltar e passear** restaura a gravidade e o passeio; **Fixar aqui** também está disponível. No retrato, o arrasto mantém o comportamento existente.

`testes/arrasto.gd` verifica captura, deslocamento, permanência, persistência e retorno à gravidade, com cache privado. Incluído em `testes/testar.sh`.

## Roupas e acessórios individuais — 2026-10-08

Clique direito → **Roupas e acessórios** → **Ocultar: peça** ou **Mostrar: peça**. O menu permanece aberto para alterar várias peças; **Restaurar todas as peças** repõe o conjunto e **Voltar** retorna aos controles do mascote. As opções correspondem ao card ativo: blusa, parte de baixo, luvas, meia-calça, meias, sapatos e cada acessório existente. Sutiã e calcinha também podem ser ocultados ou mostrados individualmente. **Ocultar todas as roupas** oculta todas as peças de roupa, mantendo os acessórios na escolha atual. Escolhas independentes por boneca são salvas no cache versão 5, junto com posição, fixação e modo.

`saida/personagem_roupas.glb` complementa o GLB original: conserva os mesmos ossos/materiais e acrescenta variantes de triângulos do corpo para blusa/parte de baixo visíveis ou ocultas, mais a camada interna superior completa quando a blusa está oculta. Apenas uma variante fica visível. `personagem/gerar.sh` agora gera esse recurso também; o modelo original e o visualizador continuam usando a geometria original. Cards sem o recurso complementar não oferecem ocultação das peças externas correspondentes.

Validação: `testes/roupas.gd` (235 verificações nas três bonecas, incluindo visibilidade, restauração de triângulos, troca e persistência); `testes/provar_roupas.py` faz a prova em Xvnc privado e grava as capturas em `evidencias/roupas/`. Capturas vestida/sem blusa/sem roupas inspecionadas, sem falhas visuais observadas. Regressão completa e prova privada do retrato passaram.

## Modo perfil, expressões e fala visual — 2026-10-08

Clique direito → **Modo perfil** amplia somente o rosto dentro da moldura âmbar. O modo retrato conserva o enquadramento de busto; modo passeio conserva o corpo inteiro. No perfil, arrasto, rodinha, troca de boneca, roupas e ocultação por tela cheia continuam disponíveis. Início direto: `./iniciar.sh --perfil`. Moldura começa ligada no perfil e pode ser alternada pelo menu.

Clique direito → **Expressões e fala** oferece **Neutra, Felicidade, Raiva, Tristeza, Medo, Surpresa, Preocupação e Confiança**, além de **Automática**. Cada expressão combina formas originais independentes de olhos, sobrancelhas e boca, com transição suave e piscar. A escolha persiste por boneca ativa na preferência global de expressão; roupas permanecem independentes por boneca. **Falar agora** inicia uma conversa visual de sete segundos; **Fala automática** alterna as conversas periódicas no perfil. O modo automático percorre as expressões; fora do perfil acompanha as reações/gestos.

Fala visual usa os 14 clipes `conversa_00..13` já extraídos do cotidiano e as cinco formas originais de vogais, com sílabas e pausas reconstruídas por código. Não há áudio nem sincronização com voz gravada nesta etapa. Dois gestos adicionais, `stand_ang_00` e `stand_sad_00`, vêm do diálogo cotidiano (`adv/motion/controller/adv/00.unity3d`), totalizando 42 clipes no mascote. Reexportação desses dois: `personagem/../animacoes/expressoes_cotidianas.py`.

Boca: shader agora usa o canal verde de `_DetailMask` para a linha dos lábios, que era ignorado; língua original `o_tang` restaurada nos modelos complementares das três bonecas e cores originais aplicadas. Sem alterações nos arquivos do jogo. `expressoes.gd` controla os grupos faciais sem acumular formas e mantém dentes/língua sincronizados quando há formas correspondentes. Cache v6 conserva perfil, expressão e fala automática, aceitando versões anteriores.

Prova privada: `python3 testes/provar_perfil.py`. Capturas em `evidencias/perfil-facial/`, expressões e quadros de fala inspecionados. Testes headless verificam as três bonecas, vogais, língua, fala/repouso, perfil/moldura, troca de modos, persistência e ciclo automático. Regressão completa e prova do retrato passaram.

Correção do repouso facial: todas as expressões usam formas fechadas da boca quando não há fala (felicidade usa sorriso fechado). Abertura das vogais só ocorre enquanto o temporizador de fala está ativo. Reação no retrato acompanha o clipe efetivamente exibido, evitando mostrar medo durante o gesto de alegria. O teste facial verifica fechamento em todas as oito expressões nas três bonecas.

## Olhos e cabeça acompanhando o mouse — 2026-10-08

O mascote acompanha o cursor em qualquer ponto do monitor enquanto está acordado, nos modos passeio, retrato e perfil. O alvo parte do centro dos olhos projetado na tela, com sentido vertical corrigido. Mudanças de foco de janelas não substituem o cursor. Pupilas (`cf_J_hitomi_tx_L/R`) respondem primeiro; a cabeça segue mais lentamente. As pálpebras continuam controladas pelas expressões e pelo piscar. Dormindo, o acompanhamento é suspenso.

`olhar.gd` usa suavização pelo tempo, limites da cabeça (±0,42 rad horizontal / ±0,20 vertical) e deslocamento das pupilas (±2,5 mm horizontal / ±1,5 mm vertical, com até 1,2 mm de folga frontal), correção dos eixos do osso pai de cada pupila e remoção da correção anterior para evitar acumulação e preservar animações. Prova: `python3 testes/provar_olhar.py`, Xvnc privado; cinco capturas em `evidencias/olhar-mouse/`, inspecionadas. Teste `olhar_mouse.gd`: 96 verificações nas três bonecas, quatro direções, retorno ao centro, limites por 600 passos, três modos e suspensão no sono. Regressão completa passou.

Correção do recorte das pupilas: a íris é uma camada curva sobre o branco do olho. O acompanhamento agora desloca essa camada em vez de girá-la, preservando sua rotação e acrescentando folga frontal proporcional ao movimento. O teste confere também que a rotação original das duas pupilas permanece intacta.

## Piscar com formas originais — 2026-10-08

O fechamento usa as formas `eye_*_op`/`eye_*_cl` originais do Koikatsu na face e nos cílios. A emoção é suavizada antes de compor o piscar; o fechamento não passa pelo filtro das expressões, que antes impedia a pálpebra de atingir o peso máximo. Temporização procedural: 65 ms para fechar, 35 ms fechado e 130 ms para reabrir, com curvas suaves e intervalo aleatório de 2,5 a 6 segundos. Essa temporização é do mascote, não foi extraída dos clipes do jogo.

O morph sintético que recuava a íris 7 cm está desativado: ele apagava as pupilas durante o fechamento parcial. Face e cílios cobrem o olho pela geometria; somente no fechamento total as malhas de íris/esclera são ocultadas para impedir pequenas frestas nas poses extremas de acompanhamento do mouse. Reaparecem imediatamente ao reabrir. Sono mantém fechamento completo.

`testes/piscar.gd` verifica formas originais, pulso completo a 30/60 FPS, retorno aberto e ausência de recuo/ocultação antecipada em todas as oito expressões e três bonecas. `python3 testes/provar_piscar.py` gera capturas privadas de cinco níveis de fechamento, incluindo olhar diagonal, em `evidencias/piscar/`.

## Corpo, mãos, física e toque — 2026-10-08

As animações corporais continuam usando os 42 clipes cotidianos originais do Koikatsu. `animacoes_corpo.gd` conserva as fontes e aplica os deltas de posição/rotação/escala ao repouso de cada boneca, preservando suas proporções. Pistas ausentes em um clipe recebem o repouso correspondente, impedindo herança acidental do clipe anterior. A biblioteca é reconstruída a cada troca de personagem, sem reaplicar offsets sobre dados já adaptados. Transições mantêm mistura de 350 ms.

`movimento_secundario.gd` acrescenta pequenas variações nos punhos e dedos durante idle/conversa, reduzidas quando a flexão original indica mão fechada. As poses de gestos permanecem originais. Cabelo, saia e ossos de movimento secundário do corpo recebem molas amortecidas, excitadas pela aceleração da animação e por arrasto/toque. Integração em passos de até 1/120 s, limites angulares, nenhuma alteração de comprimento/escala. Dormindo, retornam ao repouso. É uma adaptação leve para Godot, não a reprodução integral do DynamicBone/colisões do Unity.

Clique direito → **Interações e física**:

- **Pegar e mover**: mantém o arrasto habitual.
- **Acariciar**: segure o botão esquerdo e mova sobre cabeça, mãos ou corpo. Reação corporal original, sorriso automático e indicação da região tocada.
- **Apalpar**: toque com pressão suave sobre os ossos da região, com reação corporal/facial.
- **Física secundária** e **Mãos suaves** podem ser desligadas separadamente.

**Shift + arrastar** pega a personagem em qualquer modo de interação. O toque usa cápsulas projetadas dos ossos, acompanhando a pose, tamanho e câmera; não desloca a posição da personagem. Soltar encerra a pressão. O menu marca o modo selecionado; preferências persistem no cache versão 7.

`testes/corpo_interacoes.gd` verifica dedos originais, repouso por personagem, cobertura das pistas, movimento leve das mãos, estabilidade e retorno das molas, toque sem arrasto, pressão, Shift e persistência nas três bonecas. `python3 testes/provar_corpo.py` registra corpo inteiro, mãos e gestos em Xvnc privado, em `evidencias/corpo-interacoes/`.

## Repouso das mãos e iluminação da pele — revisão após captura do usuário

A pose original `idle_em_pe` mantém os dedos abertos e os punhos desviados para fora. As pequenas oscilações anteriores não mudavam esse formato. Com **Mãos suaves** ligado, o repouso em pé agora mistura poses de dedos dos clipes originais `conversa_03` e `sentada_idle`, incluindo a primeira falange e o polegar, e aproxima o punho de seu alinhamento de repouso com o antebraço. A mistura varia lentamente, com transição amortecida e limites de 0,45 rad nos dedos e 0,38 rad no punho. Gestos, caminhada e conversas conservam suas poses originais; desligar a opção restaura o clipe. Não é uma alegação de que essa nova pose seja a pose exata do jogo.

A investigação visual separou relevo, reflexo e sombras: as grandes faixas claras na pele apareciam com as sombras do renderizador, mesmo sem reflexo especular. O novo material `kk_pele.gdshader`, usado apenas no corpo/face, mantém texturas, rampas e normal maps, mas não recebe essas autossombras. Usa preenchimento e reflexo mais suaves; cabelo e roupas continuam com os shaders e sombras anteriores. Por isso, sombras projetadas de cabelo/roupas também não escurecem diretamente a pele nesse material.

Provas: `maos_repouso.gd` confere dedos/polegares/punhos, limites, comprimentos, retorno ao clipe e punhos de gesto preservados nas três bonecas. `provar_maos_luz.py` compara o shader anterior e o novo na mesma pose e captura mãos em detalhe; `evidencias/maos-luz-comparacao.json` registra as medições de contraste no abdômen.

## Balão de texto para agentes

A ponte local está documentada em [PONTE-FALA.md](../PONTE-FALA.md). `falar.py --autor Codex|Claude --emocao Tristeza "texto"` publica uma mensagem em fila atômica. `fala_texto.gd` controla texto progressivo, vogais/pausas e paginação; `balao.gd` exibe autor e texto sem capturar cliques. A emoção da mensagem prevalece durante sua exibição, com posturas originais para tristeza/raiva, e a preferência anterior é restaurada. Sem áudio e sem chamadas a APIs de IA. Codex/Claude Code usam o mesmo cliente, identificando o autor real.

Testes: 49 verificações Python, incluindo 30 envios concorrentes, e 259 verificações Godot nas três personagens (fila, emoção, visemas, pausas, retorno, interrupção, paginação e limites de tela). Capturas privadas dos dois canais em `evidencias/fala-balao/`; autores de teste explicitamente rotulados.

## Voz das respostas

A ponte de mensagens agora fala com voz feminina em português brasileiro e sincroniza balão e boca com o áudio. Envie usando `python3 mascote/falar.py --autor Codex --emocao Felicidade "Olá!"` a partir da raiz. Use `--sem-voz` para enviar só texto. A geração usa o serviço online Microsoft Edge; o texto é enviado ao sintetizador. Clique interrompe voz e fala; ocultar em tela cheia pausa ambas. Detalhes e protocolo em `../PONTE-FALA.md`.

## Gestos e expressões adicionais

A mascote agora carrega 54 clipes. Clique direito → **Gestos** permite escolher variações originais de conversa, alegria, timidez, surpresa, raiva e tristeza. O menu **Expressões e fala** inclui Timidez, Pensativa, Seriedade e Tédio, combinando formas originais do rosto. As mensagens dos agentes alternam os gestos conforme a emoção; `falar.py --gesto` permite selecionar um clipe. Protocolo em `../PONTE-FALA.md`.

## Eventos e controle facial fino

A ponte agora registra regiões de contato, inclusive regiões íntimas, clique/arrasto e interrupções de fala. O agente consulta `eventos.py`; não há ativação automática de uma conversa ociosa. A fala permite intensidade e combinação independente de olhos, sobrancelhas e boca. Exemplos, protocolo e limites estão em `../PONTE-FALA.md`, seção Eventos de interação e expressão fina.

## Atuação mais variada

Menu Expressões e fala → Mais expressões oferece oito perfis adicionais, total 20. Interações e física → Atuação natural controla as reações locais e complementos da fala. A ponte aceita misturas de formas faciais e cenas por trecho de texto, com gestos, movimentos suaves de cabeça e olhar breve. Exemplos/protocolo/limites em `../PONTE-FALA.md`, Atuação avançada. Prévias das três personagens em `evidencias/interacao-avancada/`.

## Atuação por mensagens

Chika pode encenar leitura, reação ao tom, digitação no celular e resposta com expressão/gestos por trecho. Menu **Atuação por mensagens** liga/desliga o modo, os sons e oferece prévias locais. Espirais de confusão e efeitos de surpresa/alegria/ideia são breves; interjeições sintetizadas e teclas ficam em volume baixo. O tom é escolhido pelo agente, sem leitura automática de chats. Guia de uso por Codex e Claude: [PONTE-FALA.md](../PONTE-FALA.md). Pesquisa e provas: [modo-mensagens](evidencias/modo-mensagens/).

## Conversa caricata de anime — 2026-10-09

Agora são 73 animações corporais e 28 perfis faciais. Clique direito → Interações e física → Estilo anime liga/desliga os rostos exagerados e sinais cômicos; o novo campo conserva demais preferências. Expressões e fala tem páginas para manter todas as opções acessíveis, e Gestos inclui Conversas extras, Cotidiano, Locomoção e Comemoração.

A ponte aceita `--roteiro explicacao|comedia|agradecimento|animada` e cenas com deslocamento/enquadramento temporários. Uma explicação pode mostrar o corpo, caminhar, parar para gesticular e voltar ao busto sem alterar sua posição salva. Veja `../PONTE-FALA.md`. Ensaio na instância ativa: `python3 testes/demo_anime.py`. Clique cancela normalmente.

Provas privadas e relatórios: `evidencias/anime-2026-10-09/`. Objetos para algumas poses sentadas e alinhamento fonético da voz continuam pendentes.

## Física dos cards — 2026-10-09

As quatro bonecas também têm casual (5) e pijama (6). Em **Roupas e acessórios**, **Roupa**
permite seleção manual ou automática: pijama das 22h às 07h, casual de dia aos sábados e domingos,
uniforme de dia nos dias úteis. A troca espera uma parada livre e conserva posição, escala,
modo e peças ocultas por boneca. O cache v12 adiciona somente `roupa_modo`, com migração automática.
Veja [hana/LEIA-ME.md](hana/LEIA-ME.md) e [../personagem/LEIA-ME.md](../personagem/LEIA-ME.md).

Cabelo, roupa e cadeias corporais agora usam parâmetros e partículas recuperados do Koikatsu, com ajustes próprios de cada card e colisores das roupas vinculados pelo fluxo original do carregador. A opção Física conserva seu funcionamento; ocultação pausa também a simulação. A mesma implementação está no visualizador. Veja [FISICA-KK.md](../FISICA-KK.md) para validação, origem e limites, incluindo os mods ainda não incorporados.
