FROM node:20

ARG TZ
ENV TZ="$TZ"

# Install basic development tools and iptables/ipset
RUN apt update && apt install -y less \
  git \
  procps \
  sudo \
  fzf \
  zsh \
  man-db \
  unzip \
  gnupg2 \
  gh \
  iptables \
  ipset \
  iproute2 \
  dnsutils \
  aggregate \
  jq \
  python3 \
  python3-pip \
  python3-venv \
  python3-dev \
  build-essential \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Install uv (Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.cargo/bin:$PATH"

# Ensure default node user has access to /usr/local/share
RUN mkdir -p /usr/local/share/npm-global && \
  chown -R node:node /usr/local/share

ARG USERNAME=node

# Persist bash history.
RUN SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
  && mkdir /commandhistory \
  && touch /commandhistory/.bash_history \
  && chown -R $USERNAME /commandhistory

# Set `DEVCONTAINER` environment variable to help with orientation
ENV DEVCONTAINER=true

# Environment variables for development
ENV PYTHONPATH=/workspace/src
ENV DEBUG_MCP_MODE=true
ENV LOG_MCP_MESSAGES=true
ENV LOG_API_PAYLOADS=true
ENV MCP_MODE=false

# Create workspace and config directories and set permissions
RUN mkdir -p /workspace /home/node/.claude && \
  chown -R node:node /workspace /home/node/.claude

WORKDIR /workspace

RUN ARCH=$(dpkg --print-architecture) && \
  wget "https://github.com/dandavison/delta/releases/download/0.18.2/git-delta_0.18.2_${ARCH}.deb" && \
  sudo dpkg -i "git-delta_0.18.2_${ARCH}.deb" && \
  rm "git-delta_0.18.2_${ARCH}.deb"

# Set up non-root user
USER node

# Install uv for node user
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python development tools globally
RUN /home/node/.cargo/bin/uv tool install pytest
RUN /home/node/.cargo/bin/uv tool install pytest-asyncio
RUN /home/node/.cargo/bin/uv tool install pytest-cov
RUN /home/node/.cargo/bin/uv tool install ruff
RUN /home/node/.cargo/bin/uv tool install mypy
RUN /home/node/.cargo/bin/uv tool install twine
RUN /home/node/.cargo/bin/uv tool install build

# Install MCP Inspector for debugging
RUN /home/node/.cargo/bin/uv tool install mcp

# Install global packages
ENV NPM_CONFIG_PREFIX=/usr/local/share/npm-global
ENV PATH=$PATH:/usr/local/share/npm-global/bin:/home/node/.cargo/bin:/home/node/.local/bin

# Set the default shell to zsh rather than sh
ENV SHELL=/bin/zsh

# Default powerline10k theme
RUN sh -c "$(wget -O- https://github.com/deluan/zsh-in-docker/releases/download/v1.2.0/zsh-in-docker.sh)" -- \
  -p git \
  -p fzf \
  -a "source /usr/share/doc/fzf/examples/key-bindings.zsh" \
  -a "source /usr/share/doc/fzf/examples/completion.zsh" \
  -a "export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
  -x

# Install Claude
RUN npm install -g @anthropic-ai/claude-code

# Pre-create workspace structure and install project dependencies
WORKDIR /workspace
RUN mkdir -p src tests docs .claude scripts && \
    chown -R node:node /workspace

# Create a minimal pyproject.toml for dependency pre-installation
COPY --chown=node:node pyproject.toml uv.lock* ./
RUN /home/node/.cargo/bin/uv sync --frozen || true

# Copy and set up firewall script
COPY init-firewall.sh /usr/local/bin/
USER root
RUN chmod +x /usr/local/bin/init-firewall.sh && \
  echo "node ALL=(root) NOPASSWD: /usr/local/bin/init-firewall.sh" > /etc/sudoers.d/node-firewall && \
  chmod 0440 /etc/sudoers.d/node-firewall
USER node
