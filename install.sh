#!/usr/bin/env bash
#
# install.sh — installer for the pop-dog/ai-tools catalog of Claude Code
# skills and agents.
#
#   curl -sSL https://raw.githubusercontent.com/pop-dog/ai-tools/mainline/install.sh | bash
#
# The whole catalog is mirrored into ~/.ai-tools (the store) on every run;
# installing means symlinking selected items into ~/.claude. Re-running with
# --update refreshes the store so every installed item updates in place.

set -euo pipefail
shopt -s nullglob

REPO="pop-dog/ai-tools"
BRANCH="mainline"
TARBALL_URL="https://codeload.github.com/${REPO}/tar.gz/refs/heads/${BRANCH}"
STORE="${HOME}/.ai-tools"
CLAUDE_SKILLS="${HOME}/.claude/skills"
CLAUDE_AGENTS="${HOME}/.claude/agents"

usage() {
    cat <<EOF
Usage: install.sh [mode]

Installs Claude Code skills and agents from ${REPO}.

Modes:
  (no args)     interactive picker
  <names...>    install the named skills/agents
  --all         install everything in the catalog
  --list        show the catalog and exit
  --update      refresh ~/.ai-tools; installed items update in place
  --uninstall   remove all installed symlinks and delete ~/.ai-tools
  -h, --help    show this help

Typically run remotely:
  curl -sSL https://raw.githubusercontent.com/${REPO}/${BRANCH}/install.sh | bash
  curl -sSL ... | bash -s -- --all
EOF
}

die() {
    echo "Error: $*" >&2
    exit 1
}

# A symlink is ours if it points into the store. Anything else at an install
# target is a foreign entry and is never touched.
is_ours() {
    local target
    [[ -L "$1" ]] || return 1
    target="$(readlink "$1")"
    [[ "$target" == "${STORE}/"* || "$target" == *"/.ai-tools/"* ]]
}

uninstall_all() {
    local dir link n=0
    for dir in "$CLAUDE_SKILLS" "$CLAUDE_AGENTS"; do
        [[ -d "$dir" ]] || continue
        for link in "$dir"/*; do
            if is_ours "$link"; then
                rm "$link"
                echo "Removed ${link}"
                n=$((n + 1))
            fi
        done
    done
    if [[ -d "$STORE" ]]; then
        rm -rf "$STORE"
        echo "Deleted ${STORE}"
    fi
    echo "Uninstalled (${n} symlinks removed)."
}

# Downloads the repo tarball and builds the catalog: SKILLS (directories in
# /skills containing a SKILL.md) and AGENTS (flat .md files in /agents).
fetch_catalog() {
    TMP="$(mktemp -d)"
    trap 'rm -rf "$TMP"' EXIT
    echo "Fetching ${REPO}@${BRANCH}..."
    curl -fsSL "$TARBALL_URL" | tar -xz -C "$TMP" \
        || die "could not download ${TARBALL_URL}"
    SRC="$(find "$TMP" -mindepth 1 -maxdepth 1 -type d -print | head -n 1)"
    [[ -n "$SRC" ]] || die "unexpected tarball layout"

    SKILLS=()
    AGENTS=()
    local d f
    for d in "$SRC"/skills/*/; do
        [[ -f "${d}SKILL.md" ]] && SKILLS+=("$(basename "$d")")
    done
    for f in "$SRC"/agents/*.md; do
        AGENTS+=("$(basename "$f" .md)")
    done
}

refresh_store() {
    local name
    rm -rf "${STORE}/skills" "${STORE}/agents"
    mkdir -p "${STORE}/skills" "${STORE}/agents"
    for name in ${SKILLS[@]+"${SKILLS[@]}"}; do
        cp -R "${SRC}/skills/${name}" "${STORE}/skills/${name}"
    done
    for name in ${AGENTS[@]+"${AGENTS[@]}"}; do
        cp "${SRC}/agents/${name}.md" "${STORE}/agents/${name}.md"
    done
    echo "Store refreshed: ${STORE}"
}

# After a refresh, our symlinks whose catalog item was removed point at
# nothing; drop them so Claude Code never sees a dangling link.
prune_dangling() {
    local dir link
    for dir in "$CLAUDE_SKILLS" "$CLAUDE_AGENTS"; do
        [[ -d "$dir" ]] || continue
        for link in "$dir"/*; do
            if is_ours "$link" && [[ ! -e "$link" ]]; then
                rm "$link"
                echo "Pruned ${link} (no longer in catalog)"
            fi
        done
    done
}

print_catalog() {
    local i=1 name
    echo ""
    echo "Available from ${REPO}:"
    echo ""
    echo "  Skills"
    if [[ ${#SKILLS[@]} -eq 0 ]]; then
        echo "   (none)"
    else
        for name in "${SKILLS[@]}"; do
            printf '  %2d) %s\n' "$i" "$name"
            i=$((i + 1))
        done
    fi
    echo ""
    echo "  Agents"
    if [[ ${#AGENTS[@]} -eq 0 ]]; then
        echo "   (none)"
    else
        for name in "${AGENTS[@]}"; do
            printf '  %2d) %s\n' "$i" "$name"
            i=$((i + 1))
        done
    fi
    echo ""
}

pick_interactive() {
    [[ -r /dev/tty ]] \
        || die "no TTY available; use --all, --list, or pass item names (e.g. ... | bash -s -- --all)"
    print_catalog
    local total=$((${#SKILLS[@]} + ${#AGENTS[@]}))
    [[ "$total" -gt 0 ]] || die "the catalog is empty"

    local sel
    printf 'Select [numbers / a = all / q = quit]: '
    IFS= read -r sel < /dev/tty || sel="q"

    case "$sel" in
        q | Q | "")
            echo "Nothing installed."
            exit 0
            ;;
        a | A)
            PICK_SKILLS=(${SKILLS[@]+"${SKILLS[@]}"})
            PICK_AGENTS=(${AGENTS[@]+"${AGENTS[@]}"})
            return
            ;;
    esac

    PICK_SKILLS=()
    PICK_AGENTS=()
    local tok
    for tok in $(echo "$sel" | tr ',' ' '); do
        [[ "$tok" =~ ^[0-9]+$ ]] || die "invalid selection: ${tok}"
        [[ "$tok" -ge 1 && "$tok" -le "$total" ]] || die "selection out of range: ${tok}"
        if [[ "$tok" -le ${#SKILLS[@]} ]]; then
            PICK_SKILLS+=("${SKILLS[$((tok - 1))]}")
        else
            PICK_AGENTS+=("${AGENTS[$((tok - 1 - ${#SKILLS[@]}))]}")
        fi
    done
}

pick_named() {
    PICK_SKILLS=()
    PICK_AGENTS=()
    local arg name found
    for arg in "$@"; do
        found=0
        for name in ${SKILLS[@]+"${SKILLS[@]}"}; do
            [[ "$name" == "$arg" ]] && { PICK_SKILLS+=("$arg"); found=1; }
        done
        for name in ${AGENTS[@]+"${AGENTS[@]}"}; do
            [[ "$name" == "$arg" ]] && { PICK_AGENTS+=("$arg"); found=1; }
        done
        [[ "$found" -eq 1 ]] || die "'${arg}' is not in the catalog (try --list)"
    done
}

# link_item <skill|agent> <name> — symlink a store item into ~/.claude.
link_item() {
    local kind="$1" name="$2" link rel
    if [[ "$kind" == "skill" ]]; then
        mkdir -p "$CLAUDE_SKILLS"
        link="${CLAUDE_SKILLS}/${name}"
        rel="../../.ai-tools/skills/${name}"
    else
        mkdir -p "$CLAUDE_AGENTS"
        link="${CLAUDE_AGENTS}/${name}.md"
        rel="../../.ai-tools/agents/${name}.md"
    fi

    if [[ -e "$link" || -L "$link" ]]; then
        if is_ours "$link"; then
            rm "$link"
            ln -s "$rel" "$link"
            echo "Updated ${kind} ${name} (already installed)"
        else
            echo "Skipped ${kind} ${name}: foreign entry at ${link}" >&2
        fi
    else
        ln -s "$rel" "$link"
        echo "Installed ${kind} ${name}"
    fi
}

# --- main ---------------------------------------------------------------

MODE="interactive"
NAMES=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --list) MODE="list" ;;
        --all) MODE="all" ;;
        --update) MODE="update" ;;
        --uninstall) MODE="uninstall" ;;
        -h | --help)
            usage
            exit 0
            ;;
        --*) die "unknown flag: $1 (try --help)" ;;
        *) NAMES+=("$1") ;;
    esac
    shift
done

if [[ "$MODE" != "interactive" && ${#NAMES[@]} -gt 0 ]]; then
    die "--${MODE} cannot be combined with item names"
fi
[[ ${#NAMES[@]} -gt 0 ]] && MODE="named"

if [[ "$MODE" == "uninstall" ]]; then
    uninstall_all
    exit 0
fi

fetch_catalog

case "$MODE" in
    list)
        print_catalog
        exit 0
        ;;
    update)
        refresh_store
        prune_dangling
        echo "Update complete; installed items now track ${BRANCH}."
        exit 0
        ;;
    all)
        PICK_SKILLS=(${SKILLS[@]+"${SKILLS[@]}"})
        PICK_AGENTS=(${AGENTS[@]+"${AGENTS[@]}"})
        ;;
    named)
        pick_named ${NAMES[@]+"${NAMES[@]}"}
        ;;
    interactive)
        pick_interactive
        ;;
esac

refresh_store
prune_dangling

for name in ${PICK_SKILLS[@]+"${PICK_SKILLS[@]}"}; do
    link_item skill "$name"
done
for name in ${PICK_AGENTS[@]+"${PICK_AGENTS[@]}"}; do
    link_item agent "$name"
done

echo "Done."
