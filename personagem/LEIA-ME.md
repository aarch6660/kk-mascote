# Pipeline de cards Koikatsu → bonecas Godot

O pipeline agora gera **várias bonecas**, com uma pasta por card. A documentação de uso, estrutura, materiais, limites e provas está em [../bonecas/LEIA-ME.md](../bonecas/LEIA-ME.md).

`KK_COORDENADA=0..6` seleciona a roupa (padrão 0). Para outra coordenada, o pipeline isola card,
peças, proporções, materiais, física e GLBs em `bonecas/<id>/coordenadas/coord_<N>/`, com recursos
em `saida/`. O uniforme em `bonecas/<id>/saida/` permanece intacto. Exemplo:

```bash
BONECA_DIR="$PWD/bonecas/chika-haruno" KK_COORDENADA=5 ./personagem/gerar.sh
BONECA_DIR="$PWD/bonecas/chika-haruno" KK_COORDENADA=6 ./personagem/gerar.sh
```

Ordem confirmada por `auditar_coordenadas.py` na enum `ChaFileDefine.CoordinateType` da DLL local:
School01=0, School02=1, Gym=2, Swim=3, Club=4, Plain=5, Pajamas=6. Fonte, token e SHA256 em
`auditoria_coordenadas.json`. ID 0 nas roupas significa peça ausente. Os GLBs completos são
duplicados por coordenada para manter seu rig/material; PNGs idênticos compartilham inode no
publicador. `KK_PUBLICAR=0` adia importação/deduplicação em lotes; depois execute `catalogo.py`
com `BONECA_DIR` da coordenada, `KK_BONECA_ID` original e `KK_COORDENADA`.

Validação isolada: `validar_corpo.py --pasta bonecas/<id>/coordenadas/coord_<N>` e
`auditar_fisica_kk.py --boneca-dir bonecas/<id>/coordenadas/coord_<N>`. O teste de acessórios
`testar_pipeline.py` também aceita `KK_COORDENADA`, sem alterar o relatório da coordenada 0.

```bash
cd ~/Games/kk-mascote
./adicionar-boneca.sh '/caminho/do/card.png'
```

A Chika foi migrada para `bonecas/chika-haruno/`; os antigos caminhos `personagem/card.png`, `card.json`, `pecas.json`, `proporcoes.json` e `saida/` são links de compatibilidade. O card original está preservado. `./personagem/gerar.sh` continua regenerando a Chika; `BONECA_DIR=/pasta/da/boneca` seleciona outra pasta. O comando principal também valida e roda a prova visual privada.

Scripts: `adicionar.py` coordena a geração, `resolver.py` resolve IDs/acessórios/skinId, `extrair.py` isola slots, `montar_blender.py` aplica TRS e preserva o rig, `preparar_visual.py` produz os materiais KK, `catalogo.py` compartilha recursos e importa nos dois aplicativos, `provar_visual.py` captura e compara no Xvnc.

Verificações repetíveis:

```bash
~/Games/samabake-mascote/.venv/bin/python personagem/testar_pipeline.py
~/.local/opt/godot/godot --headless --path mascote --script testes/bonecas.gd
~/.local/opt/godot/godot --headless --path mascote --script testes/troca_bonecas.gd
~/.local/opt/godot/godot --headless --path visualizador --script testar_troca.gd
./mascote/testes/testar.sh
```

Os testes de troca usam cache temporário, sem alterar a preferência do usuário. Provas reais de imagem ficam em `bonecas/<nome>/saida/comparacao_render.png`. **O visual não é uma portabilidade comprovada do shader Unity**; diferenças e alcance estão documentados no LEIA-ME das bonecas.

## Cor do cabelo e graduação comum — 2026-10-08

Revalidação da implementação existente: três execuções de `provar_visual.py`, nova medição com `medir_cabelo.py depois`, reextração com `extrair_cor_kk.py` e prova dos dois renderers com `provar_cor_apps.py` passaram em 2026-10-08. As comparações regeneradas foram abertas e inspecionadas; os números anteriores foram reproduzidos exatamente. Tudo foi executado em Xvnc privado ou sem janela, e o antes histórico foi preservado.

A cena do editor usa a LUT `Lut_Amount`, que faltava nos aplicativos. A extração comum fica em `extrair_cor_kk.py`, integrada à preparação dos materiais; usa somente `level2`/`sharedassets2.assets` do editor e a configuração do jogo, em leitura. Cores/máscaras, composição DXBC, rampas e sombras foram auditadas. O Godot aplica a LUT após a iluminação, sem calibração por boneca. A intensidade global de sombra ainda é uma reconstrução, explicitamente distinguida do valor passado pelo Unity.

Detalhes e números completos: [documentação das bonecas](../bonecas/LEIA-ME.md), [auditoria](../bonecas/auditoria_cor_kk.json) e [medições antes/depois](../bonecas/medicoes_cabelo.json). `medir_cabelo.py depois` repete a medição com polígonos fixos da franja; `antes` é protegido contra sobrescrita. `provar_cor_apps.py` captura a cena real do mascote em Vulkan e OpenGL, somente no Xvnc privado, compara à prova do visualizador e falha se a diferença exceder ΔE76 3. Evidências em `bonecas/provas_cor_apps/`. Todos os recursos usados em runtime são locais.
