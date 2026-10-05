#!/usr/bin/env bash
# Checks everything the demo (demo/README.md) needs before it starts: scripts/demo-check.sh <owner>/<repo>.
# Run from the factory checkout, in Git Bash on Windows or any shell elsewhere.
# One line per check: "ok <name>", "missing <name>: <what to do>", or "note <name>: <what to know>".
# Exit 1 if anything is missing; a note does not stop the demo.

set -u
TARGET="${1:?usage: scripts/demo-check.sh <owner>/<repo>, an empty repository on GitHub}"
status=0

ok()      { echo "ok $1"; }
missing() { echo "missing $1: $2"; status=1; }
note()    { echo "note $1: $2"; }

# --- tools -----------------------------------------------------------------------
for tool in git gh docker uv; do
  if command -v "$tool" >/dev/null 2>&1; then ok "$tool"; else missing "$tool" "install it and put it on the PATH"; fi
done
# Claude Code sets CLAUDECODE=1 for the commands it runs; the desktop app does not put `claude` on the PATH.
{ [ "${CLAUDECODE:-}" = "1" ] || command -v claude >/dev/null 2>&1; } && ok "claude" || missing "claude" "the session runs in Claude Code; this check is meant to run from it"

# --- github -----------------------------------------------------------------------
if gh auth status >/dev/null 2>&1; then
  ok "gh auth"
  scopes="$(gh api -i user 2>/dev/null | grep -i '^x-oauth-scopes:' | tr -d '\r')"
  case "$scopes" in
    *repo*) ok "gh scope repo" ;;
    *) missing "gh scope repo" "gh auth refresh -s repo (needed to merge, close and comment)" ;;
  esac
else
  missing "gh auth" "gh auth login"
fi

if gh api "repos/$TARGET" >/dev/null 2>&1; then
  ok "repo $TARGET exists"
  private="$(gh api "repos/$TARGET" --jq .private 2>/dev/null)"
  [ "$private" = "true" ] && ok "repo $TARGET private" || note "repo $TARGET private" "it is public: everything the demo writes, pull requests included, is visible"
  # Empty means no commits, or main's tree is empty: a further run starts from a commit that
  # removed everything, so the earlier runs stay in the history and their pull requests.
  # GitHub answers 404 for the empty tree itself, so compare the commit's tree with git's.
  EMPTY_TREE=4b825dc642cb6eb9a060e54bf8d69288fbee4904
  if gh api "repos/$TARGET/commits" >/dev/null 2>&1 && [ "$(gh api "repos/$TARGET/commits" --jq length 2>/dev/null)" != "0" ]      && [ "$(gh api "repos/$TARGET/commits/main" --jq .commit.tree.sha 2>/dev/null)" != "$EMPTY_TREE" ]; then
    missing "repo $TARGET empty" "the target must be empty: commit the removal of everything on main (git rm -r .), or use another name"
  else
    ok "repo $TARGET empty"
    # The work volume keeps a checkout per repository with its cost records under .git, keyed by
    # story path; a further run reuses the paths, so a checkout left from a run before would add
    # that run's dollars to every new pull request's cost table.
    if docker compose run --rm --no-deps -T --entrypoint sh factory -c "test ! -e /work/${TARGET##*/}" >/dev/null 2>&1; then
      ok "work volume fresh"
    else
      missing "work volume fresh" "docker compose down && docker volume rm $(basename "$PWD")_work (keeps the login in claude-home)"
    fi
  fi
else
  missing "repo $TARGET exists" "gh repo create $TARGET --private"
fi

# --- docker -----------------------------------------------------------------------
if docker info >/dev/null 2>&1; then ok "docker running"; else missing "docker running" "start Docker Desktop"; fi
docker compose version >/dev/null 2>&1 && ok "docker compose" || missing "docker compose" "Docker Desktop ships it; update Docker"

# --- this checkout -----------------------------------------------------------------
if [ -f .env ]; then
  ok ".env"
  grep -q '^GH_TOKEN=.\+' .env && ok "GH_TOKEN in .env" || missing "GH_TOKEN in .env" "GH_TOKEN=<token with repo scope>"
  if grep -q "^REPOS=.*$TARGET" .env; then ok "REPOS names $TARGET"; else missing "REPOS names $TARGET" "set REPOS=$TARGET in .env (the container serves the repositories listed there)"; fi
else
  missing ".env" "cp .env.example .env and fill it in"
fi
if grep -q '^\.env$' .gitignore 2>/dev/null; then ok ".env ignored by git"; else missing ".env ignored by git" "add .env to .gitignore"; fi

# The session commits the project, the features and the promotions under this identity.
email="$(git config user.email)"
if [ -z "$email" ] || [ -z "$(git config user.name)" ]; then
  missing "git identity" 'git config --global user.name "<name>" && git config --global user.email "<id>+<login>@users.noreply.github.com"'
else
  case "$email" in
    *@users.noreply.github.com) ok "git author address is a GitHub noreply address" ;;
    *) note "git author address" "$email goes into the target's history; github.com/settings/emails shows your noreply address" ;;
  esac
fi
git fetch -q origin 2>/dev/null
[ -z "$(git status --porcelain)" ] && ok "factory tree clean" || missing "factory tree clean" "commit or stash first"
[ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main 2>/dev/null)" ] && ok "factory at origin/main" || missing "factory at origin/main" "git checkout main && git pull --ff-only"
(unset UV_NATIVE_TLS; uv run --frozen factory-watch --help >/dev/null 2>&1) && ok "factory package runs" || missing "factory package runs" "uv sync"

# --- image -------------------------------------------------------------------------
if docker compose config >/dev/null 2>&1; then
  ok "compose config"
  built="$(docker image inspect "$(docker compose config --images 2>/dev/null | head -1)" --format '{{.Created}}' 2>/dev/null)"
  # Docker reports UTC with nanoseconds; compare both as UTC to the second, or a local offset
  # (+02:00) makes a fresh image look two hours older than the commit it was built from.
  built="${built%%.*}"; built="${built%Z}Z"
  head_time="$(TZ=UTC git log -1 --format=%cd --date=format-local:%Y-%m-%dT%H:%M:%SZ)"
  if [ "$built" != "Z" ] && ! [[ "$built" < "$head_time" ]]; then ok "image newer than HEAD"; else missing "image newer than HEAD" "docker compose build"; fi
else
  missing "compose config" "fix compose.yml or .env"
fi

# --- the human's answers ----------------------------------------------------------------
[ -f demo/README.md ] && ok "demo/README.md read by you" || missing "demo/README.md" "git pull"

echo
[ $status -eq 0 ] && echo "all set: docker compose up -d, then give Claude Code the prompt in demo/README.md" || echo "not yet: fix the missing lines first"
exit $status
