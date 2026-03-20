/**
 * @returns {string}
 */
function createSessionId() {
  return `session_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
}

/**
 * @returns {string}
 */
function nowStamp() {
  const d = new Date();
  const p = (v) => String(v).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}_${p(d.getHours())}-${p(d.getMinutes())}-${p(d.getSeconds())}`;
}

window.chatApp = function chatApp() {
  return {
    sessionId: createSessionId(),
    messages: [],
    input: "",
    processing: false,
    queueing: false,
    progressMessage: "",
    queueMessage: "You're in line...",
    theme: window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light",

    get canSend() {
      return this.input.trim().length > 0 && !this.processing && !this.queueing;
    },

    init() {
      const media = window.matchMedia("(prefers-color-scheme: dark)");
      media.addEventListener("change", (event) => {
        if (!localStorage.getItem("zelda_theme")) {
          this.theme = event.matches ? "dark" : "light";
        }
      });
      const saved = localStorage.getItem("zelda_theme");
      if (saved === "light" || saved === "dark") {
        this.theme = saved;
      }

      this.$watch('messages', () => {
        this.scrollToBottom();
      })
    },

    toggleTheme() {
      this.theme = this.theme === "dark" ? "light" : "dark";
      localStorage.setItem("zelda_theme", this.theme);
    },

    /**
     * @param {KeyboardEvent} event
     */
    onKeydown(event) {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        if (this.canSend) {
          this.sendMessage();
        }
      }
    },

    /**
     * @param {InputEvent} event
     */
    autoResize(event) {
      const target = /** @type {HTMLTextAreaElement} */ (event.target);
      target.style.height = "auto";
      const lineHeight = 24;
      const minHeight = lineHeight * 3;
      const maxHeight = lineHeight * 8;
      target.style.height = `${Math.max(minHeight, Math.min(target.scrollHeight, maxHeight))}px`;
    },

    scrollToBottom() {
      this.$nextTick(() => {
          const container = this.$refs.msgEl;
          if (container) {
              container.scrollTo({
                  top: container.scrollHeight,
                  behavior: 'smooth' // Scroll suave
              });
          }
      });
    },

    renderMarkdown(content) {
      return window.marked.parse(content || "");
    },

    async sendMessage() {
      if (!this.canSend) {
        return;
      }

      const messageText = this.input.trim();
      this.messages.push({ role: "user", content: messageText });
      this.input = "";
      const textArea = document.querySelector("#chatInput");
      if (textArea) {
        textArea.style.height = "auto";
      }
      this.scrollToBottom();

      await this.trySendWithQueue(messageText);
    },

    async trySendWithQueue(messageText) {
      this.processing = true;
      this.queueing = false;
      this.progressMessage = "Summoning Zelda wisdom...";

      while (true) {
        const response = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: this.sessionId, message: messageText }),
        });

        if (response.status === 429) {
          this.queueing = true;
          this.queueMessage = "You're in line... A sage will be with you shortly.";
          await new Promise((resolve) => setTimeout(resolve, 2200));
          continue;
        }

        this.queueing = false;

        if (!response.ok || !response.body) {
          this.messages.push({ role: "bot", content: "I hit an issue reaching the kingdom archives. Please try again." });
          this.processing = false;
          this.progressMessage = "";
          this.scrollToBottom();
          return;
        }

        await this.consumeSSE(response.body);
        return;
      }
    },

    async consumeSSE(body) {
      const decoder = new TextDecoder();
      const reader = body.getReader();
      let buffer = "";
      let botIndex = -1;

      this.messages.push({ role: "bot", content: "" });
      botIndex = this.messages.length - 1;

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          break;
        }
        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split("\n\n");
        buffer = chunks.pop() || "";

        for (const chunk of chunks) {
          const lines = chunk.split("\n");
          const eventLine = lines.find((line) => line.startsWith("event:"));
          const dataLines = lines.filter((line) => line.startsWith("data:"));
          if (!eventLine || dataLines.length === 0) {
            continue;
          }
          const eventName = eventLine.replace("event:", "").trim();
          const data = JSON.parse(dataLines.map((line) => line.slice(5)).join("\n")).text;

          if (eventName === "progress") {
            this.progressMessage = data;
          } else if (eventName === "token") {
            this.messages[botIndex].content += data;
            this.scrollToBottom();
          } else if (eventName === "done") {
            this.progressMessage = "";
            this.processing = false;
            this.scrollToBottom();
          } else if (eventName === "error") {
            this.messages[botIndex].content = `Error: ${data}`;
            this.processing = false;
            this.progressMessage = "";
            this.scrollToBottom();
          }
        }
      }

      this.processing = false;
      this.progressMessage = "";
    },

    downloadMarkdown() {
      if (this.messages.length === 0) {
        return;
      }
      const lines = ["# Zelda Chat Export", ""];
      for (const message of this.messages) {
        const role = message.role === "user" ? "User" : "Zelda Bot";
        lines.push(`## ${role}`);
        lines.push("");
        lines.push(message.content);
        lines.push("");
      }
      const blob = new Blob([lines.join("\n")], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `zelda_chat_${nowStamp()}.md`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    },
  };
};
