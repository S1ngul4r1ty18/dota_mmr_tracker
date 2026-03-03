from pathlib import Path

from litestar import Litestar
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.template.config import TemplateConfig

from utils import create_templates
from services import init_main_db
from routes import (
    login_page, login_steam, login_steam_callback, logout,
    setup_mmr_page, process_setup_mmr, process_calibrate, dashboard, update_match,
    matches_page, match_detail_page, records_page, heroes_page, superadmin_dashboard,
    img_hero, img_item, admin_audit_user, admin_export_user, profile_page,
    admin_login_page, admin_login_post, admin_change_pwd_page, admin_change_pwd_post
)

create_templates()
init_main_db()

template_config = TemplateConfig(
    directory=Path("templates"),
    engine=JinjaTemplateEngine,
)

app = Litestar(
    route_handlers=[
        login_page,
        login_steam,
        login_steam_callback,
        logout,
        setup_mmr_page,
        process_setup_mmr,
        process_calibrate,
        dashboard,
        profile_page,
        update_match,
        matches_page,
        match_detail_page,
        records_page,
        heroes_page,
        superadmin_dashboard,
        img_hero,
        img_item,
        admin_audit_user,
        admin_export_user,
        admin_login_page,
        admin_login_post,
        admin_change_pwd_page,
        admin_change_pwd_post
    ],
    template_config=template_config,
    debug=True
)