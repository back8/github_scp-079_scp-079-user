# SCP-079-USER - Invite and help other bots
# Copyright (C) 2019 SCP-079 <https://scp-079.org>
#
# This file is part of SCP-079-USER.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from time import sleep

from pyrogram import Client

from .. import glovar
from .channel import share_data
from .etc import code, general_link, thread
from .file import save
from .group import leave_group
from .telegram import get_admins, get_group_info, send_message

# Enable logging
logger = logging.getLogger(__name__)


def backup_files(client: Client) -> bool:
    # Backup data files to BACKUP
    try:
        for file in glovar.file_list:
            try:
                share_data(
                    client=client,
                    receivers=["BACKUP"],
                    action="backup",
                    action_type="pickle",
                    data=file,
                    file=f"data/{file}"
                )
                sleep(5)
            except Exception as e:
                logger.warning(f"Send backup file {file} error: {e}", exc_info=True)

        return True
    except Exception as e:
        logger.warning(f"Backup error: {e}", exc_info=True)

    return False


def interval_ten_min() -> bool:
    # Execute every 10 minutes
    try:
        # glovar.deleted_ids = {}
        glovar.recorded_ids = {}

        return True
    except Exception as e:
        logger.warning(f"Clear recorded ids error: {e}", exc_info=True)

    return False


def reset_data() -> bool:
    # Reset user data every month
    try:
        glovar.bad_ids = {
            "channels": set(),
            "users": set()
        }
        save("bad_ids")

        glovar.banned_ids = {}
        save("banned_ids")

        glovar.except_ids = {
            "temp": set()
        }
        save("except_ids")

        glovar.user_ids = {}
        save("user_ids")

        return True
    except Exception as e:
        logger.warning(f"Reset data error: {e}", exc_info=True)

    return False


def update_admins(client: Client) -> bool:
    # Update admin list every day
    group_list = list(glovar.admin_ids)
    for gid in group_list:
        try:
            should_leave = True
            admin_members = get_admins(client, gid)
            if admin_members and any([admin.user.is_self for admin in admin_members]):
                glovar.admin_ids[gid] = {admin.user.id for admin in admin_members
                                         if not admin.user.is_bot and not admin.user.is_deleted}
                for admin in admin_members:
                    if admin.user.is_self:
                        if (admin.permissions.can_delete_messages
                                and admin.permissions.can_restrict_members
                                and admin.permissions.can_invite_users
                                and admin.permissions.can_promote_members):
                            should_leave = False

                if should_leave:
                    group_name, group_link = get_group_info(client, gid)
                    share_data(
                        client=client,
                        receivers=["MANAGE"],
                        action="leave",
                        action_type="request",
                        data={
                            "group_id": gid,
                            "group_name": group_name,
                            "group_link": group_link,
                            "reason": "权限缺失"
                        }
                    )
                    debug_text = (f"项目编号：{general_link(glovar.project_name, glovar.project_link)}\n"
                                  f"群组名称：{general_link(group_name, group_link)}\n"
                                  f"群组 ID：{code(gid)}\n"
                                  f"状态：{code('权限缺失')}\n")
                    thread(send_message, (client, glovar.debug_channel_id, debug_text))
            elif admin_members is False or any([admin.user.is_self for admin in admin_members]) is False:
                # Bot is not in the chat, leave automatically without approve
                group_name, group_link = get_group_info(client, gid)
                leave_group(client, gid)
                share_data(
                    client=client,
                    receivers=["MANAGE"],
                    action="leave",
                    action_type="info",
                    data={
                        "group_id": gid,
                        "group_name": group_name,
                        "group_link": group_link
                    }
                )
                debug_text = (f"项目编号：{general_link(glovar.project_name, glovar.project_link)}\n"
                              f"群组名称：{general_link(group_name, group_link)}\n"
                              f"群组 ID：{code(gid)}\n"
                              f"状态：{code('自动退出并清空数据')}\n"
                              f"原因：{code('非管理员或已不在群组中')}\n")
                thread(send_message, (client, glovar.debug_channel_id, debug_text))
        except Exception as e:
            logger.warning(f"Update admin in {gid} error: {e}", exc_info=True)

    return True


def update_status(client: Client) -> bool:
    # Update running status to BACKUP
    try:
        share_data(
            client=client,
            receivers=["BACKUP"],
            action="backup",
            action_type="status",
            data="awake"
        )

        return True
    except Exception as e:
        logger.warning(f"Update status error: {e}", exc_info=True)

    return False
