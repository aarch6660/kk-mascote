#!/usr/bin/env python3
"""Validação Python do payload de encenação anime e do envio sem voz."""
import json
import math
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import falar
import roteiros

casos = 0


def verificar(ok: bool, nome: str) -> None:
    global casos
    casos += 1
    assert ok, nome


TEXTO = "Uma explicação caricata em várias partes; vamos começar!"
ATUACAO_VALIDA = [
    {
        "indice": 0,
        "emocao": "Felicidade",
        "deslocamento": {"pixels": 140, "duracao": 1.5},
        "enquadramento": "corpo",
    },
    {
        "indice": 30,
        "gesto": "conversa_03",
        "deslocamento": {"pixels": 0, "duracao": 0.75},
        "enquadramento": "normal",
    },
]

verificar(len(falar.EMOCOES) == 28, "28 perfis de expressão estão disponíveis")
for perfil in falar.EMOCOES:
    verificar(falar.validar(TEXTO, "Codex", emocao=perfil)["emocao"] == perfil, "perfil aceito: " + perfil)

verificar(falar.validar_atuacao(ATUACAO_VALIDA, TEXTO) == ATUACAO_VALIDA, "aceita deslocamento e enquadramento válidos")
verificar(
    falar.validar_atuacao(
        [
            {"indice": 0, "deslocamento": {"pixels": -180, "duracao": 0.5}},
            {"indice": 30, "deslocamento": {"pixels": 180, "duracao": 6}},
        ],
        TEXTO,
    )
    == [
        {"indice": 0, "deslocamento": {"pixels": -180, "duracao": 0.5}},
        {"indice": 30, "deslocamento": {"pixels": 180, "duracao": 6}},
    ],
    "aceita limites inclusivos de pixels e duração",
)

texto_curto = "Vamos explicar com alegria!"
texto_longo = (
    "Primeiro, vamos entender o começo. Depois, organizamos as ideias com calma. "
    "Então, aparece uma surpresa engraçada! Por fim, agradeço por acompanhar a explicação. "
    "Agora podemos comemorar e seguir para a próxima parte."
)
for nome in ("explicacao", "comedia", "agradecimento", "animada"):
    cenas_curtas = roteiros.montar(texto_curto, nome)
    verificar(len(cenas_curtas) == 1 and cenas_curtas[0]["indice"] == 0, "roteiro curto usa uma cena: " + nome)
    verificar(falar.validar_atuacao(cenas_curtas, texto_curto) == cenas_curtas, "roteiro curto passa validação: " + nome)

    cenas_longas = roteiros.montar(texto_longo, nome)
    indices = [cena["indice"] for cena in cenas_longas]
    verificar(len(cenas_longas) > 1, "roteiro longo gera múltiplos acentos: " + nome)
    verificar(all(0 <= indice < len(texto_longo) for indice in indices), "índices do roteiro estão no texto: " + nome)
    verificar(all(esquerda < direita for esquerda, direita in zip(indices, indices[1:])), "índices do roteiro crescem: " + nome)
    verificar(falar.validar_atuacao(cenas_longas, texto_longo) == cenas_longas, "roteiro longo passa validação: " + nome)

invalidas = [
    [{"indice": 0, "deslocamento": {"pixels": True, "duracao": 1}}],
    [{"indice": 0, "deslocamento": {"pixels": 1, "duracao": False}}],
    [{"indice": 0, "deslocamento": {"pixels": math.nan, "duracao": 1}}],
    [{"indice": 0, "deslocamento": {"pixels": 1, "duracao": math.inf}}],
    [{"indice": 0, "deslocamento": {"pixels": -math.inf, "duracao": 1}}],
    [{"indice": 0, "deslocamento": {"pixels": "40", "duracao": 1}}],
    [{"indice": 0, "deslocamento": {"pixels": 40, "duracao": "1"}}],
    [{"indice": 0, "deslocamento": [40, 1]}],
    [{"indice": 0, "deslocamento": {"pixels": 40, "duracao": 1, "curva": "sine"}}],
    [{"indice": 0, "deslocamento": {"pixels": 40}}],
    [{"indice": 0, "deslocamento": {"duracao": 1}}],
    [{"indice": 0, "deslocamento": {"pixels": -181, "duracao": 1}}],
    [{"indice": 0, "deslocamento": {"pixels": 181, "duracao": 1}}],
    [{"indice": 0, "deslocamento": {"pixels": 0, "duracao": 0.49}}],
    [{"indice": 0, "deslocamento": {"pixels": 0, "duracao": 6.01}}],
    [{"indice": 0, "deslocamento": {"pixels": 0, "duracao": 1}, "extra": 1}],
    [{"indice": 0, "enquadramento": True}],
    [{"indice": 0, "enquadramento": "zoom"}],
]
for cena_invalida in invalidas:
    try:
        falar.validar_atuacao(cena_invalida, TEXTO)
    except ValueError:
        verificar(True, "rejeita cena inválida")
    else:
        verificar(False, "cena inválida foi aceita: " + repr(cena_invalida))

with tempfile.TemporaryDirectory(prefix="kk-anime-encenacao-") as pasta:
    runtime = Path(pasta)
    pid = os.getpid()
    start = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
    (runtime / "pids.json").write_text(json.dumps({"godot": pid, "godot_starttime": start}))
    (runtime / "status.json").write_text(json.dumps({"pid": pid}))

    enviado = falar.enviar(TEXTO, "Codex — teste", emocao="Felicidade", runtime=runtime, voz=False, atuacao=ATUACAO_VALIDA)
    arquivos = list((runtime / "falas").glob("*.json"))
    verificar(len(arquivos) == 1, "envia uma fala no runtime temporário")
    payload = json.loads(arquivos[0].read_text())
    verificar(payload["atuacao"] == ATUACAO_VALIDA, "serialização preserva cenas de encenação")
    verificar(payload["id"] == enviado["id"] and payload["pid_destino"] == pid, "payload mantém identidade de destino")
    verificar("audio" not in payload and not (runtime / "audio").exists(), "voz=False publica fala válida sem gerar áudio")
    verificar(not list((runtime / "falas").glob("*.tmp")), "envio atômico não deixa arquivo temporário")

    # Roteiro é montado pelo caminho de envio; não se testa roteiro em falar.validar().
    (runtime / "falas" / (payload["id"] + ".json")).unlink(missing_ok=True)
    enviar_roteiro = falar.enviar(texto_longo, "Codex — teste", runtime=runtime, voz=False, roteiro="explicacao")
    payload_roteiro = json.loads(next((runtime / "falas").glob("*.json")).read_text())
    verificar(payload_roteiro["id"] == enviar_roteiro["id"], "enviar(roteiro=) publica no runtime temporário")
    verificar(payload_roteiro["atuacao"] == roteiros.montar(texto_longo, "explicacao"), "payload serializa o roteiro montado")
    verificar(falar.validar_atuacao(payload_roteiro["atuacao"], texto_longo) == payload_roteiro["atuacao"], "roteiro enviado passa validar_atuacao")

print(json.dumps({"casos": casos, "passou": True, "erros": []}, ensure_ascii=False))
