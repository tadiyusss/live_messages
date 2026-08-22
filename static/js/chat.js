function chat_app() {
	return {
		search: '',
		mobile_view: 'list',
		new_message: '',
		socketio: null,
		showUploadModal: false,
        selected_user: null,
        clients: [],
        connected: false,
        messages: [],
		scroll_to_bottom() {
			const el = this.$refs.messagesContainer;
			if (el) el.scrollTop = el.scrollHeight;
		},
        is_user_visible(name){
            if (this.search.trim() === '') {
                return true;
            }
            if (name.toLowerCase().includes(this.search.trim().toLowerCase())) {
                return true;
            }
            return false;
        },
        select_user(client_object){
            this.selected_user = client_object;
            this.mobile_view = 'chat';
            this.socketio.emit('get_history', { client_uuid: client_object.uuid });
            this.$nextTick(() => {
                this.scroll_to_bottom();
            });
        },
		init() {
			this.socketio = io();

			this.socketio.on('connect', () => {
				this.connected = true;
			});

			this.socketio.on('disconnect', () => {
				this.connected = false;
			});

            this.socketio.on('clients_data', (data) => {
                this.clients = [];
                for(row of data.clients){
                    this.clients.push(row);
                }
                console.log(this.clients)
            })

            this.socketio.on('get_history', (data) => {
                this.messages = [];
                for(row of data.messages){
                    this.messages.push(row);
                }
                this.$nextTick(() => {
                    this.scroll_to_bottom();
                });
            })
		}
	};
}