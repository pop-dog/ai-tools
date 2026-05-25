#!/usr/bin/env bash
# Shared symlink and gitignore logic for ai resource manage scripts.
# Source this file; do not execute it directly.
#
# Override these before sourcing or after sourcing to customise per-resource:
GITIGNORE_COMMENT="# Claude skills (managed by 'ai skills install')"
GITIGNORE_PATH_PREFIX=".claude/skills/"
INTERACTIVE=false

prompt_yes() {
    local msg="$1"
    if [[ "$INTERACTIVE" == true ]]; then
        read -r -p "      $msg [y/N] " answer
        [[ "${answer,,}" == "y" ]]
    else
        return 0
    fi
}

do_link() {
    local src="$1"
    local target="$2"
    local name
    name="$(basename "$src")"

    if [[ -L "$target" ]]; then
        local current
        current="$(readlink "$target")"
        if [[ "$current" == "$src" ]]; then
            echo "SKIP    $name — already installed"
        else
            echo "SKIP    $name — symlink points elsewhere ($current)"
        fi
        return
    elif [[ -e "$target" ]]; then
        echo "SKIP    $name — path exists and is not a symlink"
        return
    fi

    if prompt_yes "$name is not installed. Install?"; then
        ln -s "$src" "$target"
        echo "INSTALL $name"
    else
        echo "SKIP    $name"
    fi
}

do_unlink() {
    local target="$1"
    local name
    name="$(basename "$target")"

    if [[ ! -L "$target" ]]; then
        echo "SKIP    $name — not a managed symlink"
        return
    fi

    if prompt_yes "$name is installed. Uninstall?"; then
        rm "$target"
        echo "REMOVE  $name"
    else
        echo "SKIP    $name"
    fi
}

# Returns true if name is in the filter list, or if filter list is empty.
name_matches() {
    local name="$1"
    shift
    local filter_names=("$@")
    [[ ${#filter_names[@]} -eq 0 ]] && return 0
    local n
    for n in "${filter_names[@]}"; do
        [[ "$n" == "$name" ]] && return 0
    done
    return 1
}

add_gitignore_entry() {
    local project_root="$1"
    local entry="$2"
    local gitignore="$project_root/.gitignore"

    grep -qxF "$entry" "$gitignore" 2>/dev/null && return

    if ! grep -qxF "$GITIGNORE_COMMENT" "$gitignore" 2>/dev/null; then
        printf '\n%s\n' "$GITIGNORE_COMMENT" >> "$gitignore"
    fi

    echo "$entry" >> "$gitignore"
}

remove_gitignore_entry() {
    local project_root="$1"
    local entry="$2"
    local gitignore="$project_root/.gitignore"

    [[ -f "$gitignore" ]] || return 0

    local tmp
    tmp="$(mktemp)"
    grep -vxF "$entry" "$gitignore" > "$tmp" || true
    mv "$tmp" "$gitignore"

    # Remove comment header if no more managed entries remain
    if ! grep -qF "$GITIGNORE_PATH_PREFIX" "$gitignore" 2>/dev/null; then
        tmp="$(mktemp)"
        grep -vxF "$GITIGNORE_COMMENT" "$gitignore" > "$tmp" || true
        mv "$tmp" "$gitignore"
    fi
}

# Prints .claude/skills/<name> entries from the managed block in .gitignore
get_gitignore_managed() {
    local project_root="$1"
    local gitignore="$project_root/.gitignore"
    [[ -f "$gitignore" ]] || return 0
    grep -x '\.claude/skills/[^/]*' "$gitignore" 2>/dev/null || true
}
