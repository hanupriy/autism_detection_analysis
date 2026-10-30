// Form validation script
(function () {
    'use strict'
  
    // Fetch all the forms we want to apply custom Bootstrap validation styles to
    var forms = document.querySelectorAll('.needs-validation')
  
    // Loop over them and prevent submission
    Array.prototype.slice.call(forms)
      .forEach(function (form) {
        form.addEventListener('submit', function (event) {
          if (!form.checkValidity()) {
            event.preventDefault()
            event.stopPropagation()
          } else {
            // Show loading state on button before submitting
            const btn = form.querySelector('button[type="submit"]');
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Analyzing Data...';
            btn.classList.add('disabled');
          }
  
          form.classList.add('was-validated')
        }, false)
      })

    // Chatbot functionality
    const chatBtn = document.getElementById('chatbotBtn');
    if (chatBtn) {
        const chatPanel = document.getElementById('chatbotPanel');
        const chatClose = document.getElementById('chatbotClose');
        const chatInput = document.getElementById('chatInput');
        const chatSubmit = document.getElementById('chatSubmit');
        const chatHistory = document.getElementById('chatHistory');

        // Toggle chat panel
        chatBtn.addEventListener('click', () => {
            chatPanel.style.display = chatPanel.style.display === 'flex' ? 'none' : 'flex';
        });

        chatClose.addEventListener('click', () => {
            chatPanel.style.display = 'none';
        });

        // Send message function
        const sendMessage = async () => {
            const message = chatInput.value.trim();
            if (!message) return;

            // Add user message to UI
            addMessageToUI(message, 'user');
            chatInput.value = '';

            try {
                // Determine base URL dynamically (helps if app isn't at root)
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });

                const data = await response.json();
                addMessageToUI(data.reply, 'bot');
            } catch (error) {
                console.error("Chat error:", error);
                addMessageToUI("Sorry, I'm having trouble connecting to the server.", 'bot');
            }
        };

        const addMessageToUI = (text, sender) => {
            const msgDiv = document.createElement('div');
            msgDiv.classList.add('chat-msg', sender === 'user' ? 'chat-user' : 'chat-bot');
            msgDiv.innerText = text;
            chatHistory.appendChild(msgDiv);
            chatHistory.scrollTop = chatHistory.scrollHeight;
        };

        // Event listeners for sending
        chatSubmit.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
})()
