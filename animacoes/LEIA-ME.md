# Animações cotidianas — etapa 1 concluída

Há 61 clipes em `exportados/`, selecionados por `selecao.json`.
`catalogo.json` registra os assets; `exportados/manifesto.json` registra origem, duração,
loop, tamanho, estatísticas de decodificação e medições de raiz.
`esqueleto.json` contém os 580 nós canônicos, em coordenadas Unity originais.

As fontes permitidas pelo extrator são action e os bundles específicos de apoio indicados
no código (`adv/motion/controller/adv/00.unity3d`, `communication/info_00.unity3d`
e `chara/oo_base.unity3d`). Nenhuma etapa acessa `abdata/h/`.
A seleção inclui parada, conversa, gestos/reações, caminhada, sentar e dormir.

## Regerar

```bash
cd ~/Games/kk-mascote
~/Games/samabake-mascote/.venv/bin/python animacoes/extrair.py --reuse-index
```

Remova `--reuse-index` para refazer o catálogo. Use `--index-only` para gerar somente o índice.
O jogo é aberto em leitura; as saídas ficam confinadas a `animacoes/`.
O ambiente Python existente contém `UnityPy` e `numpy`.

`extrair.py` decodifica canais Transform compilados do muscle clip
(streamed, dense e constant), amostra a 30 fps e preserva as transformações locais.
`glb.py` grava glTF destro com Y para cima, espelhando X.
Não há reconstrução por retarget Humanoid. Bindings desconhecidos falham explicitamente;
auxiliares exclusivos do Avatar low são omitidos quando comprovadamente ausentes no rig high.

Os GLBs desta pasta contêm um manequim geométrico para inspeção, não a malha da personagem.
A personagem real está em `../personagem/saida/personagem.glb`.
O esqueleto corporal compartilha os mesmos nomes. No Godot, ao mover animações entre cenas,
ajuste o caminho do nó `Skeleton3D`, mantendo nomes de ossos, tempos e valores das pistas.
A prova de reuso está em `../personagem/saida/reuso_clipe_godot.json`.

## Prévias e validação

`previa/prancha_01..04.jpg` reúne quatro amostras por clipe; essas pranchas foram conferidas.
`previa/validacao_blender.json` registra a reimportação e as posições amostradas.
Para repetir renderizações selecionadas:

```bash
~/.local/opt/blender-5.2.2-linux-x64/blender -b -t 4 \
  -P animacoes/previa_blender.py -- idle_em_pe caminhar
~/Games/samabake-mascote/.venv/bin/python animacoes/pranchas.py
```

A aplicação do idle à personagem foi validada em Blender e Godot.
O visualizador independente em `../visualizador/` permite experimentar nove clipes;
espaço/N troca a animação. Ele foi criado pelo Claude e não foi alterado nesta etapa.

## Root motion das caminhadas

Verificado em 2026-10-08 por `verificar_root_motion.py`, diretamente nos GLBs exportados:

- `caminhar`: `cf_j_root` permanece em `[0, 0, 0]`, amplitude e deslocamento iguais a zero.
- `caminhar_zangada`: mesmo resultado.
- O quadril oscila durante ambos os ciclos, mas retorna à posição inicial;
  a maior diferença entre início e fim é aproximadamente `1,2 × 10⁻⁷` unidades.

As duas caminhadas **já ficam no lugar**. Não foi necessário gerar outra versão.
O código do mascote deve controlar o deslocamento global; não deve remover a oscilação do quadril.
As medidas estão em `root_motion.json` e podem ser repetidas:

```bash
~/Games/samabake-mascote/.venv/bin/python animacoes/verificar_root_motion.py
```

A validação acima diz respeito aos clipes exportados. Não é uma medição da velocidade
que o controlador do próprio jogo aplica à personagem durante a caminhada.

## Variações de diálogo — 2026-10-08

Mais 12 clipes originais integrados: Stand_Joy_02/03/05/08, Stand_Ang_01/02, Stand_Sad_01/02, Stand_Oth_02/04/05/06. Os Oth escolhidos correspondem aos rótulos nativos de timidez (恥) do índice cotidiano. A seleção continua limitada aos bundles autorizados. `expressoes_cotidianas.py` reproduz esta ampliação usando o decoder existente.

Manifesto, seleção e catálogo agora cobrem os 54 GLBs: 12 conversas antigas que faltavam nesses registros foram recuperadas a partir dos metadados originais embutidos nos arquivos. A extração completa usa `extrair.py --reuse-index`; o importador Godot confere e salva a biblioteca portátil com os 54 clipes.

Capturas de todos os 12 novos gestos nas três bonecas e das quatro novas combinações faciais em `../mascote/evidencias/gestos-expressoes/`. Pranchas abertas e inspecionadas; 718 verificações específicas, regressão completa e importação portátil passaram.

## Celular — modo mensagens, 2026-10-08

Sete clipes cotidianos do controlador Phone foram acrescentados à seleção: celular_em_pe, celular_em_pe_transicao, celular_sentada, celular_sentada_transicao, celular_jogando, celular_sentada_2 e celular_sentada_2_transicao. As variantes sentadas usam o tamanho M. As transições são preservadas para inspeção; o modo mensagens usa os movimentos contínuos. O manifesto agora contém 61 clipes. O aparelho usado no Godot é geometria criada para o protótipo, não um objeto extraído do jogo.

## Lote anime cotidiano — 2026-10-09

`extrair_anime.py` extrai um allowlist por `source_id`, sem reindexar nem exportar os outros
clipes. O lote atual contém quatro gestos de fala (`conversa_gesto_*`), duas corridas,
uma postura pensativa, duas comemorações e três posições sentadas de atividades. Os nomes
são conservadores e as poses aguardam inspeção visual. O relatório por fonte, duração,
bindings, métricas de raiz/quadril e SHA-256 está em `evidencias/extrair_anime_resultado.json`;
`evidencias/extrair_anime_baseline.json` preserva os hashes e contagens anteriores.
Com este lote, seleção e manifesto passaram a 73 clipes.

Para repetir exatamente o lote no ambiente existente:

```bash
~/Games/samabake-mascote/.venv/bin/python animacoes/extrair_anime.py
```

O script exige que as fontes continuem no bundle cotidiano permitido, falha para source IDs
ou nomes já exportados, valida todos os bindings (exceto auxiliares low-only identificados),
mede `cf_j_root`, `cf_n_height` quando presente e `cf_j_hips`, e rejeita deslocamento persistente
acima dos limites registrados no relatório. Copia cada GLB novo para `mascote/anims/` e
`visualizador/anims/`; não importa recursos no Godot.
