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
				this.clients = data.clients;
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