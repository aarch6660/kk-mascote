"""Direção de atuação escolhida pelo agente, sem classificar emoções por palavras."""
import re

ROTEIROS = {
    'explicacao': [
        {'emocao':'Curiosidade','gesto':'conversa_gesto_00','movimento':'inclinar'},
        {'emocao':'Pensativa','gesto':'conversa_03','enquadramento':'corpo','deslocamento':{'pixels':140,'duracao':3}},
        {'emocao':'Orgulho','gesto':'conversa_gesto_03','deslocamento':{'pixels':0,'duracao':3},'movimento':'concordar'},
        {'emocao':'Espanto','gesto':'conversa_gesto_07','enquadramento':'normal','efeito':'estrelas'},
        {'emocao':'Confiança','gesto':'conversa_gesto_11','efeito':'ideia','movimento':'concordar'},
    ],
    'comedia': [
        {'emocao':'Dúvida','gesto':'conversa_03','efeito':'interrogacao','movimento':'inclinar'},
        {'emocao':'Espanto','gesto':'stand_oth_01','efeito':'surpresa'},
        {'emocao':'Pânico cômico','gesto':'stand_oth_08','efeito':'suor'},
        {'emocao':'Birra','gesto':'stand_ang_01','efeito':'raiva','movimento':'negar'},
        {'emocao':'Gargalhada','gesto':'stand_joy_02','efeito':'alegria','movimento':'concordar'},
    ],
    'agradecimento': [
        {'emocao':'Vergonha fofa','gesto':'stand_oth_02','efeito':'rubor'},
        {'emocao':'Encantada','gesto':'conversa_gesto_03','efeito':'coracoes','movimento':'concordar'},
        {'emocao':'Gargalhada','gesto':'stand_joy_03','efeito':'alegria'},
    ],
    'animada': [
        {'emocao':'Encantada','gesto':'conversa_gesto_00','efeito':'estrelas'},
        {'emocao':'Orgulho','gesto':'comemorar_03','efeito':'ideia'},
        {'emocao':'Gargalhada','gesto':'stand_joy_05','efeito':'alegria','movimento':'concordar'},
    ],
}

def montar(texto, nome):
    if nome not in ROTEIROS:
        raise ValueError('Roteiro desconhecido.')
    # Falas curtas recebem uma pose; falas longas têm acentos espaçados.
    cenas = ROTEIROS[nome][:1] if len(texto)<80 else ROTEIROS[nome]
    inicios = [0] + [m.end() for m in re.finditer(r'[.!?。！？]\s*',texto) if m.end()<len(texto)]
    if len(inicios)<len(cenas):
        inicios = sorted(set(inicios+[m.start() for m in re.finditer(r'\S+',texto)]))
    resultado=[]
    anterior=-1
    for i,cena in enumerate(cenas):
        alvo=round(i*len(texto)/len(cenas))
        candidatos=[p for p in inicios if anterior<p<len(texto)]
        if not candidatos:
            break
        indice=min(candidatos,key=lambda p:abs(p-alvo)) if i else 0
        resultado.append(dict(cena,indice=indice))
        anterior=indice
    return resultado
