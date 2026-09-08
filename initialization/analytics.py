from core.utils.registry.analytics import register_analytics, register_analytics_item
from core.utils.analytics import Grid, MediumAnalyticsCardData, SmallAnalyticsCardData
from ..utils.analytics import get_active_live_chat_client_count, get_unread_messages_count, unaccepted_live_chat_clients_count
from flask_login import current_user

ANALYTICS_ITEMS = [
    MediumAnalyticsCardData(
        title="Unread Messages",
        value_function=lambda: get_unread_messages_count(current_user),
        roles=["Administrator", "Support Agent"],
        icon="<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='currentColor' class='fd-analytics-card-icon'><path fill-rule='evenodd' d='M1 8.74c0 .983.713 1.825 1.69 1.943.904.108 1.817.19 2.737.243.363.02.688.231.85.556l1.052 2.103a.75.75 0 0 0 1.342 0l1.052-2.103c.162-.325.487-.535.85-.556.92-.053 1.833-.134 2.738-.243.976-.118 1.689-.96 1.689-1.942V4.259c0-.982-.713-1.824-1.69-1.942a44.45 44.45 0 0 0-10.62 0C1.712 2.435 1 3.277 1 4.26v4.482Zm3-3.49a.75.75 0 0 1 .75-.75h6.5a.75.75 0 0 1 0 1.5h-6.5A.75.75 0 0 1 4 5.25ZM4.75 7a.75.75 0 0 0 0 1.5h2.5a.75.75 0 0 0 0-1.5h-2.5Z' clip-rule='evenodd' /></svg>",
        subtitle="Number of unread messages on your live messages clients.",
    ),
]

DEFAULT_ANALYTICS_GRID = [
    Grid(
        title="Live Messages",
        contents=[
            SmallAnalyticsCardData(
                "Active Live Chat Clients",
                value_function=lambda: get_active_live_chat_client_count(current_user),
                roles=["Administrator", "Support Agent"],
                icon="<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='currentColor' class='fd-analytics-card-icon'><path d='M1 8.849c0 1 .738 1.851 1.734 1.947L3 10.82v2.429a.75.75 0 0 0 1.28.53l1.82-1.82A3.484 3.484 0 0 1 5.5 10V9A3.5 3.5 0 0 1 9 5.5h4V4.151c0-1-.739-1.851-1.734-1.947a44.539 44.539 0 0 0-8.532 0C1.738 2.3 1 3.151 1 4.151V8.85Z' /><path d='M7 9a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v1a2 2 0 0 1-2 2h-.25v1.25a.75.75 0 0 1-1.28.53L9.69 12H9a2 2 0 0 1-2-2V9Z' /></svg>"
            ),
            SmallAnalyticsCardData(
                "Unaccepted Live Chat Clients",
                value_function=lambda: unaccepted_live_chat_clients_count(),
                roles=["Administrator", "Support Agent"],
                icon="<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='currentColor' class='fd-analytics-card-icon'><path fill-rule='evenodd' d='M1 8c0-3.43 3.262-6 7-6s7 2.57 7 6-3.262 6-7 6c-.423 0-.838-.032-1.241-.094-.9.574-1.941.948-3.06 1.06a.75.75 0 0 1-.713-1.14c.232-.378.395-.804.469-1.26C1.979 11.486 1 9.86 1 8Z' clip-rule='evenodd' /></svg>"
            )
        ],
        roles=["*"],
    )
]

def initialize_analytics():
    for item in ANALYTICS_ITEMS:
        register_analytics_item(item, "Dashboard Analytics")
    for item in DEFAULT_ANALYTICS_GRID:
        register_analytics(item)