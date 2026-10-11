# Hana: source somente em bash interativo. Sem subprocessos por comando.
[[ $- == *i* ]] || return 0
[[ ${_hana_hook_instalado:-0} == 1 ]] && return 0
_hana_hook_instalado=1
_hana_avisar="${MASCOTE_HANA_AVISAR:-${BASH_SOURCE[0]%/*}/avisar.py}"
_hana_inicio=
_hana_comando=
_hana_no_prompt=1
_hana_debug_anterior=
_hana_trap=$(trap -p DEBUG)
if [[ -n $_hana_trap ]]; then
    _hana_trap=${_hana_trap% DEBUG}
    eval "_hana_debug_anterior=${_hana_trap#trap -- }"
fi
unset _hana_trap

_hana_debug() {
    local hana_status=$1 hana_comando=$2 hana_resultado=0
    if [[ $_hana_no_prompt == 0 && -z $_hana_inicio && $hana_comando != _hana_prompt* && $hana_comando != _hana_pronta* ]]; then
        _hana_inicio=${EPOCHSECONDS:-$SECONDS}
        # Só o nome; argumentos podem conter dados privados.
        _hana_comando=${hana_comando%%[[:space:]]*}
    fi
    if [[ -n $_hana_debug_anterior ]]; then
        # Mantém o status observado pelo trap que já existia.
        _hana_repor_status "$hana_status"
        eval "$_hana_debug_anterior"
        hana_resultado=$?
    fi
    return "$hana_resultado"
}

_hana_repor_status() { return "$1"; }

_hana_prompt() {
    local hana_status=$? hana_fim=${EPOCHSECONDS:-$SECONDS}
    _hana_no_prompt=1
    if [[ -n $_hana_inicio ]] && (( hana_fim - _hana_inicio > 90 )); then
        python3 "$_hana_avisar" "Comando ${_hana_comando:-terminal} terminou após $((hana_fim-_hana_inicio)) s (código de saída $hana_status)." >/dev/null 2>&1 &
    fi
    _hana_inicio=
    _hana_comando=
    return "$hana_status"
}

_hana_pronta() { _hana_no_prompt=0; }

# Preserva string ou array de PROMPT_COMMAND e o código de saída para os hooks existentes.
if [[ $(declare -p PROMPT_COMMAND 2>/dev/null) == 'declare -a '* ]]; then
    PROMPT_COMMAND=(_hana_prompt "${PROMPT_COMMAND[@]}" _hana_pronta)
else
    PROMPT_COMMAND="_hana_prompt; ${PROMPT_COMMAND:+$PROMPT_COMMAND; }_hana_pronta"
fi
trap '_hana_debug "$?" "$BASH_COMMAND"' DEBUG
