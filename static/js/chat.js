function chat_app() {
	return {
		search: '',
		mobile_view: 'list',
		new_message: '',
		socket: null,
		show_upload_modal: false,
		selected_file: null,
		uploading_file: false,
		selected_client: null,
		clients: [],
		connected: false,
		messages: [],
		new_clients: [],
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
			this.socket.emit('get-history', { client_uuid: client.uuid });
			this.$nextTick(() => {
				this.scroll_to_bottom();
			});
		},

		send_message() {
			const text = this.new_message.trim();
			if (!text || !this.selected_client) return;
			this.socket.emit('send-message', { client_uuid: this.selected_client.uuid, content: text });
			this.new_message = '';
		},

		handle_file_selected(event) {
			this.selected_file = event.target.files.length > 0 ? event.target.files[0] : null;
		},

		clear_selected_file() {
			this.selected_file = null;
			const input = this.$refs.file_input;
			if (input) input.value = '';
		},

		format_file_size(size) {
			if (size >= 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(1)} MB`;
			if (size >= 1024) return `${(size / 1024).toFixed(1)} KB`;
			return `${size} B`;
		},

		async upload_file() {
			if (!this.selected_file || !this.selected_client || this.uploading_file) return;
			this.uploading_file = true;
			try {
				const form_data = new FormData();
				form_data.append('client_uuid', this.selected_client.uuid);
				form_data.append('file', this.selected_file);
				const response = await fetch('/api/live-messages/upload', { method: 'POST', body: form_data });
				const data = await response.json();
				if (data.success === false) {
					console.error('Error uploading file:', data.error);
					return;
				}
				this.clear_selected_file();
				this.show_upload_modal = false;
			} finally {
				this.uploading_file = false;
			}
		},
		accept_client(client_uuid) {
			this.socket.emit('accept-client', { client_uuid: client_uuid });
		},

		init() {
			this.socket = io();

			this.socket.on('connect', () => {
				this.connected = true;
			});

			this.socket.on('disconnect', () => {
				this.connected = false;
			});

			this.socket.on('unaccommodated-clients', (data) => {
				new_clients = data.clients;
				if (new_clients.length > 0) {
					this.new_clients = new_clients;
				}
			})

			this.socket.on('new-client', (data) => {
				client = data.client;
				if (!this.new_clients.some(c => c.uuid === client.uuid) && !this.clients.some(c => c.uuid === client.uuid)) {
					this.new_clients.unshift(client);
				}
			})

			this.socket.on('client-assigned', (data) => {
				const client = data.client;
				this.new_clients = this.new_clients.filter(c => c.uuid !== client.uuid);
			})

			this.socket.on('accept-client', (data) => {
				if (data.success === false) {
					alert(`Error accepting client: ${data.error}`);
				}

				client = data.client
				this.new_clients = this.new_clients.filter(c => c.uuid !== client.uuid);
				if (!this.clients.some(c => c.uuid === client.uuid)) {
					this.clients.unshift(client);
				}
			});

			this.socket.on('clients-data', (data) => {
				this.clients = data.clients;
			});

			this.socket.on('sidebar_update', (data) => {
				const updated_client = data.client;
				const existing_client = this.clients.find((client) => client.uuid === updated_client.uuid);
				if (!existing_client) {
					this.clients.unshift(updated_client);
					return;
				}
				existing_client.last_message = updated_client.last_message;
				existing_client.unread_count = updated_client.unread_count;
			});

			this.socket.on('get-history', (data) => {
				if (data.success === false) {
					console.error('Error loading message history:', data.error);
					return;
				}
				this.messages = data.messages;
				this.$nextTick(() => {
					this.scroll_to_bottom();
				});
			});

			this.socket.on('sidebar-update', (data) => {
				const updated_client = data.client;
				const existing_client = this.clients.find((client) => client.uuid === updated_client.uuid);
				if (!existing_client) {
					this.clients.unshift(updated_client);
					return;
				}
				existing_client.last_message = updated_client.last_message;
				existing_client.unread_count = updated_client.unread_count;
			})

			this.socket.on('send-message', (data) => {
				if (data.success === false) {
					console.error('Error sending message:', data.error);
					return;
				}

				if (this.selected_client && this.selected_client.uuid === data.message.client_uuid) {
					this.messages.push(data.message);
					this.$nextTick(() => {
						this.scroll_to_bottom();
					});
				}
			});
		}
	};
}