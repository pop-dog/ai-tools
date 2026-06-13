#!/usr/bin/env bash
#
# dev-link.sh — link skills/agents straight from this working tree into
# ~/.claude so you can test them live, before committing.
#
# Unlike install.sh, this never touches the store (~/.ai-tools): it symlinks
# the working-tree copy directly, so edits are picked up immediately. The
# links point into this repo, which makes them "foreign" to install.sh — a
# later remote install or --update will skip them rather than clobber.
#
#   ./dev-link.sh my-skill            # link one working-tree item
#   ./dev-link.sh --all               # link everything in the working tree
#   ./dev-link.sh --list              # show working-tree items + link status
#   ./dev-link.sh --unlink my-skill   # remove that dev link
#   ./dev-link.sh --unlink --all      # remove every dev link from this repo

set -euo pipefail
shopt -s nullglob

CLAUDE_SKILLS="${HOME}/.claude/skills"
CLAUDE_AGENTS="${HOME}/.claude/agents"

# This is a clone-only tool — it needs a real file path to find the repo.
SOURCE="${BASH_SOURCE[0]:-}"
case "$SOURCE" in
    "" | bash | sh | /dev/*)
        echo "Error: dev-link.sh must be run from a clone (e.g. ./dev-link.sh), not piped to a shell." >&2
        exit 1
        ;;
esac
REPO_DIR="$(cd "$(dirname "$SOURCE")" && pwd)"

usage() {
    cat <<EOF
Usage: dev-link.sh [mode] [names...]

Links skills/agents from this working tree into ~/.claude for live testing.

Modes:
  <names...>          dev-link the named working-tree items
  --all               dev-link every working-tree skill and agent
  --list              show working-tree items and their link status
  --unlink <names>    remove the named dev links
  --unlink --all      remove every dev link pointing into this repo
  -h, --help          show this help

Dev links point at this repo's working tree, so edits are live. They never
use the store (~/.ai-tools) and are left untouched by install.sh.
EOF
}

die() {
    echo "Error: $*" >&2
    exit 1
}

# A link is a dev link of ours if it points into this repo's working tree.
is_devlink() {
    [[ -L "$1" ]] && [[ "$(readlink "$1")" == "${REPO_DIR}/"* ]]
}

# Build the working-tree catalog: SKILLS (dirs in skills/ with a SKILL.md),
# AGENTS (flat .md files in agents/).
scan_catalog() {
    SKILLS=()
    AGENTS=()
    local d f
    for d in "$REPO_DIR"/skills/*/; do
        [[ -f "${d}SKILL.md" ]] && SKILLS+=("$(basename "$d")")
    done
    for f in "$REPO_DIR"/agents/*.md; do
        AGENTS+=("$(basename "$f" .md)")
    done
}

# Echoes "skill" or "agent" for a catalog name, or nothing if absent.
kind_of() {
    local name="$1" s a
    for s in ${SKILLS[@]+"${SKILLS[@]}"}; do
        [[ "$s" == "$name" ]] && { echo skill; return; }
    done
    for a in ${AGENTS[@]+"${AGENTS[@]}"}; do
        [[ "$a" == "$name" ]] && { echo agent; return; }
    done
}

link_path() {
    if [[ "$1" == skill ]]; then echo "${CLAUDE_SKILLS}/${2}"; else echo "${CLAUDE_AGENTS}/${2}.md"; fi
}

src_path() {
    if [[ "$1" == skill ]]; then echo "${REPO_DIR}/skills/${2}"; else echo "${REPO_DIR}/agents/${2}.md"; fi
}

link_item() {
    local kind="$1" name="$2" link src
    link="$(link_path "$kind" "$name")"
    src="$(src_path "$kind" "$name")"
    mkdir -p "$(dirname "$link")"

    if is_devlink "$link"; then
        rm "$link"
        ln -s "$src" "$link"
        echo "Re-linked ${kind} ${name} (dev)"
    elif [[ -e "$link" || -L "$link" ]]; then
        echo "Skipped ${kind} ${name}: already present at ${link} (not a dev link — uninstall it first)" >&2
    else
        ln -s "$src" "$link"
        echo "Dev-linked ${kind} ${name}"
    fi
}

unlink_one() {
    local kind="$1" name="$2" link
    link="$(link_path "$kind" "$name")"
    if is_devlink "$link"; then
        rm "$link"
        echo "Unlinked ${kind} ${name}"
        return 0
    fi
    return 1
}

unlink_all() {
    local dir link n=0
    for dir in "$CLAUDE_SKILLS" "$CLAUDE_AGENTS"; do
        [[ -d "$dir" ]] || continue
        for link in "$dir"/*; do
            if is_devlink "$link"; then
                rm "$link"
                echo "Unlinked ${link}"
                n=$((n + 1))
            fi
        done
    done
    echo "Removed ${n} dev link(s)."
}

print_list() {
    local name link status
    echo ""
    echo "Working tree: ${REPO_DIR}"
    echo ""
    echo "  Skills"
    [[ ${#SKILLS[@]} -eq 0 ]] && echo "   (none)"
    for name in ${SKILLS[@]+"${SKILLS[@]}"}; do
        link="$(link_path skill "$name")"
        if is_devlink "$link"; then status="dev-linked"
        elif [[ -e "$link" || -L "$link" ]]; then status="other (not ours)"
        else status="-"; fi
        printf '   %-20s %s\n' "$name" "$status"
    done
    echo ""
    echo "  Agents"
    [[ ${#AGENTS[@]} -eq 0 ]] && echo "   (none)"
    for name in ${AGENTS[@]+"${AGENTS[@]}"}; do
        link="$(link_path agent "$name")"
        if is_devlink "$link"; then status="dev-linked"
        elif [[ -e "$link" || -L "$link" ]]; then status="other (not ours)"
        else status="-"; fi
        printf '   %-20s %s\n' "$name" "$status"
    done
    echo ""
}

# --- main ---------------------------------------------------------------

UNLINK=0
ALL=0
LIST=0
NAMES=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --unlink) UNLINK=1 ;;
        --all) ALL=1 ;;
        --list) LIST=1 ;;
        -h | --help)
            usage
            exit 0
            ;;
        --*) die "unknown flag: $1 (try --help)" ;;
        *) NAMES+=("$1") ;;
    esac
    shift
done

scan_catalog

if [[ "$LIST" -eq 1 ]]; then
    print_list
    exit 0
fi

if [[ "$UNLINK" -eq 1 ]]; then
    if [[ "$ALL" -eq 1 ]]; then
        unlink_all
        exit 0
    fi
    [[ ${#NAMES[@]} -gt 0 ]] || die "--unlink needs item names or --all"
    for name in "${NAMES[@]}"; do
        unlink_one skill "$name" || unlink_one agent "$name" \
            || echo "Skipped ${name}: no dev link from this repo" >&2
    done
    exit 0
fi

# Link mode
if [[ "$ALL" -eq 1 ]]; then
    [[ ${#NAMES[@]} -eq 0 ]] || die "--all cannot be combined with item names"
    for name in ${SKILLS[@]+"${SKILLS[@]}"}; do link_item skill "$name"; done
    for name in ${AGENTS[@]+"${AGENTS[@]}"}; do link_item agent "$name"; done
    echo "Done."
    exit 0
fi

[[ ${#NAMES[@]} -gt 0 ]] || { usage; exit 1; }

for name in "${NAMES[@]}"; do
    kind="$(kind_of "$name")"
    [[ -n "$kind" ]] || die "'${name}' is not in the working tree (try --list)"
    link_item "$kind" "$name"
done
echo "Done."
