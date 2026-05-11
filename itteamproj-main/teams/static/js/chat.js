import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';

// IMPORTANT: Replace with actual Supabase project keys to work
const supabaseUrl = 'https://YOUR_SUPABASE_URL.supabase.co';
const supabaseKey = 'YOUR_SUPABASE_ANON_KEY';

// Initialize Supabase only if valid URL is provided
let supabase;
if (supabaseUrl !== 'https://YOUR_SUPABASE_URL.supabase.co') {
    supabase = createClient(supabaseUrl, supabaseKey);
}

// UI Elements mapping
const chatContainer = document.getElementById('chat-messages');
const messageInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-msg-btn');

// Mock data context
const currentUserId = 'user-1';
const activeChatId = 'chat-workspace-1';

/**
 * Appends a message bubble dynamically to the chat interface.
 * Implements a "Glassy" chat design.
 */
export function appendMessage(message, isMe) {
    if (!chatContainer) return;
    
    // Create outermost wrapper
    const wrapper = document.createElement('div');
    // Align appropriately based on sender
    wrapper.className = `flex flex-col mb-4 w-full animate-[slideUpFade_0.3s_ease-out] ${isMe ? 'items-end' : 'items-start'}`;
    
    // Create the message bubble with glassmorphism logic
    const bubble = document.createElement('div');
    let extraClasses = isMe 
        ? 'bg-[#0070f3]/90 backdrop-blur-md border border-[#00f0ff]/20 text-white rounded-br-none shadow-[0_4px_20px_rgba(0,112,243,0.3)]' 
        : 'glass-card border border-white/10 text-gray-200 rounded-bl-none shadow-sm';
        
    bubble.className = `px-4 py-3 rounded-2xl max-w-[75%] relative ${extraClasses}`;
    
    // Sender label
    const sender = document.createElement('span');
    sender.className = `text-[10px] uppercase font-bold tracking-wider mb-1 block opacity-80 ${isMe ? 'text-cyan-100' : 'text-accent-cyan'}`;
    sender.innerText = isMe ? 'Ви' : message.sender;
    
    // Actual text content
    const text = document.createElement('p');
    text.className = 'text-sm leading-relaxed';
    text.innerText = message.content;
    
    // Append children
    bubble.appendChild(sender);
    bubble.appendChild(text);
    wrapper.appendChild(bubble);
    chatContainer.appendChild(wrapper);
    
    // Auto-scroll logic targeting the bottom
    chatContainer.scrollTo({
        top: chatContainer.scrollHeight,
        behavior: 'smooth'
    });
}

// Example usage to populate initial state if no messages
if (chatContainer && chatContainer.children.length === 0) {
    appendMessage({ sender: 'Nexus Team', content: 'Привіт! Ми готові обговорити ваш проєкт. Які основні вимоги до бази даних?' }, false);
}

/**
 * Handles payload submission
 */
async function handleSend() {
    if (!messageInput || !messageInput.value.trim()) return;
    
    const content = messageInput.value.trim();
    messageInput.value = ''; // clear field immediately
    
    // Optimistic Append (update UI without waiting for server response)
    appendMessage({ sender: 'Ви', content: content }, true);
    
    // Real Supabase Insertion
    if (supabase) {
        try {
            const { error } = await supabase.from('messages').insert([
                { user_id: currentUserId, content: content, chat_id: activeChatId }
            ]);
            if (error) {
                console.error("Помилка відправки:", error);
                // In a real app, you'd show a toast error here
            }
        } catch (e) {
            console.error(e);
        }
    } else {
        console.warn("Supabase is not configured. Message simulated.");
    }
}

// Bind Events
if (sendBtn) {
    sendBtn.addEventListener('click', handleSend);
}

if (messageInput) {
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSend();
    });
}

// Real-time subscription to the PostgreSQL database table
if (supabase) {
    supabase.channel('public:messages')
        .on('postgres_changes', { 
            event: 'INSERT', 
            schema: 'public', 
            table: 'messages',
            filter: `chat_id=eq.${activeChatId}`
        }, payload => {
            const newMsg = payload.new;
            // Validate it's from the other person to avoid duplicate from optimistic UI
            if (newMsg.user_id !== currentUserId) {
                // Determine sender name based on real app logic; hardcoded here
                appendMessage({ sender: 'Співрозмовник', content: newMsg.content }, false);
            }
        })
        .subscribe();
}
