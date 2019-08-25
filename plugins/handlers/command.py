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
import re
from time import time
from copy import deepcopy

from pyrogram import Client, Filters, Message

from .. import glovar
from ..functions.channel import get_debug_text, share_data
from ..functions.etc import bold, code, code_block, get_command_context, get_command_type, get_int, thread, user_mention
from ..functions.file import save
from ..functions.filters import is_class_c, test_group
from ..functions.group import delete_message
from ..functions.telegram import get_group_info, send_message, send_report_message
from ..functions.user import resolve_username

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group
                   & Filters.command(["config"], glovar.prefix))
def config(client: Client, message: Message):
    # Request CONFIG session
    try:
        gid = message.chat.id
        mid = message.message_id
        # Check permission
        if is_class_c(None, message):
            # Check command format
            command_type = get_command_type(message)
            if command_type and re.search("^user$", command_type, re.I):
                now = int(time())
                # Check the config lock
                if now - glovar.configs[gid]["lock"] > 310:
                    # Set lock
                    glovar.configs[gid]["lock"] = now
                    # Ask CONFIG generate a config session
                    group_name, group_link = get_group_info(client, message.chat)
                    share_data(
                        client=client,
                        receivers=["CONFIG"],
                        action="config",
                        action_type="ask",
                        data={
                            "project_name": glovar.project_name,
                            "project_link": glovar.project_link,
                            "group_id": gid,
                            "group_name": group_name,
                            "group_link": group_link,
                            "user_id": message.from_user.id,
                            "config": glovar.configs[gid],
                            "default": glovar.default_config
                        }
                    )
                    # Send a report message to debug channel
                    text = get_debug_text(client, message.chat)
                    text += (f"群管理：{code(message.from_user.id)}\n"
                             f"操作：{code('创建设置会话')}\n")
                    thread(send_message, (client, glovar.debug_channel_id, text))

        thread(delete_message, (client, gid, mid))
    except Exception as e:
        logger.warning(f"Config error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group
                   & Filters.command(["config_user"], glovar.prefix))
def config_user(client: Client, message: Message):
    # Config the bot directly
    try:
        gid = message.chat.id
        mid = message.message_id
        # Check permission
        if is_class_c(None, message):
            aid = message.from_user.id
            success = True
            reason = "已更新"
            new_config = deepcopy(glovar.configs[gid])
            text = f"管理员：{code(aid)}\n"
            # Check command format
            command_type, command_context = get_command_context(message)
            if command_type:
                now = int(time())
                # Check the config lock
                if now - new_config["lock"] > 310:
                    if command_type == "show":
                        text += (f"操作：{code('查看设置')}\n"
                                 f"设置：{code((lambda x: '默认' if x else '自定义')(new_config.get('default')))}\n"
                                 f"订阅名单：{code((lambda x: '启用' if x else '禁用')(new_config.get('channel')))}\n")
                        thread(send_report_message, (15, client, gid, text))
                        thread(delete_message, (client, gid, mid))
                        return
                    elif command_type == "default":
                        if not new_config.get("default"):
                            new_config = deepcopy(glovar.default_config)
                    else:
                        if command_context:
                            if command_type == "subscribe":
                                if command_context == "off":
                                    new_config["subscribe"] = False
                                elif command_context == "on":
                                    new_config["subscribe"] = True
                                else:
                                    success = False
                                    reason = "订阅选项有误"
                            elif command_type == "dafm":
                                if command_context == "off":
                                    new_config["dafm"] = False
                                elif command_context == "on":
                                    new_config["dafm"] = True
                                else:
                                    success = False
                                    reason = "自助选项有误"
                            else:
                                success = False
                                reason = "命令类别有误"
                        else:
                            success = False
                            reason = "命令选项缺失"

                        if success:
                            new_config["default"] = False
                else:
                    success = False
                    reason = "设置当前被锁定"
            else:
                success = False
                reason = "格式有误"

            if success and new_config != glovar.configs[gid]:
                glovar.configs[gid] = new_config
                save("configs")

            text += (f"操作：{code('更改设置')}\n"
                     f"状态：{code(reason)}\n")
            thread(send_report_message, ((lambda x: 10 if x else 5)(success), client, gid, text))

        thread(delete_message, (client, gid, mid))
    except Exception as e:
        logger.warning(f"Config error: {e}", exc_info=True)


# @Client.on_message(Filters.incoming & Filters.group
#                    & Filters.command(["dafm"], glovar.prefix))
# def dafm(client, message):
#     try:
#         gid = message.chat.id
#         mid = message.message_id
#         if init_group_id(gid):
#             if glovar.configs[gid]["dafm"] or is_class_c(None, message):
#                 uid = message.from_user.id
#                 command_list = list(filter(None, message.command))
#                 if len(command_list) == 2 and command_list[1] == "yes":
#                     if uid not in glovar.deleted_ids[gid]:
#                         # Forward the request command message as evidence
#                         result = forward_evidence(client, message, "自助删除", "群组自定义")
#                         if result:
#                             glovar.deleted_ids[gid].add(uid)
#                             thread(delete_all_messages, (client, gid, uid))
#                             send_debug(client, message.chat, "自助删除", uid, mid, result)
#
#         thread(delete_message, (client, gid, mid))
#     except Exception as e:
#         logger.warning(f"DAFM error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & test_group
                   & Filters.command(["mention"], glovar.prefix))
def mention(client: Client, message: Message):
    # Mention a user
    try:
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        text = f"管理员：{user_mention(aid)}\n\n"
        uid = 0
        id_text = get_command_type(message)
        the_type = ""
        if id_text:
            uid = get_int(id_text)
            if not uid:
                the_type, the_id = resolve_username(client, id_text)
                if the_type == "user":
                    uid = the_id
        elif message.reply_to_message.forward_from:
            uid = message.reply_to_message.forward_from.id

        if uid:
            if the_type:
                text += f"查询用户：{code(uid)}\n"
            else:
                text += f"查询用户：{user_mention(uid)}\n"
        else:
            text += f"错误：{code('缺少用户参数')}\n"

        thread(send_message, (client, cid, text, mid))
    except Exception as e:
        logger.warning(f"Mention error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & test_group
                   & Filters.command(["print"], glovar.prefix))
def print_message(client: Client, message: Message):
    # Print a message
    try:
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        if message.reply_to_message:
            result = str(message.reply_to_message).replace("pyrogram.", "")
            result = re.sub('"phone_number": ".*?"', '"phone_number": "███████████"', result)
            result_list = [result[i:i + 3000] for i in range(0, len(result), 3000)]
            for result in result_list:
                text = (f"管理员：{user_mention(aid)}\n\n"
                        f"消息结构：" + "-" * 24 + "\n\n"
                        f"{code_block(result)}\n")
                send_message(client, cid, text, mid)
    except Exception as e:
        logger.warning(f"Print message error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & test_group
                   & Filters.command(["version"], glovar.prefix))
def version(client: Client, message: Message):
    # Check the program's version
    try:
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        text = (f"管理员：{user_mention(aid)}\n\n"
                f"版本：{bold(glovar.version)}\n")
        thread(send_message, (client, cid, text, mid))
    except Exception as e:
        logger.warning(f"Version error: {e}", exc_info=True)
