function chat_support() {
	return {
		socketio: null,
		open_chat_bubble: true,
		client_uuid: localStorage.getItem('client_uuid') || null,
		newMessage: '',
		start_chat_form_data: {
			fullname: '',
			email: '',
			phone_number: '',
		},
		start_chat_form_errors: {},
		userInfo: {
			name: '',
			email: '',
			subject: '',
		},
		messages: [{
				id: 1,
				sender: 'support',
				text: 'Hi there! Welcome to our support chat. How can we help you today?',
				time: '10:30 AM'
			},
			{
				id: 2,
				sender: 'user',
				text: 'I have a question about my account.',
				time: '10:31 AM'
			},
			{
				id: 3,
				sender: 'support',
				text: 'Of course! I\'d be happy to help. What seems to be the issue?',
				time: '10:32 AM'
			},
		],

		open() {
			this.open_chat_bubble = true;
		},

		close() {
			this.open_chat_bubble = false;
		},

		start_chat() {
			this.socketio.emit('start_chat', this.start_chat_form_data);
		},

		sendMessage() {
			const text = this.newMessage.trim();
			if (!text) return;

			this.messages.push({
				id: Date.now(),
				sender: 'user',
				text,
				time: new Date().toLocaleTimeString([], {
					hour: 'numeric',
					minute: '2-digit'
				}),
			});
			this.newMessage = '';
			this.$nextTick(() => this.scrollToBottom());

			// mock reply
			setTimeout(() => {
				const replies = [
					'Got it! Let me help you with that.',
					'Thank you for reaching out. We\'ll assist you shortly.',
					'I understand. Let me look into this for you.',
					'No problem! I\'m here to help.',
					'That\'s a great question. Let me check our system.',
				];
				const reply = replies[Math.floor(Math.random() * replies.length)];
				this.messages.push({
					id: Date.now() + 1,
					sender: 'support',
					text: reply,
					time: new Date().toLocaleTimeString([], {
						hour: 'numeric',
						minute: '2-digit'
					}),
				});
				this.$nextTick(() => this.scrollToBottom());
			}, 1000);
		},

		scrollToBottom() {
			const el = this.$refs.messagesContainer;
			if (el) el.scrollTop = el.scrollHeight;
		},
		init(){
			this.socketio = io();

			this.socketio.on('connect', () => {
				if (this.client_uuid) {
					this.socketio.emit('history', { client_uuid: this.client_uuid });
				}
			});

			this.socketio.on('start_chat', (data) => {
				console.log('Received start_chat event:', data);
				if (data.status === "error") {
					this.start_chat_form_errors = data.errors || {};
				} else if (data.status === "success") {
					this.start_chat_form_errors = {};
					this.client_uuid = data.client_uuid;
					localStorage.setItem('client_uuid', data.client_uuid);
				}
			});
		}
	};
}