from flask_login import login_required
from core.utils.decorators import roles_required
from .. import bp
from flask import render_template, Response, url_for, redirect
from ..models import LiveChatClient
from core.extensions import db
    
@bp.route('/dashboard/live-messages/')
@login_required
@roles_required(['Administrator', 'Support Agent'])
def messages():
    clients = LiveChatClient.query.all()
    return render_template('dashboard/messages.html', clients=clients)

@bp.route('/dashboard/live-messages/leads/download')
@login_required
@roles_required(['Administrator'])
def download_leads():
    leads = LiveChatClient.query.all()
    headers = ['Full Name', 'Email', 'Phone Number']
    data = [[lead.fullname, lead.email, lead.phone_number] for lead in leads]
    return Response(
        '\n'.join([','.join(headers)] + [','.join(map(str, row)) for row in data]),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=leads.csv'}
    )