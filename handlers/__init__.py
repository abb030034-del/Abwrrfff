# ============================================================
# Group Manager Bot
# Author: LearningBotsOfficial (https://github.com/LearningBotsOfficial)
# Support: https://t.me/LearningBotsCommunity
# Channel: https://t.me/learning_bots
# YouTube: https://youtube.com/@learning_bots
# License: Open-source (keep credits, no resale)
# ============================================================

from .start import register_handlers
from .group_commands import register_group_commands
from .repo import register_repo_handler
from .filters_handler import register_filters_handler
from .fun_handler import register_fun_handler
from .info_handler import register_info_handler
from .rules_handler import register_rules_handler
from .quran_handler import register_quran_handler
from .whisper_handler import register_whisper_handler
from .sarhni_handler import register_sarhni_handler


def register_all_handlers(app):
    # Order matters when handlers share the same Pyrogram group.
    # Sarhni intercepts /start in group=-1; register it BEFORE start handlers.
    register_sarhni_handler(app)

    # Core handlers
    register_handlers(app)
    register_repo_handler(app)
    register_group_commands(app)

    # Feature handlers
    register_info_handler(app)
    register_rules_handler(app)
    register_filters_handler(app)
    register_fun_handler(app)
    register_quran_handler(app)
    register_whisper_handler(app)

    print("✅ All handlers registered!")
