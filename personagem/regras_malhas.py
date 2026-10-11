"""Decisões de exportação explícitas, preservadas no relatório de cobertura."""

def decisao(m, tipo, card):
    nome = m['go']
    shaders = {v['shader'] for v in m['materiais'] if v}
    if tipo == 'corpo':
        if nome in ('o_mnpa','o_mnpb') and shaders == {'Shader Forge/mnpb'}:
            return False, 'auxiliar de mosaico: ChaReference S_MNPA/S_MNPB/S_MOZ_ALL; shader mnpb'
        if nome == 'o_dankon':
            return False, 'componente alternativo: UncensorSelector DisplayPenis=false nesta seleção'
        if nome == 'o_gomu':
            return False, 'componente condicional: ChaReference S_GOMU; Status.visibleGomu=false'
        if shaders == {'Shader Forge/shadowcast'}:
            return False, 'proxy de sombra Unity; sombra Godot usa as malhas visíveis'
    if not m['ativo']:
        return False, m.get('motivo_inativo','renderer/GameObject inativo na origem')
    if not any(m['materiais']):
        return False, 'malha auxiliar sem material renderizável'
    if nome == 'cf_O_canine' and not card['Custom']['rosto']['doubleTooth']:
        return False, 'doubleTooth desativado no card'
    if nome == 'o_top_tsyats_b':
        return False, 'variante parcialmente retirada da camiseta; estado vestido selecionado'
    if nome.startswith('cf_O_namida'):
        return False, 'lágrima condicional não ativada no estado facial selecionado'
    return True, 'malha selecionada e material resolvido'
