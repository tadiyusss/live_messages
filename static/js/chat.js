function chat_app() {
	return {
		search: '',
		mobile_view: 'list',
		new_message: '',
		socket: null,
		show_upload_modal: false,
		selected_client: null,
		clients: [],
		connected: false,
		messages: [],

		scroll_to_bottom() {
			const el = this.$refs.messagesContainer;
			if (el) el.scrollTop = el.scrollHeight;
		},

		is_client_visible(name) {
			const query = this.search.trim().toLowerCase();
			if (!query) return true;
			return name.toLowerCase().includes(query);
		},

		select_client(client) {
			this.selected_client = client;
			client.unread_count = 0;
			this.mobile_view = 'chat';
			this.socket.emit('get_history', { client_uuid: client.uuid });
			this.$nextTick(() => {
				this.scroll_to_bottom();
			});
		},

		send_message() {
			const text = this.new_message.trim();
			if (!text || !this.selected_client) return;
			this.socket.emit('send_message', { client_uuid: this.selected_client.uuid, content: text });
			this.new_message = '';
		},

		init() {
			this.socket = io();

			this.socket.on('connect', () => {
				this.connected = true;
			});

			this.socket.on('disconnect', () => {
				this.connected = false;
			});

			this.socket.on('clients_data', (data) => {
				this.clients = data.clients.map((client) => ({ ...client, unread_count: 0 }));
			});

			this.socket.on('sidebar_update', (data) => {
				const updated_client = data.client;
				const existing_client = this.clients.find((client) => client.uuid === updated_client.uuid);
				if (!existing_client) {
					this.clients.unshift({ ...updated_client, unread_count: 0 });
					return;
				}
				existing_client.last_message = updated_client.last_message;
				const is_viewing = this.selected_client && this.selected_client.uuid === updated_client.uuid;
				if (data.message_sender === 'client' && !is_viewing) {
					existing_client.unread_count += 1;
				}
			});

			this.socket.on('get_history', (data) => {
				if (data.success === false) {
					console.error('Error loading message history:', data.error);
					return;
				}
				this.messages = data.messages;
				this.$nextTick(() => {
					this.scroll_to_bottom();
				});
			});

			this.socket.on('send_message', (data) => {
				if (data.success === false) {
					console.error('Error sending message:', data.error);
					return;
				}
				for (const message of data.messages) {
					if (this.selected_client && message.client_uuid === this.selected_client.uuid) {
						this.messages.push(message);
					}
				}
				this.$nextTick(() => {
					this.scroll_to_bottom();
				});
			});
		}
	};
}