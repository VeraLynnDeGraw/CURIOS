
const $ = (selector) => document.querySelector(selector);

const state = {
  providers: [],
  activeId: null,
  messages: [],
  online: false,
  chatPending: false,
  networkPending: false
};

const dialog = $("#provider-dialog");
const form = $("#provider-form");
const networkToggle = $("#network-toggle");

const toast = (message) => {
  const node = $("#toast");
  node.textContent = message;
  node.classList.add("show");
  setTimeout(() => node.classList.remove("show"), 2600);
};

async function api(path, data) {
  const response = await fetch(path, {
    method: data ? "POST" : "GET",
    headers: data
      ? { "Content-Type": "application/json" }
      : {},
    body: data ? JSON.stringify(data) : undefined
  });

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.error || `Request failed (${response.status})`
    );
  }

  return result;
}

/* =========================================
   NETWORK STATE
========================================= */

function renderNetworkState(online) {
  state.online = online;

  const status = $("#network-status");
  const label = $("#network-label");

  networkToggle.dataset.state = online ? "online" : "offline";
  networkToggle.setAttribute("aria-pressed", String(online));

  networkToggle.setAttribute(
    "aria-label",
    online
      ? "Network is online. Activate to go offline."
      : "Network is offline. Activate to go online."
  );

  networkToggle.title = online
    ? "Disconnect CURIOS"
    : "Activate network connections";

  status.dataset.state = online ? "online" : "offline";
  label.textContent = online ? "ONLINE" : "OFFLINE";

  updateComposer();
  updateNetworkButton();
}

function updateNetworkButton() {
  networkToggle.disabled =
    state.chatPending || state.networkPending;

  if (state.chatPending) {
    networkToggle.title =
      "Wait for the active provider request to finish.";
  } else if (state.networkPending) {
    networkToggle.title = "Changing network state…";
  } else {
    networkToggle.title = state.online
      ? "Disconnect CURIOS"
      : "Activate network connections";
  }
}

async function loadNetworkState() {
  const result = await api("/api/network");

  if (typeof result.online !== "boolean") {
    throw new Error("Invalid network state received from CURIOS.");
  }

  renderNetworkState(result.online);
}

networkToggle.addEventListener("click", async () => {
  if (state.chatPending || state.networkPending) return;

  const nextState = !state.online;

  if (nextState) {
    const approved = confirm(
      "Activate ONLINE mode?\n\n" +
      "CURIOS will be permitted to connect to configured providers " +
      "and external services.\n\n" +
      "Conversation content sent to a provider may leave this computer."
    );

    if (!approved) return;
  }

  state.networkPending = true;
  updateNetworkButton();

  try {
    const result = await api("/api/network", {
      online: nextState
    });

    renderNetworkState(result.online);

    toast(
      result.online
        ? "CURIOS is ONLINE."
        : "CURIOS is OFFLINE."
    );
  } catch (error) {
    toast(`Network change failed: ${error.message}`);
  } finally {
    state.networkPending = false;
    updateNetworkButton();
  }
});

/* =========================================
   PROVIDERS
========================================= */

function renderProviders() {
  const list = $("#provider-list");
  list.replaceChildren();

  if (!state.providers.length) {
    const empty = document.createElement("p");
    empty.className = "muted small";
    empty.textContent = "No providers configured.";
    list.append(empty);
  }

  for (const provider of state.providers) {
    const wrap = document.createElement("div");

    const button = document.createElement("button");
    button.className =
      `provider-item ${
        provider.id === state.activeId ? "active" : ""
      }`;

    const name = document.createElement("strong");
    name.textContent = provider.name;

    const model = document.createElement("span");
    model.textContent = provider.model;

    button.append(name, model);
    button.addEventListener("click", () => {
      selectProvider(provider.id);
    });

    wrap.append(button);

    const actions = document.createElement("div");
    actions.className = "provider-actions";

    const remove = document.createElement("button");
    remove.textContent = "Remove";

    remove.addEventListener("click", async () => {
      if (!confirm(`Remove ${provider.name}?`)) return;

      try {
        await api("/api/providers/remove", {
          id: provider.id
        });

        if (state.activeId === provider.id) {
          state.activeId = null;
          state.messages = [];

          renderMessages();
          updateComposer();
        }

        await loadProviders();
      } catch (error) {
        toast(error.message);
      }
    });

    actions.append(remove);
    wrap.append(actions);
    list.append(wrap);
  }
}

function selectProvider(id) {
  state.activeId = id;
  state.messages = [];

  const provider = state.providers.find(
    item => item.id === id
  );

  $("#active-provider").textContent =
    provider?.name || "Choose a connection";

  $("#model-label").textContent =
    provider?.model || "No model selected";

  renderProviders();
  renderMessages();
  updateComposer();
}

function updateComposer() {
  const ready = Boolean(state.activeId);
  const input = $("#message-input");
  const send = $("#send-button");
  const hint = $("#composer-hint");

  input.disabled = !ready;

  send.disabled =
    !ready || !state.online || state.chatPending;

  input.placeholder = ready
    ? "Write a message…"
    : "Choose a provider to begin…";

  if (!ready) {
    hint.textContent = "Select a connection first";
  } else if (!state.online) {
    hint.textContent =
      "CURIOS is OFFLINE · Activate the moon to connect";
  } else if (state.chatPending) {
    hint.textContent = "Waiting for the provider…";
  } else {
    hint.textContent =
      "Enter to send · Shift+Enter for a new line";
  }
}

async function loadProviders() {
  const result = await api("/api/providers");

  state.providers = result.providers;

  if (
    state.activeId &&
    !state.providers.some(p => p.id === state.activeId)
  ) {
    state.activeId = null;
  }

  renderProviders();
}

/* =========================================
   MESSAGES
========================================= */

function renderMessages() {
  const area = $("#messages");
  area.replaceChildren();

  if (!state.messages.length) {
    const welcome = document.createElement("div");
    welcome.className = "welcome";

    const symbol = document.createElement("div");
    symbol.className = "welcome-symbol";
    symbol.textContent = "✳";

    const heading = document.createElement("h2");
    heading.textContent = "A little room for big questions.";

    const paragraph = document.createElement("p");

    paragraph.textContent = state.activeId
      ? "Your conversation starts here. What would you like to explore?"
      : "Add an API connection, choose a model, and start a conversation.";

    welcome.append(symbol, heading, paragraph);
    area.append(welcome);

    return;
  }

  for (const message of state.messages) {
    const bubble = document.createElement("div");
    bubble.className = `message ${message.role}`;

    const role = document.createElement("div");
    role.className = "role";
    role.textContent =
      message.role === "user" ? "YOU" : "ASSISTANT";

    const content = document.createElement("div");
    content.textContent = message.content;

    bubble.append(role, content);
    area.append(bubble);
  }

  area.scrollTop = area.scrollHeight;
}

/* =========================================
   PROVIDER DIALOG
========================================= */

$("#add-provider").addEventListener("click", () => {
  dialog.showModal();
});

$("#close-dialog").addEventListener("click", () => {
  dialog.close();
});

$("#cancel-dialog").addEventListener("click", () => {
  dialog.close();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const data = Object.fromEntries(
    new FormData(form).entries()
  );

  try {
    await api("/api/providers", data);

    dialog.close();
    form.reset();

    await loadProviders();

    const id = data.name
      .toLowerCase()
      .replace(/[^a-z0-9_-]/g, "-")
      .replace(/^-|-$/g, "") || "provider";

    const saved = state.providers.find(
      p => p.id === id
    );

    if (saved) {
      selectProvider(saved.id);
    }

    toast("Connection saved locally.");
  } catch (error) {
    toast(error.message);
  }
});

/* =========================================
   CHAT
========================================= */

$("#chat-form").addEventListener("submit", async (event) => {
  event.preventDefault();

  const input = $("#message-input");
  const content = input.value.trim();

  if (!content || !state.activeId) return;

  if (!state.online) {
    toast("CURIOS is OFFLINE. No provider connection was made.");
    return;
  }

  if (state.chatPending) return;

  state.chatPending = true;
  updateComposer();
  updateNetworkButton();

  state.messages.push({
    role: "user",
    content
  });

  input.value = "";
  renderMessages();

  try {
    const result = await api("/api/chat", {
      provider_id: state.activeId,
      messages: state.messages
    });

    state.messages.push({
      role: "assistant",
      content: result.reply
    });
  } catch (error) {
    state.messages.push({
      role: "assistant",
      content: `Connection error: ${error.message}`
    });
  } finally {
    state.chatPending = false;

    renderMessages();
    updateComposer();
    updateNetworkButton();

    input.focus();
  }
});

$("#message-input").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    $("#chat-form").requestSubmit();
  }
});

/* =========================================
   APPLICATION STARTUP
========================================= */

async function initialize() {
  try {
    await Promise.all([
      loadNetworkState(),
      loadProviders()
    ]);

    updateComposer();
  } catch (error) {
    toast(`Startup error: ${error.message}`);
  }
}

initialize();

/* =========================================
   SHUTDOWN
========================================= */

$("#power-off").addEventListener("click", async () => {
  if (
    !confirm(
      "Shut down CURIOS and close the dedicated browser session?"
    )
  ) {
    return;
  }

  $("#power-off").disabled = true;
  $("#power-off").textContent = "Shutting down…";

  try {
    await api("/api/shutdown", {});

    document.body.innerHTML =
      '<main style="min-height:100vh;display:grid;place-items:center;background:#111216;color:#eee;font-family:system-ui;text-align:center"><div><h1>CURIOS is off.</h1><p style="color:#999">The local server is shutting down. You can close this tab if it remains open.</p></div></main>';
  } catch (error) {
    toast(error.message);

    $("#power-off").disabled = false;
    $("#power-off").textContent = "Power off";
  }
});
