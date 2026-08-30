function chat_support() {
	return {
		socket: null,
		open_chat_bubble: false,
		client_uuid: localStorage.getItem('client_uuid') || null,
		new_message: '',
		connected: false,
		start_chat_form_data: {
			fullname: '',
			email: '',
			phone_number: '',
		},
		start_chat_form_errors: {},
		messages: [],

		open() {
			this.open_chat_bubble = true;
		},

		close() {
			this.open_chat_bubble = false;
		},

		start_chat() {
			this.socket.emit('new-client', this.start_chat_form_data);
		},

		send_message() {
			const text = this.new_message.trim();
			if (!text) return;
			this.socket.emit('send_message', { client_uuid: this.client_uuid, content: text });
			this.new_message = '';
		},

		format_message(message) {
			return {
				uuid: message.uuid,
				sender: message.sender,
				text: message.content,
				time: message.created_at,
				name: message.name,
				content_type: message.content_type,
				content: message.content,
				content_name: message.content_name,
			};
		},

		scroll_to_bottom() {
			this.$nextTick(() => {
				const el = this.$refs.messagesContainer;
				if (!el) return;
				el.scrollTo({
					top: el.scrollHeight,
					behavior: 'smooth'
				});
			});
		},

		init() {
			this.socket = io();

			this.socket.on('connect', () => {
				this.connected = true;
				if (this.client_uuid) {
					this.socket.emit('validate-client-uuid', { client_uuid: this.client_uuid });
				}
			});

			this.socket.on('disconnect', () => {
				this.connected = false;
			});

			this.socket.on('validate-client-uuid', (data) => {
				if (data.success === false) {
					localStorage.removeItem('client_uuid');
					this.client_uuid = null;
					this.messages = [];
				}
			});

			this.socket.on('new-client', (data) => {
				if (data.success === false) {
					this.start_chat_form_errors = data.errors;
					return;
				}
				this.client_uuid = data.client.uuid;
				localStorage.setItem('client_uuid', this.client_uuid);
			});

			this.socket.on('get-history', (data) => {
				if (data.success === false) {
					console.error('Error loading message history:', data.error);
					return;
				}
				this.messages = data.messages.map(this.format_message);
				this.scroll_to_bottom();
			});

			this.socket.on('send_message', (data) => {
				if (data.success === false) {
					console.error('Error sending message:', data.error);
					this.new_message = data.message;
					return;
				}
				this.messages.push(...data.messages.map(this.format_message));
				this.scroll_to_bottom();
			});
		}
	};
}