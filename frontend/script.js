document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    
    const sessionId = `session-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
    console.log('Session ID:', sessionId);

    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(sender === 'user' ? 'user-message' : 'system-message');
        messageDiv.textContent = text;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    async function sendMessage() {
        const query = userInput.value.trim();
        if (query === '') return;

        addMessage(query, 'user');
        userInput.value = ''; 

        try {
            const apiUrl = 'http://localhost:8000/chat';

            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    query: query, 
                    session_id: sessionId
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Erro ao comunicar com a API do agente.');
            }

            const data = await response.json();
            addMessage(data.answer, 'system'); 
        } catch (error) {
            console.error('Erro ao enviar mensagem:', error);
            addMessage('Desculpe, houve um erro ao processar sua solicitação. Tente novamente mais tarde.', 'system');
        }
    }

    async function clearHistory() {
        try {
            const response = await fetch(`http://localhost:8000/chat/history/${sessionId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                chatBox.innerHTML = '';
                console.log('Histórico limpo com sucesso');
            }
        } catch (error) {
            console.error('Erro ao limpar histórico:', error);
        }
    }

    async function loadHistory() {
        try {
            const response = await fetch(`http://localhost:8000/chat/history/${sessionId}`);
            
            if (response.ok) {
                const data = await response.json();
                
                chatBox.innerHTML = '';
                
                for (const msg of data.messages) {
                    const sender = msg.type === 'human' ? 'user' : 'system';
                    addMessage(msg.content, sender);
                }
            }
        } catch (error) {
            console.error('Erro ao carregar histórico:', error);
        }
    }

    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });

    const debugDiv = document.createElement('div');
    debugDiv.innerHTML = `
        <button onclick="clearHistory()" style="margin: 5px; padding: 5px 10px; background: #ff4444; color: white; border: none; border-radius: 3px;">
            Limpar Histórico
        </button>
        <button onclick="loadHistory()" style="margin: 5px; padding: 5px 10px; background: #4444ff; color: white; border: none; border-radius: 3px;">
            Carregar Histórico
        </button>
        <small style="display: block; margin: 5px; color: #666;">Session ID: ${sessionId}</small>
    `;

    window.clearHistory = clearHistory;
    window.loadHistory = loadHistory;
});