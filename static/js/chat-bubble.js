function chat_support() {
	return {
		socketio: null,
		open_chat_bubble: true,
		client_uuid: localStorage.getItem('client_uuid') || null,
		new_message: '',
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
		messages: [],
		open() {
			this.open_chat_bubble = true;
		},

		close() {
			this.open_chat_bubble = false;
		},

		start_chat() {
			console.log('Starting chat with data:', this.start_chat_form_data);
			this.socketio.emit('start_chat', this.start_chat_form_data);
		},

		send_message() {
			const text = this.new_message.trim();
			if (!text) return;
			this.socketio.emit('send_message', { client_uuid: this.client_uuid, content: text });
			this.new_message = '';
		},

		scroll_to_bottom() {
			this.$nextTick(() => {
				const el = this.$refs.messagesContainer;

				if (!el) {
					console.warn('Messages container not found. Cannot scroll to bottom.');
					return;
				}

				el.scrollTo({
					top: el.scrollHeight,
					behavior: 'smooth'
				});
			});
		},
		init(){
			this.socketio = io();

			this.socketio.on('connect', (data) => {
				if (this.client_uuid) {
					this.socketio.emit('validate_client_uuid', { client_uuid: this.client_uuid });
				}
			});

			this.socketio.on('validate_client_uuid', (data) => {
				if (data.success === false) {
					localStorage.removeItem('client_uuid');
					this.client_uuid = null;
				}
			})

			this.socketio.on('start_chat', (data) => {
				if (data.success === false) {
					this.start_chat_form_errors = data.errors;
				}
				this.client_uuid = data.client_uuid;
				localStorage.setItem('client_uuid', this.client_uuid);
			});

			this.socketio.on('send_message', (data) => {
				if (data.success === false) {
					console.error('Error sending message:', data.error);
					return;
				}
			})

			this.socketio.on('receive_message', (data) => {
				for (const msg of data.messages) {
					this.messages.push({
						uuid: msg.uuid,
						sender: msg.sender,
						text: msg.content,
						time: msg.time,
						name: msg.name,
					});
				}
				this.scroll_to_bottom();
			});
		}
	};
}