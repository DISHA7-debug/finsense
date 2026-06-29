// =============================================
// FinSense AI Chat Module
// agent.js
// =============================================

import {
    startAgentConversation,
    sendAgentMessage
} from "./api.js";

let loanId = null;
let conversationId = null;

// DOM Elements
let chatWindow;
let inputBox;
let sendButton;
let quickReplies;

// =============================================
// Initialize Chat
// =============================================

export async function initializeAgent(id) {

    loanId = id;

    chatWindow = document.getElementById("chatWindow");
    inputBox = document.getElementById("chatInput");
    sendButton = document.getElementById("sendMessage");
    quickReplies = document.querySelectorAll(".quickReply");

    if (!chatWindow) return;

    attachEvents();

    await beginConversation();

}

// =============================================
// Event Listeners
// =============================================

function attachEvents() {

    sendButton?.addEventListener("click", sendCurrentMessage);

    inputBox?.addEventListener("keypress", (e) => {

        if (e.key === "Enter") {

            sendCurrentMessage();

        }

    });

    quickReplies.forEach(button => {

        button.addEventListener("click", () => {

            inputBox.value = button.innerText;

            sendCurrentMessage();

        });

    });

}

// =============================================
// Start Conversation
// =============================================

async function beginConversation() {

    try {

        showTyping();

        const response =
            await startAgentConversation(loanId);

        removeTyping();

        conversationId =
            response.conversation_id;

        addAgentMessage(response.message);

    }

    catch (error) {

        removeTyping();

        addAgentMessage(
            "Unable to connect to the FinSense AI service."
        );

        console.error(error);

    }

}

// =============================================
// Send Message
// =============================================

async function sendCurrentMessage() {

    const text = inputBox.value.trim();

    if (!text) return;

    addUserMessage(text);

    inputBox.value = "";

    showTyping();

    try {

        const response =
            await sendAgentMessage(

                loanId,

                conversationId,

                text

            );

        removeTyping();

        addAgentMessage(response.reply);

    }

    catch (error) {

        removeTyping();

        addAgentMessage(
            "Sorry, I couldn't understand that."
        );

        console.error(error);

    }

}

// =============================================
// Agent Bubble
// =============================================

function addAgentMessage(message) {

    const bubble = document.createElement("div");

    bubble.className = "flex mb-4";

    bubble.innerHTML = `

<div
class="chat-bubble-ai rounded-2xl rounded-tl-none p-4 shadow max-w-lg">

<div class="chat-bubble-ai-title mb-2">

🤖 FinSense AI

</div>

<div>

${message}

</div>

</div>

`;

    chatWindow.appendChild(bubble);

    scrollBottom();

}

// =============================================
// Borrower Bubble
// =============================================

function addUserMessage(message) {

    const bubble = document.createElement("div");

    bubble.className = "flex justify-end mb-4";

    bubble.innerHTML = `

<div
class="bg-white border rounded-2xl rounded-tr-none p-4 shadow max-w-lg">

<div class="font-semibold text-gray-700 mb-2">

👤 Borrower

</div>

<div>

${message}

</div>

</div>

`;

    chatWindow.appendChild(bubble);

    scrollBottom();

}

// =============================================
// Typing Animation
// =============================================

function showTyping() {

    const typing = document.createElement("div");

    typing.id = "typing";

    typing.className = "flex mb-4";

    typing.innerHTML = `

<div
class="chat-bubble-ai rounded-2xl rounded-tl-none px-5 py-4">

<div class="flex gap-2">

<div class="w-2 h-2 rounded-full typing-dot animate-bounce"></div>

<div class="w-2 h-2 rounded-full typing-dot animate-bounce"
style="animation-delay:.2s"></div>

<div class="w-2 h-2 rounded-full typing-dot animate-bounce"
style="animation-delay:.4s"></div>

</div>

</div>

`;

    chatWindow.appendChild(typing);

    scrollBottom();

}

// =============================================

function removeTyping() {

    const typing = document.getElementById("typing");

    if (typing) {

        typing.remove();

    }

}

// =============================================

function scrollBottom() {

    chatWindow.scrollTop =
        chatWindow.scrollHeight;

}