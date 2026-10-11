"""Fontes locais e seleção UncensorSelector, auditadas na DLL 3.12.3.

Lê ZIPs/configuração sem instalar mods ou alterar o jogo. A seleção do card
precede o padrão do plugin. Não transforma uma seleção desconhecida em vanilla.
"""
from __future__ import annotations
import os
import configparser
import hashlib
import json
from functools import lru_cache
from pathlib import Path, PurePosixPath
import zipfile
import xml.etree.ElementTree as ET

GAME = Path(os.environ.get('KK_JOGO') or Path.home()/'Downloads/Koikatsu.Party/Koikatsu Party')
GUID = 'com.deathweasel.bepinex.uncensorselector'

def sha(data):
    return hashlib.sha256(data).hexdigest()

@lru_cache(maxsize=1)
def inventario():
    pacotes, bundles, corpos, migracoes = [], {}, {}, {}
    for path in sorted((GAME / 'mods').rglob('*.zipmod')):
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            if 'manifest.xml' not in names:
                continue
            raw = z.read('manifest.xml')
            xml = ET.fromstring(raw)
            entry = {'arquivo': str(path.relative_to(GAME)), 'sha256': sha(path.read_bytes()),
                     'guid': xml.findtext('guid'), 'nome': xml.findtext('name'),
                     'versao': xml.findtext('version'), 'manifest_sha256': sha(raw), 'bundles': []}
            for name in names:
                if not name.startswith('abdata/chara/') or not name.endswith('.unity3d'):
                    continue
                relative = name.removeprefix('abdata/')
                if '..' in PurePosixPath(relative).parts:
                    raise ValueError('Caminho inválido no zipmod: '+name)
                fonte = {'arquivo': entry['arquivo'], 'membro': name, 'zip_sha256': entry['sha256']}
                bundles.setdefault(relative, []).append(fonte)
                entry['bundles'].append(relative)
            for body in xml.findall('KK_UncensorSelector/body'):
                key = body.findtext('guid')
                if key in corpos:
                    raise ValueError('GUID corporal duplicado: '+str(key))
                base = body.find('oo_base')
                if base is None:
                    continue
                corpos[key] = {'guid': key, 'nome': body.findtext('displayName', key),
                    'sexo': 1 if body.findtext('sex','').lower() == 'female' else 0,
                    'MainAB': base.findtext('file'), 'MainData': base.findtext('asset','p_cf_body_00'),
                    'mainTex': base.findtext('mainTex','cf_body_00_t'),
                    'colorMask': base.findtext('colorMask','cf_body_00_mc'),
                    'materialAB': base.findtext('mm_base','chara/mm_base.unity3d'),
                    'material': base.findtext('material','cf_m_body'),
                    'materialCreate': base.findtext('materialCreate','cf_m_body_create'),
                    'additionalParts': [p.text for p in base.findall('additionalPart')],
                    'overlay': base.findtext('uncensorOverlay'), 'underlay': base.findtext('uncensorUnderlay'),
                    'colorMatch': [{x.tag:x.text for x in v} for v in base.findall('colorMatch')],
                    'pacote': entry['arquivo'], 'pacote_sha256': entry['sha256']}
            for v in xml.findall('KK_UncensorSelector/migration'):
                migracoes[v.findtext('guidUncensor')] = {x.tag: x.text for x in v}
            pacotes.append(entry)
    plugins = []
    for path in sorted((GAME/'BepInEx/plugins').rglob('*.dll')):
        plugins.append({'arquivo':str(path.relative_to(GAME)), 'sha256':sha(path.read_bytes())})
    return {'pacotes':pacotes, 'bundles':bundles, 'corpos':corpos, 'migracoes':migracoes, 'plugins':plugins}

def configuracao(nome):
    p = GAME/'BepInEx/config'/nome
    c = configparser.ConfigParser(interpolation=None, strict=False)
    if p.exists():
        c.read(p, encoding='utf-8-sig')
    return c

def fonte_bundle(relative, pacote=None):
    relative = str(relative).replace('\\','/')
    if not relative.startswith('chara/') or '..' in PurePosixPath(relative).parts:
        raise ValueError('Bundle corporal fora de chara: '+relative)
    choices = inventario()['bundles'].get(relative, [])
    if pacote:
        choices = [v for v in choices if v['arquivo'] == pacote]
        if len(choices) != 1:
            raise ValueError('Bundle ausente/ambíguo no mod: '+relative)
    # Fontes originais permanecem explícitas. Substituições são selecionadas
    # pelo manifesto, nunca por uma colisão acidental entre nomes de arquivos.
    elif (GAME/'abdata'/relative).is_file():
        p = GAME/'abdata'/relative
        return {'arquivo':str(p.relative_to(GAME)), 'sha256':sha(p.read_bytes())}
    if len(choices) != 1:
        raise ValueError('Bundle local ausente/ambíguo: '+relative)
    result = dict(choices[0])
    result['sha256'] = sha(ler_fonte(result))
    return result

def ler_fonte(fonte):
    path = (GAME/fonte['arquivo']).resolve()
    path.relative_to(GAME.resolve())
    if 'membro' in fonte:
        with zipfile.ZipFile(path) as z:
            return z.read(fonte['membro'])
    return path.read_bytes()

def dados_plugin(card, guid):
    v = card.get('ExtendedPlugins',card.get('KKEx',{})).get(guid)
    if v is None:
        return 0, {}
    if isinstance(v,list) and len(v)==2:
        return int(v[0]), v[1] or {}
    if isinstance(v,dict):
        return int(v.get('version',0)), v.get('data',{}) or {}
    raise ValueError('PluginData inválido: '+guid)

def selecionar(card):
    inv = inventario()
    enabled = any(v['arquivo'].endswith('/KK_UncensorSelector.dll') for v in inv['plugins'])
    cfg = configuracao(GUID+'.cfg')
    sex = int(card['Parameter']['sex'])
    if sex != 1:
        raise ValueError('Pipeline atual valida apenas cards femininos')
    version, data = dados_plugin(card,GUID)
    if version == 1:
        old = data.get('UncensorGUID')
        if old and old not in inv['migracoes']:
            raise ValueError('Migração UncensorSelector ausente: '+str(old))
        migration = inv['migracoes'].get(old,{})
        data = {**data, 'BodyGUID':migration.get('guidBody'),
                'DisplayPenis':bool(migration.get('guidPenis'))}
    elif version not in (0,2):
        raise ValueError('Versão UncensorSelector ainda não validada: '+str(version))
    if data.get('DisplayPenis',False) or data.get('DisplayBalls',cfg.getboolean('Config','Default Female Balls Display',fallback=False)):
        raise ValueError('Card seleciona componentes penis/balls: montagem modular ainda não validada; nenhuma substituição silenciosa será feita')
    key = data.get('BodyGUID') or None
    origin = 'card/KKEx' if key else 'configuracao/Default Female Body'
    if not enabled:
        if key:
            raise ValueError('Card exige UncensorSelector, mas a DLL não está instalada')
        key = 'Default.Body.Female'; origin = 'jogo original (plugin ausente)'
    if not key:
        default = cfg.get('Config','Default Female Body',fallback='Random')
        if default == '[Female] Default Body F':
            key = 'Default.Body.Female'
        else:
            matches = [k for k,v in inv['corpos'].items() if '[Female] '+v['nome'] == default and v['sexo']==1]
            if len(matches)!=1:
                raise ValueError('Padrão corporal não determinável: '+default+'; é necessário um BodyGUID explícito ou padrão fixo do jogo')
            key = matches[0]
    if key == 'Default.Body.Female':
        body = {'guid':key,'nome':'Default Body F','sexo':1,'MainAB':'chara/oo_base.unity3d',
                'MainData':'p_cf_body_00','mainTex':'cf_body_00_t','colorMask':'cf_body_00_mc',
                'materialAB':'chara/mm_base.unity3d','material':'cf_m_body','additionalParts':[]}
    elif key in inv['corpos']:
        body = dict(inv['corpos'][key])
    else:
        raise ValueError('Mod corporal selecionado não encontrado: '+str(key))
    if body['sexo']!=1:
        raise ValueError('Corpo masculino em card feminino ainda não validado: '+key)
    if body.get('colorMatch') or body.get('overlay') or body.get('underlay'):
        raise ValueError('Camadas adicionais deste mod exigem adaptação: '+key)
    body.update(tipo='corpo', id=None, origem=origin, versao_plugin_data=version,
                fonte=fonte_bundle(body['MainAB'],body.get('pacote')),
                plugins_card=sorted(card.get('ExtendedPlugins',{})))
    return body

def escrever_inventario(path):
    data = inventario()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
