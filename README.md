# kk-mascote — Koikatsu characters, alive on your desktop

> **Why this exists:** Koikatsu Party has a great character editor, but the characters you make
> only live inside the game. This project takes them **out of the game and onto the Linux desktop**:
> the same card, the same body, clothes, hair, faces, animations and voices, rendered in real time
> by Godot as a desktop mascot that walks on your windows, reacts to you and can hold a conversation.
>
> The rule from day one: **use what the game itself has** (its meshes, shaders, animation clips,
> physics settings and voice lines), reproduced faithfully, instead of substitutes made up by the project.

![Four characters animated in real time](docs/media/animations.gif)

---

## Contents

- [What it does](#what-it-does)
- [How it works](#how-it-works)
- [Design choices](#design-choices)
- [Body import (UncensorSelector)](#body-import-uncensorselector)
- [Hana, the optional brain](#hana-the-optional-brain)
- [Requirements](#requirements)
- [Setup and usage](#setup-and-usage)
- [Configuration](#configuration)
- [Tests](#tests)
- [Project layout](#project-layout)
- [Known limitations](#known-limitations)
- [Legal](#legal)

---

## What it does

**One command per character.** Point it at a Koikatsu card PNG and it extracts everything:

```bash
./adicionar-boneca.sh ~/path/to/Koikatsu_F_card.png
```

That reads the card, resolves every part against your local game install (and its mods), and builds
Godot-ready GLBs for three outfits: school uniform, casual and pajamas. It also prepares the voice
lines for the character's personality and renders a private proof image.

| | |
|---|---|
| **Multiple characters** | Switch between any imported character from the menu. |
| **Outfits by context** | Uniform / casual / pajamas chosen by time of day and weekday, or fixed from the menu. Each clothing piece can be hidden individually. |
| **Faithful look** | Koikatsu's toon shading reimplemented from the game's shader bytecode: ramp lighting, color masks, hair gloss, skin detail, card overlays (blush, areolae, body hair, makeup). |
| **Original animations** | Idle poses, gestures, reactions, walking, sitting and sleeping, decoded from the game's Humanoid muscle clips. |
| **Facial acting** | 28 expression profiles built from the game's own blend shapes, plus optional anime-style effects (hearts, sweat drops, anger marks, tears). |
| **Physics** | A port of Koikatsu's DynamicBone and DynamicBone_Ver02 (hair, skirts, bust, mod bones) using the original per-asset parameters. |
| **Procedural body correction** | A transpiled port of the game's `ExpressionBone` system (shoulders, elbows, wrists, knees) so poses deform the way they do in Unity. |
| **Desktop life** | Stands and walks on top of windows, jumps between them, falls when a window closes, hides in fullscreen and game mode, follows the mouse with eyes and head, can be dragged, poked and resized with the wheel. |
| **Voice** | Short original voice lines from the character's personality (surprise, doubt, laughter, sighs…), lip-synced from the audio envelope. |
| **Chat** | A chat window next to her: she "reads", reacts, thinks and *types* her answer on her in-game phone. |
| **Companion (optional)** | Hana, a persona with memory, tasks and reminders, driven by Claude or by a local model. |

![Twelve expressions with anime effects](docs/media/expressions.png)

<details>
<summary><b>All four characters × three outfits</b> (click to expand)</summary>

![Outfits](docs/media/outfits.png)

</details>

![Hair and skirt physics during a celebration](docs/media/celebrate.gif)

---

## How it works

```
 Koikatsu install (read-only)           personagem/  (Python + Blender)              mascote/  (Godot 4)
 ─────────────────────────────          ───────────────────────────────              ────────────────────
 card PNG  ──► ler_card.py   ──► resolver.py ──► extrair.py ──► montar_blender.py ──► GLB + materials JSON
 abdata/*.unity3d (UnityPy)        (parts, mods)   (meshes,      (skinning, morphs,      │
 mods/*.zipmod                                      textures,     UV sets, bone           ▼
 Assembly-CSharp.dll (IL) ──► physics / ExpressionBone audits     implants)        mascote.gd + shaders
                                                                                   physics, faces, behaviour
 abdata/action, sound/…   ──► animacoes/extrair.py (muscle clips → GLB)  ───────────────►  animation library
                         ──► mascote/vozes/preparar.py (voices → OGG + lip-sync)  ─────►  reaction sounds
```

1. **Read the card.** `ler_card.py` parses the PNG trailer: body/face sliders, outfit coordinates, colors,
   and the ExtendedSave plugin data that mods store.
2. **Resolve.** `resolver.py` maps each card ID to the exact asset bundle and prefab, including
   zipmod content and the body chosen by UncensorSelector.
3. **Extract.** `extrair.py` and `geometria.py` read the Unity bundles with UnityPy: meshes, sub-meshes, bone
   hierarchy, skin weights, blend shapes (with normals), tangents and every UV set the shaders sample.
4. **Assemble.** `montar_blender.py` runs headless Blender and writes glTF with card proportions applied as
   bone scales (`proporcoes.py` evaluates the game's own shape animation curves).
5. **Audit and validate.** Physics, ExpressionBone and coordinate-type data are read straight from the
   game's IL (Intermediate Language, the compiled .NET code) and checked by hash. `validar_corpo.py`
   verifies binds, weights, morphs and coverage before anything is published.
6. **Render and live.** Godot loads the GLBs, applies the reconstructed KK materials, and runs the
   physics, face, gaze, state machine and desktop logic.

---

## Design choices

**Godot 4 + XWayland, not a Unity mod.** The mascot runs outside the game, with no runtime dependency on it.
It uses the OpenGL compatibility renderer on the integrated GPU, so it stays light (about 40% of one core
while idle, nearly 0% asleep). Click-through uses the alpha outline of the rendered character, so
clicks on transparent pixels reach the window underneath.

**Read the game's code instead of guessing.** Wherever the visual result depends on Koikatsu logic,
the project reads the original: shader DXBC for skin and hair, IL for DynamicBone and ExpressionBone,
the `CoordinateType` enum for outfit slots. The ExpressionBone formulas are even *transpiled* from IL to
GDScript, then checked against an independent Python IL interpreter (max error ≈ 3e-7 m).

**Fail loudly over substituting silently.** Unknown bundles, unexpected plugin data, an unaudited DLL
hash or a mod layer that is not supported yet all stop the pipeline with a precise error. The pipeline
never quietly falls back to a "close enough" asset.

**Original assets first.** Idle poses are the game's `f_tachi_*` clips, not procedural fixes. Reaction
sounds are the personality's own voice lines, not TTS. The phone in the typing animation is the game's
phone model.

**Game files are read-only.** Nothing is written into the Koikatsu install. Extraction outputs live
in `bonecas/` (git-ignored) and are rebuilt per machine.

**Private proofs.** Visual checks render in a private Xvnc display, so tests never open windows or
move the mouse on your real desktop.

**AI is optional.** Everything except Hana's conversation runs without any AI. Hana can use Claude
or a local model through Ollama, chosen from the menu.

---

## Body import (UncensorSelector)

Many Koikatsu installs replace the stock body with mods managed by
[KK_UncensorSelector](https://github.com/IllusionMods/KK_Plugins). The importer reproduces what the
plugin does at runtime, so the exported body is the one the game would actually show.

**Selection** (`personagem/mods_corpo.py`)
- Inventories every local `.zipmod`, reading the `KK_UncensorSelector/body` and `migration` entries of each manifest.
- Picks the body in plugin order: the card's ExtendedSave `BodyGUID` first, with migration of v1 data.
  Otherwise it uses the plugin's `Default Female Body` setting from the BepInEx config.
- Unsupported cases stop with an explicit error: male bodies, penis or balls display, overlay and
  underlay textures, `colorMatch` layers, an unknown plugin data version.

**Geometry** (`geometria.py`, `regras_malhas.py`)
- Bundles inside zipmods are loaded straight from the archive. Their external CAB dependencies are resolved against both the game and the mods.
- The material is the stock `cf_m_body` built by `InitBaseCustomTextureBody`, as the plugin does. The mod prefab leaves that slot empty on purpose.
- Each skipped helper mesh has a documented reason, instead of a blanket skip list:
  - `o_mnpa`/`o_mnpb`: mosaic helpers, recognized by their `mnpb` shader;
  - `o_dankon`: hidden while `DisplayPenis=false`;
  - `o_gomu`: hidden while `visibleGomu=false`;
  - `o_shadowcaster`: Unity-only shadow proxy.

  Every decision is written to `saida/geometria_origem.json`, with weights per region.
- **Bone implants:** `BoneImplantProcess` components re-parent mod bones into the base skeleton
  (`SetParent(dst, false)`, keeping local TRS). They are applied at assembly time.
- Blend-shape normals use the inverse-transpose basis. Original tangents are preserved.

**Materials**
- The body-hair overlay (`_overtex2`) follows the `main_skin` DXBC: the third UV set, multiplied by vertex color B, then the texture's ST transform.
  The exporter writes `TEXCOORD_2/3`, which Godot reads as `CUSTOM0`.

**Physics**
- The mod prefab's serialized DynamicBones (12 chains) join the physics set. They use their original parameters and colliders.

**Clothing interaction**
- The body ships with the same mask variants as the stock body, so hiding the top or bottom swaps in the right variant.
  This avoids both holes and overlapping surfaces.

Not reproduced: plugin behaviour that only runs during H scenes (e.g. BetterPenetration's dynamic
deformation), and DynamicBoneEditor/Pushup overrides. No sexual animations are included. The import is
about geometry fidelity only.

---

## Hana, the optional brain

`mascote/hana/` is a small daemon that lets the character talk on her own:
- persona text in `PERSONA.md`;
- memory of facts and tasks with dates, kept outside the repo;
- morning greetings, reminders, evening check-ins;
- light awareness of desktop events: window changes, music, battery, downloads.

Every reply is constrained to a JSON schema: the text, plus a tone, an emotion, a gesture and memory edits.
It is validated before reaching the screen.

| Backend | Menu entry | Needs |
|---|---|---|
| Claude (default) | *Cérebro da Hana: Claude* | Claude Code CLI logged in (`claude -p`, Haiku) |
| Local | *Cérebro da Hana: local (Ollama)* | Ollama running with a model; GPU build recommended |

If the local server is down, she says so in the chat instead of hanging. Hana can also be switched off
entirely ("Hana responde sozinha"), and an agent can speak through the mascot via `mascote/falar.py`.

---

## Requirements

- Linux, tested on Arch with Hyprland, running under XWayland.
- **Koikatsu Party** installed. BepInEx and mods are optional but supported.
- **Python 3** venv with `UnityPy`, `numpy`, `msgpack`, `Pillow`.
- **Blender 5.2** (headless) and **Godot 4.7**.
- `ffmpeg`; `Xvnc` (TigerVNC) for the private visual tests.
- Optional:
  - Claude Code CLI or Ollama, for Hana;
  - an NVIDIA GPU, to speed up the Whisper voice transcription. The Whisper environment is created automatically.

## Setup and usage

```bash
# 1. Point the tools at your install (see Configuration for every variable)
export KK_JOGO="$HOME/Games/Koikatsu Party"
export PYTHON_PERSONAGEM="$HOME/venvs/kk/bin/python"

# 2. First run: animation library, editor color grading and the in-game phone (read-only extraction)
./configurar.sh

# 3. Import characters (repeat per card)
./adicionar-boneca.sh "$KK_JOGO/UserData/chara/female/my_character.png"

# 4. Start / stop the mascot
mascote/iniciar.sh            # start
mascote/iniciar.sh --status
mascote/iniciar.sh --parar    # stop
```

Right-click her for the menu: characters, outfits and pieces, expressions, chat mode, Hana and sounds.
Drag her to move her and use the mouse wheel to resize her.

Regenerate a single outfit: `BONECA_DIR=bonecas/<id> KK_COORDENADA=5 personagem/gerar.sh`
(0 = uniform, 5 = casual, 6 = pajamas).

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `KK_JOGO` | `~/Downloads/Koikatsu.Party/Koikatsu Party` | Koikatsu install root (read-only) |
| `PYTHON_PERSONAGEM` | `~/Games/samabake-mascote/.venv/bin/python` | Python with UnityPy |
| `BLENDER_PERSONAGEM` | `~/.local/opt/blender-5.2.2-linux-x64/blender` | Headless Blender |
| `GODOT`, `GODOT_PERSONAGEM` | `~/.local/opt/godot/…` | Godot binary |
| `KK_SO_UNIFORME=1` / `KK_SEM_VOZES=1` | off | Skip extra outfits / voices in `adicionar-boneca.sh` |
| `KK_WHISPER_VENV` | `~/.local/share/kk-mascote/whisper` | Auto-created transcription env |
| `MASCOTE_HANA_DIR` | `~/.local/share/kk-mascote/hana` | Hana's memory and `config.json` |
| `HANA_OLLAMA_URL` / `HANA_OLLAMA_MODELO` | `http://127.0.0.1:11434` / first installed | Local brain |

Voice categories (`mascote/vozes/categorias_cNN.json`) are generated automatically. You can edit them
by hand if you like; the tools never overwrite an existing file.

## Tests

```bash
mascote/testes/testar.sh
```

It runs about 40 headless suites (over 1.8 million numeric checks). They cover:
- physics convergence and frame-rate independence;
- rig and bone integrity;
- ExpressionBone against an independent IL oracle;
- outfit switching, faces, blinking and gaze;
- chat, Hana and the local-brain backend.

Visual proofs (`mascote/testes/prova_corporal.gd`, `previa_roupas_contexto.py`, `demo_readme.gd`) render in a
private Xvnc display. The README media was produced that way.

## Project layout

```
configurar.sh           first-run extraction of shared assets (animations, color grading, phone)
adicionar-boneca.sh     one-command character import
personagem/             card → GLB pipeline (UnityPy, Blender), audits, validation
animacoes/              animation clip extraction (muscle clips → glTF); selecao.json is the allowlist
mascote/                Godot app: rendering, physics, faces, behaviour, chat, menus
  shaders/              KK toon shaders reimplemented from DXBC
  hana/                 optional conversational companion
  vozes/                voice transcription / classification / extraction
  testes/               headless suites and private visual proofs
visualizador/           standalone Godot viewer sharing the same materials
docs/media/             README images
bonecas/                generated per machine (git-ignored)
```

## Known limitations

- Visual fidelity is close but not identical to Unity's renderer. Some print and overlay compositions and
  the skin's warm rim term are approximations.
- Clicks very close to the animated head occasionally miss. Hyprland still lists the mascot window in
  window switchers.
- Only female cards are supported. Plugin behaviour beyond what is described above is not emulated.
- Built and tested on one machine. Other installs may hit the deliberate "unsupported" errors.

## Legal

This repository contains **only original code and documentation**. It ships no Koikatsu assets
(models, textures, animations, audio or decompiled code). Every user extracts from their own
legally owned copy. Koikatsu is a trademark of ILLUSION / ILLGAMES; this is an unofficial fan project,
not affiliated with or endorsed by them.
