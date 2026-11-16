document.addEventListener("DOMContentLoaded", () => {
    const chatContainer = document.getElementById("chat-container");
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const passkeyInput = document.getElementById("passkey-input");
    const savePasskeyBtn = document.getElementById("save-passkey");

    if (sessionStorage.getItem("demo_passkey")) {
        passkeyInput.value = sessionStorage.getItem("demo_passkey");
    }

    savePasskeyBtn.addEventListener("click", () => {
        sessionStorage.setItem("demo_passkey", passkeyInput.value.trim());
        alert("Passkey saved to session.");
    });

    let sessionMacros = { calories: 0.0, protein_g: 0.0, carbs_g: 0.0, fat_g: 0.0, fiber_g: 0.0 };

    function renderFormattedMarkdown(container, markdownText) {
        const html = markdownText
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-white">$1</strong>')
            .split("\n")
            .map((line) => {
                const trimmed = line.trim();
                if (trimmed.startsWith("### ")) {
                    return `<h3 class="text-base font-semibold text-emerald-400 mt-4 mb-1.5 first:mt-0">${trimmed.slice(4)}</h3>`;
                }
                if (line.startsWith("  - ") || line.startsWith("    - ")) {
                    return `<div class="pl-8 text-slate-300 my-0.5">◦ ${trimmed.slice(2)}</div>`;
                }
                if (trimmed.startsWith("- ")) {
                    return `<div class="pl-4 text-slate-200 my-1">• ${trimmed.slice(2)}</div>`;
                }
                return trimmed ? `<p class="my-1.5 leading-relaxed text-slate-200">${trimmed}</p>` : "";
            })
            .join("");

        container.innerHTML = html;
    }

    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const message = userInput.value.trim();
        const passkey = passkeyInput.value.trim() || sessionStorage.getItem("demo_passkey") || "";

        if (!message) return;

        appendMessage(message, "user");
        userInput.value = "";

        const assistantBubble = appendMessage("Initializing Agentic RAG pipeline...", "assistant", true);
        const traceBox = assistantBubble.querySelector(".trace-box");
        const contentBox = assistantBubble.querySelector(".content-box");

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Demo-Passkey": passkey
                },
                body: JSON.stringify({ message: message, running_macros: sessionMacros })
            });

            if (!response.ok) {
                const errData = await response.json();
                contentBox.textContent = `Error: ${errData.detail || "Unauthorized or rate limited"}`;
                return;
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";
            let latestMealMacros = null;

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n\n");
                buffer = lines.pop();

                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        const jsonStr = line.replace("data: ", "");
                        const data = JSON.parse(jsonStr);

                        if (data.error) {
                            contentBox.textContent = `Error: ${data.error}`;
                            break;
                        }

                        if (data.node) {
                            const traceItem = document.createElement("div");
                            traceItem.className = "text-xs text-emerald-400 font-mono my-1";
                            traceItem.textContent = `⚙️ Executed Node: [${data.node}]`;
                            traceBox.appendChild(traceItem);

                            if (data.node === "generate" && data.output && data.output.generation) {
                                renderFormattedMarkdown(contentBox, data.output.generation);

                                if (data.output.running_macros) {
                                    latestMealMacros = data.output.running_macros;
                                }

                                if (data.output.documents && data.output.documents.length > 0) {
                                    const existingSourceBox = assistantBubble.querySelector(".source-box");
                                    if (existingSourceBox) existingSourceBox.remove();

                                    const sourceBox = document.createElement("div");
                                    sourceBox.className = "source-box mt-4 pt-3 border-t border-slate-800 text-xs text-slate-400";

                                    const listItems = data.output.documents.map((d) => {
                                        const meta = d.metadata || {};
                                        const foodName = meta.food_name || "Web Result";
                                        const source = String(meta.source || "Local DB");
                                        const page = meta.page || meta.page_number;

                                        if (source.startsWith("http://") || source.startsWith("https://")) {
                                            return `<li>${foodName} (<a href="${source}" target="_blank" rel="noopener noreferrer" class="text-emerald-400 underline hover:text-emerald-300">${source}</a>)</li>`;
                                        } else {
                                            const pageText = page ? ` - Page ${page}` : "";
                                            return `<li>${foodName} (${source} PDF${pageText})</li>`;
                                        }
                                    }).join("");

                                    sourceBox.innerHTML = `<strong class="text-slate-300 block mb-1">Sources:</strong><ul class="list-disc pl-5 space-y-1">${listItems}</ul>`;
                                    assistantBubble.appendChild(sourceBox);
                                }
                            }
                        }
                    }
                }
            }

            if (latestMealMacros) {
                sessionMacros.calories += latestMealMacros.calories || 0;
                sessionMacros.protein_g += latestMealMacros.protein_g || 0;
                sessionMacros.carbs_g += latestMealMacros.carbs_g || 0;
                sessionMacros.fat_g += latestMealMacros.fat_g || 0;
                sessionMacros.fiber_g += latestMealMacros.fiber_g || 0;

                document.getElementById("macro-cal").textContent = Math.round(sessionMacros.calories);
                document.getElementById("macro-pro").textContent = Math.round(sessionMacros.protein_g);
                document.getElementById("macro-carb").textContent = Math.round(sessionMacros.carbs_g);
                document.getElementById("macro-fat").textContent = Math.round(sessionMacros.fat_g);
                document.getElementById("macro-fiber").textContent = Math.round(sessionMacros.fiber_g);
            }
        } catch (err) {
            contentBox.textContent = `Connection Error: ${err.message}`;
        }
    });

    function appendMessage(text, sender, isAgent = false) {
        const bubble = document.createElement("div");
        bubble.className = `p-4 rounded-xl border max-w-2xl ${sender === "user" ? "bg-slate-900 border-slate-800 ml-auto text-right" : "bg-slate-900/80 border-slate-800 mr-auto"}`;

        if (isAgent) {
            bubble.innerHTML = `
                <div class="trace-box bg-slate-950 p-2 rounded mb-3 border border-slate-800/80 max-h-32 overflow-y-auto"></div>
                <div class="content-box text-sm text-slate-200">${text}</div>
            `;
        } else {
            bubble.innerHTML = `<p class="text-sm text-slate-200">${text}</p>`;
        }

        chatContainer.appendChild(bubble);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return bubble;
    }
});