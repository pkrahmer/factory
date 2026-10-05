#!/usr/bin/env bash
# Container entrypoint: own a checkout of every repository in REPOS and tick them in turn.
# Settings come from the environment (see compose.yml): REPOS (owner/name, comma-separated),
# GH_TOKEN, TICK_SECONDS (default 120), GIT_USER_NAME, GIT_USER_EMAIL.
set -euo pipefail

: "${REPOS:?set REPOS to owner/name[,owner/name...]}"
: "${GH_TOKEN:?set GH_TOKEN to a token with repo access}"
TICK_SECONDS="${TICK_SECONDS:-120}"

# The skills and agents live in the image; the volume mounted over ~/.claude starts empty,
# so they are copied in on every start (the login token in the volume is left alone).
cp -r /opt/factory/claude/skills /opt/factory/claude/agents "$HOME/.claude/"
cp /opt/factory/claude/settings.json "$HOME/.claude/settings.json"

git config --global user.name "${GIT_USER_NAME:-factory}"
git config --global user.email "${GIT_USER_EMAIL:-factory@users.noreply.github.com}"
git config --global pull.ff only
gh auth setup-git >/dev/null

IFS=',' read -r -a repos <<< "$REPOS"
declare -A synced=() waiting=()

# Bring a checkout to where it can be ticked: cloned, on main, set up for the pipeline
# (`factory/stages.yml`), environment synced. A repository may be cloned while it is still
# empty or before its setup is pushed; the tick cannot fetch for it (it needs the stage table
# first), so until then this fetches and fast-forwards main itself. Returns 1 while the
# repository is not ready and says why once, not every round.
prepare() {
  local repo="$1" work="/work/${1##*/}" why=""
  if [ ! -d "$work/.git" ]; then
    echo "cloning $repo into $work"
    gh repo clone "$repo" "$work" -- --quiet || return 1
  fi
  if [ ! -f "$work/factory/stages.yml" ] && git -C "$work" fetch -q origin \
     && git -C "$work" rev-parse -q --verify origin/main >/dev/null; then
    if ! git -C "$work" rev-parse -q --verify HEAD >/dev/null; then
      git -C "$work" checkout -q -B main origin/main   # cloned empty: main did not exist yet
    elif [ "$(git -C "$work" rev-parse --abbrev-ref HEAD)" = main ]; then
      git -C "$work" merge -q --ff-only origin/main || true
    fi
  fi
  if ! git -C "$work" rev-parse -q --verify HEAD >/dev/null; then
    why="the repository is still empty"
  elif [ ! -f "$work/factory/stages.yml" ]; then
    why="main has no factory/stages.yml yet (see template/ in the factory)"
  elif [ -z "${synced[$repo]:-}" ] && [ -f "$work/pyproject.toml" ] \
       && ! (cd "$work" && uv sync --frozen --quiet); then
    why="uv sync --frozen failed"
  fi
  if [ -n "$why" ]; then
    [ "${waiting[$repo]:-}" = "$why" ] || echo "waiting for $repo: $why"
    waiting[$repo]="$why"
    return 1
  fi
  [ -z "${waiting[$repo]:-}" ] || echo "$repo is ready"
  waiting[$repo]=""
  synced[$repo]=1
}

# Nothing runs in a checkout before the first round, so a lock found there was left by a run
# the restart killed: a tick lock would idle the repository for lease + 10 minutes, a git index
# lock would fail every git command. The start time lets the tick expire claims of killed runs.
# The memo of the last handled line goes too: a restart usually brings a new factory version,
# and whatever the old one left as handled-but-stuck deserves one more try.
export FACTORY_STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
# As PID 1, bash ignores SIGTERM unless it traps it: `docker stop` would wait ten seconds and
# kill. A running tick still finishes first (bash runs the trap after the foreground command).
trap 'echo "factory stopping"; exit 0' TERM INT
for repo in "${repos[@]}"; do
  git_dir="/work/${repo##*/}/.git"
  rm -f "$git_dir/factory-tick.lock" "$git_dir/index.lock" "$git_dir/factory-tick.json"
done

echo "factory ticking every ${TICK_SECONDS}s on ${REPOS}"
# Exit code 3 from a tick means a line was just handled there; evaluate that
# repository again at once instead of waiting out the interval.
while true; do
  again=0
  for repo in "${repos[@]}"; do
    prepare "$repo" || continue
    rc=0
    (cd "/work/${repo##*/}" && factory-tick) || rc=$?
    if [ "$rc" -eq 3 ]; then again=1; fi
  done
  # In the background and waited for, so `docker stop` ends the wait at once (see the trap).
  if [ "$again" -eq 1 ]; then sleep 2 & else sleep "$TICK_SECONDS" & fi
  wait $!
done
