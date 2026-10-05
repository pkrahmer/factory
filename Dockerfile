# The factory's machine: the pipeline package, its Claude Code skills and agents at user level,
# and the tools the preflight checks for. Repositories are not copied in; the container clones
# the ones named in REPOS into a volume and keeps them current.

FROM python:3.12-slim-bookworm

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y --no-install-recommends git make curl ca-certificates procps gnupg \
 && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
      -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
 && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
      > /etc/apt/sources.list.d/github-cli.list \
 && apt-get update && apt-get install -y --no-install-recommends gh \
 && rm -rf /var/lib/apt/lists/*

# Pin what the loop depends on; bump deliberately.
COPY --from=ghcr.io/astral-sh/uv:0.9.2 /uv /uvx /usr/local/bin/

# Agents run model-written commands; they do that as an ordinary user.
RUN useradd --create-home --uid 1000 factory \
 && mkdir -p /work /home/factory/.claude \
 && chown -R factory:factory /work /home/factory
USER factory
WORKDIR /home/factory
ENV PATH="/home/factory/.local/bin:${PATH}" \
    UV_LINK_MODE=copy \
    CLAUDE_CODE_FORK_SUBAGENT=0

# Claude Code, native build. (npm alternative: `npm install -g @anthropic-ai/claude-code`, needs Node.)
# A pipe into bash must fail when the download fails, not run an empty script.
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ARG CLAUDE_VERSION=latest
RUN curl -fsSL https://claude.ai/install.sh | bash -s -- "$CLAUDE_VERSION" \
 && claude --version

# The pipeline itself: the package on the PATH, skills and agents where every repository sees them.
COPY --chown=factory:factory . /opt/factory
# A Windows checkout may carry CRLF; the kernel would then look for "bash\r".
RUN sed -i 's/\r$//' /opt/factory/entrypoint.sh \
 && uv tool install /opt/factory \
 && mkdir -p /home/factory/.claude \
 && cp -r /opt/factory/claude/skills /opt/factory/claude/agents /home/factory/.claude/ \
 && cp /opt/factory/claude/settings.json /home/factory/.claude/settings.json

# Volumes: the login token (next to the skills, in the same home) and the checkouts.
VOLUME ["/home/factory/.claude", "/work"]
ENTRYPOINT ["/opt/factory/entrypoint.sh"]
