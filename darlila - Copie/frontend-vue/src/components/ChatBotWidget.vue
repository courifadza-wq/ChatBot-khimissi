<script setup>
import { ref, nextTick, onMounted } from 'vue'

// Proxy PHP sur Hostinger (même domaine = pas de CORS)
const CHAT_URL = '/chat-proxy.php'

// Session persistante (localStorage)
function getSessionId() {
  let sid = localStorage.getItem('pk_chat_session')
  if (!sid) {
    sid = crypto.randomUUID()
    localStorage.setItem('pk_chat_session', sid)
  }
  return sid
}

const isOpen    = ref(false)
const messages  = ref([])
const inputText = ref('')
const isLoading = ref(false)
const messagesEl = ref(null)
const inputEl    = ref(null)

// Message de bienvenue
onMounted(() => {
  messages.value.push({
    from: 'bot',
    text: '👋 Bonjour ! Je suis l\'assistant de **Planète Kids**.\n\nJe peux vous aider à :\n📂 Chercher des produits\n🛒 Passer une commande\n🚚 Infos livraison\n💳 Modes de paiement\n\nQue puis-je faire pour vous ?',
  })
})

function toggle() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    nextTick(() => {
      scrollToBottom()
      inputEl.value?.focus()
    })
  }
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return

  messages.value.push({ from: 'user', text })
  inputText.value = ''
  isLoading.value = true
  await nextTick()
  scrollToBottom()

  try {
    const res = await fetch(CHAT_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, session_id: getSessionId() }),
    })
    const data = await res.json()
    messages.value.push({ from: 'bot', text: data.reply || '😕 Pas de réponse.' })
  } catch {
    messages.value.push({ from: 'bot', text: '😕 Connexion impossible. Réessayez dans un moment.' })
  } finally {
    isLoading.value = false
    await nextTick()
    scrollToBottom()
    inputEl.value?.focus()
  }
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

function scrollToBottom() {
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

// Formate *gras* et sauts de ligne
function formatText(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}
</script>

<template>
  <!-- Bulle flottante -->
  <button
    class="chat-fab"
    :class="{ open: isOpen }"
    @click="toggle"
    aria-label="Ouvrir le chat"
  >
    <!-- Icône chat (fermé) -->
    <svg v-if="!isOpen" viewBox="0 0 24 24" fill="currentColor" class="fab-icon">
      <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/>
    </svg>
    <!-- Icône X (ouvert) -->
    <svg v-else viewBox="0 0 24 24" fill="currentColor" class="fab-icon">
      <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
    </svg>
    <span class="fab-label" v-if="!isOpen">Chat</span>
  </button>

  <!-- Panneau de chat -->
  <Transition name="chat-slide">
    <div v-if="isOpen" class="chat-panel">
      <!-- Header -->
      <div class="chat-header">
        <div class="chat-avatar">🛍️</div>
        <div class="chat-title">
          <span class="chat-name">Assistant Planète Kids</span>
          <span class="chat-status">● En ligne</span>
        </div>
        <button class="chat-close" @click="toggle" aria-label="Fermer">✕</button>
      </div>

      <!-- Messages -->
      <div class="chat-messages" ref="messagesEl">
        <div
          v-for="(msg, i) in messages"
          :key="i"
          class="chat-bubble-wrap"
          :class="msg.from"
        >
          <div class="chat-bubble" v-html="formatText(msg.text)"></div>
        </div>

        <!-- Indicateur de frappe -->
        <div v-if="isLoading" class="chat-bubble-wrap bot">
          <div class="chat-bubble typing">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>

      <!-- Input -->
      <div class="chat-input-row">
        <input
          ref="inputEl"
          v-model="inputText"
          type="text"
          class="chat-input"
          placeholder="Votre message..."
          @keydown="onKeydown"
          :disabled="isLoading"
          maxlength="500"
        />
        <button
          class="chat-send"
          @click="sendMessage"
          :disabled="isLoading || !inputText.trim()"
          aria-label="Envoyer"
        >
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
          </svg>
        </button>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
/* ── Bulle flottante ─────────────────────────────────────────── */
.chat-fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 20px;
  background: linear-gradient(135deg, #ea2f90, #2d3590);
  color: #fff;
  border: none;
  border-radius: 50px;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(234, 47, 144, 0.4);
  font-family: 'Quicksand', sans-serif;
  font-weight: 700;
  font-size: 15px;
  transition: transform 0.2s, box-shadow 0.2s;
}
.chat-fab:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 24px rgba(234, 47, 144, 0.5);
}
.chat-fab.open {
  padding: 14px;
  border-radius: 50%;
}
.fab-icon {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
}
.fab-label {
  white-space: nowrap;
}

/* ── Panneau chat ────────────────────────────────────────────── */
.chat-panel {
  position: fixed;
  bottom: 90px;
  right: 24px;
  z-index: 9998;
  width: min(380px, calc(100vw - 48px));
  height: min(520px, calc(100vh - 120px));
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 8px 40px rgba(45, 53, 144, 0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font-family: 'Quicksand', sans-serif;
}

/* Header */
.chat-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 18px;
  background: linear-gradient(135deg, #2d3590, #ea2f90);
  color: #fff;
  flex-shrink: 0;
}
.chat-avatar {
  font-size: 28px;
  background: rgba(255,255,255,0.2);
  border-radius: 50%;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.chat-title {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.chat-name {
  font-weight: 700;
  font-size: 14px;
}
.chat-status {
  font-size: 11px;
  opacity: 0.85;
  color: #a8f5a8;
}
.chat-close {
  background: none;
  border: none;
  color: #fff;
  font-size: 18px;
  cursor: pointer;
  opacity: 0.8;
  padding: 4px;
  line-height: 1;
}
.chat-close:hover { opacity: 1; }

/* Messages */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: #f7f8fc;
  scroll-behavior: smooth;
}
.chat-bubble-wrap {
  display: flex;
}
.chat-bubble-wrap.bot {
  justify-content: flex-start;
}
.chat-bubble-wrap.user {
  justify-content: flex-end;
}
.chat-bubble {
  max-width: 78%;
  padding: 10px 14px;
  border-radius: 18px;
  font-size: 13.5px;
  line-height: 1.55;
  word-break: break-word;
}
.chat-bubble-wrap.bot .chat-bubble {
  background: #fff;
  color: #2d3590;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.chat-bubble-wrap.user .chat-bubble {
  background: linear-gradient(135deg, #ea2f90, #c0196e);
  color: #fff;
  border-bottom-right-radius: 4px;
}

/* Typing indicator */
.typing {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 12px 16px;
}
.typing span {
  width: 7px;
  height: 7px;
  background: #2d3590;
  border-radius: 50%;
  animation: bounce 1.2s infinite;
  opacity: 0.7;
}
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-6px); }
}

/* Input */
.chat-input-row {
  display: flex;
  gap: 8px;
  padding: 12px 14px;
  border-top: 1px solid #eee;
  background: #fff;
  flex-shrink: 0;
}
.chat-input {
  flex: 1;
  border: 1.5px solid #e0e0e0;
  border-radius: 24px;
  padding: 10px 16px;
  font-size: 13.5px;
  font-family: 'Quicksand', sans-serif;
  outline: none;
  transition: border-color 0.2s;
}
.chat-input:focus {
  border-color: #2d3590;
}
.chat-send {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #ea2f90, #2d3590);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: opacity 0.2s, transform 0.15s;
}
.chat-send:disabled {
  opacity: 0.4;
  cursor: default;
}
.chat-send:not(:disabled):hover {
  transform: scale(1.1);
}
.chat-send svg {
  width: 18px;
  height: 18px;
  fill: #fff;
}

/* ── Animation slide ─────────────────────────────────────────── */
.chat-slide-enter-active,
.chat-slide-leave-active {
  transition: opacity 0.25s, transform 0.25s;
}
.chat-slide-enter-from,
.chat-slide-leave-to {
  opacity: 0;
  transform: translateY(16px) scale(0.97);
}

/* Mobile */
@media (max-width: 480px) {
  .chat-panel {
    bottom: 0;
    right: 0;
    width: 100vw;
    height: 70vh;
    border-radius: 20px 20px 0 0;
  }
  .chat-fab {
    bottom: 16px;
    right: 16px;
  }
}
</style>
