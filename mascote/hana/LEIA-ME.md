# Companheira Hana — núcleo e vida própria

Roupas: no menu **Roupas e acessórios**, escolha **Roupa: Automática / Uniforme / Casual / Pijama**.
`roupa_modo` é persistido (cache v12; padrão `automatica`). Automática usa relógio local:
22h–07h pijama, fim de semana de dia casual, dia útil de dia uniforme. A troca aguarda parada,
sem fala, celular, gesto, arrasto, toque ou menu aberto; reaparece em 180 ms. Mantém posição,
escala, enquadramento e ocultação por tipo de peça de cada boneca. Se a coordenada não foi
exportada, continua com o uniforme. `status.json.roupa` e `desktop.roupa` no pedido ao modelo
informam nome e coordenada efetivos, inclusive enquanto uma troca está aguardando. A coordenada
temporária não é salva como preferência. Provas e testes em `evidencias/hana-etapa3/`.

O supervisor inicia `cerebro.py` junto com o mascote e o encerra ao fechar. Quedas do cérebro têm
reinício com backoff de 1 a 60 s; o log fica em `runtime/hana.log`. Ensaios `--prova` não iniciam Hana.
Menu **Atuação por mensagens → Hana responde sozinha** controla `hana_auto`, ligada por padrão.
Desligar mantém pedidos pendentes e pausa respostas novas. Não muda a boneca, o arrasto ou o foco.

A Hana usa o Claude Code instalado/autenticado, modelo `claude-haiku-4-5-20251001`, sem ferramentas,
MCP configurado ou sessão persistente. O subprocesso roda no diretório de dados, fora do repositório;
timeout de 60 s e uma repetição. Falhas usam “aff, travei. manda de novo” e ficam no log.
`PERSONA.md` é lida em cada chamada; emoções, tons, gestos e roteiros vêm dos catálogos locais.
IDs para concluir/remover tarefas são limitados pelo schema aos existentes na memória e conferidos
novamente em Python. Campos inválidos são descartados.

Com Modo mensagens ligado, respostas passam pela mesma escrita no celular e pelas vozes curtas do jogo.
Fora dele, usam balão e a opção de voz sintética existente. A leitura já iniciada pelo chat é continuada;
durante chamadas lentas, o pensamento é renovado. Recibos confirmam entrega, e clique interrompido
nunca reenvia a resposta. Um ID estável impede duplicação do histórico.

## Dados e comandos

Memória: `~/.local/share/kk-mascote/hana/memoria.json`, versão 1, com transações protegidas por `flock`
e gravação atômica. `pendencia.json` preserva o lote/resposta em curso; `cerebro.lock` impede dois daemons.
`MASCOTE_HANA_DIR` permite outro diretório, sempre fora do repositório. O chat mantém pedidos ainda
sem resposta em `.pendentes-hana/`, separadamente do limite visual de 300 mensagens.

Na raiz do projeto:

```bash
python3 mascote/hana/memoria.py --listar
python3 mascote/hana/memoria.py --tarefa "Lavar a louça amanhã"
python3 mascote/hana/memoria.py --tarefa "Estudar" --data 2026-10-12
python3 mascote/hana/memoria.py --concluir ID
python3 mascote/hana/memoria.py --esquecer ID
```

Sem data, uma tarefa é para hoje; “amanhã” no texto muda para amanhã. Pendências antigas continuam
atrasadas. Até 60 fatos deduplicados; resumo de até 1500 caracteres. Mais de 30 mensagens novas
disparam uma chamada separada de resumo em segundo plano, sem persona.

## Rotina e contexto

Os horários e intervalos ficam no topo de `rotina.py`: dia às 05:00, noite entre 21:00 e 02:00,
cobranças a cada 40–70 minutos, intervalo global de 15 minutos. Bom dia sai uma vez por dia; retorno
após mais de três horas sem entrada observada usa o motivo `volta`. Ambos recebem reverência original
antes de começar a escrever (ou como gesto no balão). Teclado/mouse vêm da ponte existente,
sem guardar teclas. Sem entrada confiável, só o login dá bom dia; cobrança/noite exigem atividade.
Tela cheia e modo jogo adiam toda proatividade. Estado, contagens e horários sobrevivem a reinícios.

`desktop.py` consulta janela ativa, música e bateria com tolerância a ausência e timeout de 0,7 s.
Ignora mascote/chat. A tabela editável `categorias_janela.json` classifica jogos, música, navegador,
código e vídeo por classe e, em alguns casos, título. Publica `runtime/contexto.json` a cada 5 s,
mesmo com as respostas automáticas desligadas. Godot descarta contexto sem atualização há 15 s.
Jogos em janela usam `sentada_idle`, olhando para a janela; música sentada usa `sentada_musica`.
Em pé, o balanço discreto da cabeça é procedural, a 100 BPM ou pelo metadado MPRIS disponível.
Comentários só seguem transições que duram mais de 2 min, no máximo um a cada 30 min,
compartilhando a trava geral de 15 min. Títulos e música entram no contexto autorizado do modelo.

## Gatilhos da etapa 2

```bash
python3 mascote/hana/avisar.py "A compilação terminou com sucesso."
python3 mascote/hana/instalar_hook.py
```

O primeiro comando só publica um evento local; não liga o mascote nem chama modelos. Avisos ficam
em `eventos/` no diretório de dados até o cérebro persistir a fila. Fila limitada a 64; avisos/downloads
expiram em 1 h e crashes em 30 min. Bateria, categoria, música e assinatura do download são rechecadas
antes de falar. Tela cheia/modo jogo acumulam eventos; observações vencidas ou irrelevantes são descartadas.
Todas as mensagens de evento também exigem atividade recente do usuário.

O instalador acrescenta uma única linha `source ~/Games/kk-mascote/mascote/hana/shell-hook.bash`
no `~/.bashrc`, preservando `~/.bashrc.antes-hana`. Novos bash interativos avisam quando um comando
dura mais de 90 s, com seu nome e código de saída; argumentos não entram no aviso. String/array de
PROMPT_COMMAND e trap DEBUG anterior são mantidos. Bash não interativo não instala o hook.
Downloads usa polling (arquivos estáveis por mais de 3 s, ignorando temporários e arquivos já existentes).
Crashes combinam journalctl opcional, sem bloqueio, com processos conhecidos em /proc que viram zumbis
com sinal. Sem journal disponível, um processo que desapareça entre duas consultas pode não ser detectado.
Bateria baixa exige ≤15% descarregando; cheia exige transição Charging → Full/Not charging a 100%.

## Gestos, madrugada e consumo

`animacoes/extrair_gestos_hana.py` usa o mesmo pipeline dos idles, somente action/animator/00.unity3d.
Cinco gestos originais nas duas aplicações, em Cotidiano. Quatro são sorteados na parada a cada
40–120 s de parada disponível, sem repetir o anterior; reverência fica reservada ao cumprimento.
O celular continua com prioridade durante leitura/escrita. As pausas/poses em pé são as originais.

Na madrugada (00h–05h), pálpebras mais pesadas e bocejo ocasional composto com formas faciais existentes.
A busca cotidiana não identificou um bocejo acordado; animações de dormir e falas sobre o sono foram
registradas em `../evidencias/hana-etapa2/busca-bocejo.json`. Nenhuma voz de bocejo foi inventada.

Parada estabilizada usa 20 FPS e modo de menor uso do processador. Interação, mouse sobre ela,
fala/escrita, gestos, música, bocejo, movimento ou energia física acima do limiar restauram o limite
de 60 imediatamente. Física mantém passo fixo 60 Hz e foi verificada a 20/30/60/120 FPS;
silhueta continua amostrada por tempo (10 Hz), com atualização por frame após interação.
Sono/ocultação conservam 10 FPS. Medições de 30 s em Xvnc/Intel: parada 24,94% → 21,17% de CPU;
fala 26,75% → 52,47%, pois o limite sobe de 30 para 60. Os resultados variam com GPU/escala;
a execução NVIDIA em Xvnc ficou limitada pela renderização e não mostrou redução.

## Testes e limites

```bash
python3 mascote/testes/hana_python.py
python3 mascote/testes/hana_etapa2_python.py
bash mascote/testes/testar.sh
```

Testes usam exclusivamente um executável Claude falso, diretórios temporários e Godot headless.
Cobrem falha, timeout/cancelamento, memória concorrente/atômica, datas, rotina, fila durável, reinício,
leitura única, histórico, interrupções e preferências. Evidências em `../evidencias/hana-nucleo/`.

Mensagens próximas são agrupadas por 0,8 s, até 2 s antes da chamada; as que chegam durante uma
chamada já iniciada ficam para a próxima resposta. Não há respostas com o mascote fechado.
Interpretação de texto e extração de fatos dependem do modelo; operações inválidas não alteram tarefas.
O ensaio real limitado a duas chamadas validou o formato e revelou um ID por texto, que motivou o
schema dinâmico e sua regressão automática. Não houve ensaio de janelas reais nesta entrega.
Etapa 2: `testes/hana_etapa2.gd` valida os cinco gestos nos quatro rigs, horários/bocejo,
assistindo/música, reverência antes do celular, interrupção, política de FPS e preferências.
`testes/previa_hana.py` gera a prancha Xvnc dos cinco gestos e de assistir (Python do pipeline com Pillow).
Evidências, medição reproduzível (`testes/consumo_hana.py`) e registros em `../evidencias/hana-etapa2/`.
