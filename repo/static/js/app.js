const stateScript = document.querySelector("#workspace-state");
const refreshButton = document.querySelector("[data-refresh-workspace]");

function parseEmbeddedState() {
  if (!stateScript || !stateScript.textContent) {
    return null;
  }

  try {
    return JSON.parse(stateScript.textContent);
  } catch (_error) {
    return null;
  }
}

function setPressedState(event) {
  const button = event.currentTarget;
  button.classList.add("is-pressed");
  window.setTimeout(() => button.classList.remove("is-pressed"), 140);
}

function applyWorkspaceState(state) {
  if (!state) {
    return;
  }

  const sourceNode = document.querySelector("[data-current-source]");
  const targetNode = document.querySelector("[data-current-target]");
  const led = document.querySelector("[data-status-led]");
  if (sourceNode) {
    sourceNode.textContent = state.currentSourceDocument?.originalFilename ?? "No resume uploaded yet";
  }
  if (targetNode) {
    targetNode.textContent = state.currentJobTarget?.roleTitle ?? "No job target yet";
  }
  if (led) {
    led.lastElementChild.textContent = state.currentSourceDocument ? "Workspace Synced" : "Workspace Ready";
  }
}

async function refreshWorkspaceState() {
  const response = await fetch("/api/workspace/current", {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error("Unable to refresh workspace state.");
  }
  const state = await response.json();
  applyWorkspaceState(state);
}

document.querySelectorAll(".tactile-button").forEach((button) => {
  button.addEventListener("click", setPressedState);
});

if (refreshButton) {
  refreshButton.addEventListener("click", async () => {
    try {
      await refreshWorkspaceState();
    } catch (_error) {
      const led = document.querySelector("[data-status-led]");
      if (led) {
        led.lastElementChild.textContent = "Refresh Failed";
      }
    }
  });
}

applyWorkspaceState(parseEmbeddedState());