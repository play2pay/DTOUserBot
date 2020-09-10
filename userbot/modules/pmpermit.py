# Copyright (C) 2020 TeamDerUntergang.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

""" Özəl mesaj icazə modulu. """

from telethon.tl.functions.contacts import BlockRequest, UnblockRequest
from telethon.tl.functions.messages import ReportSpamRequest
from telethon.tl.types import User
from sqlalchemy.exc import IntegrityError

from userbot import (COUNT_PM, CMD_HELP, BOTLOG, BOTLOG_CHATID,
                     PM_AUTO_BAN, LASTMSG, LOGS)
from userbot.events import register

# ========================= CONSTANTS ============================
UNAPPROVED_MSG = ("`Salam mən DTÖUserBot.\n\n`"
                  "`Sahibim sizin mesaj göndərmənizə icazə verməyib. `"
                  "`Zəhmət olmasa çoxlu mesaj göndərməyin əks təqdirdə blok olunacaqsız :).\n\n`")
# =================================================================


@register(incoming=True, disable_edited=True, disable_errors=True)
async def permitpm(event):
    """ PM Blok İcazə/İcazə verməmək. """
    if PM_AUTO_BAN:
        self_user = await event.client.get_me()
        if event.is_private and event.chat_id != 777000 and event.chat_id != self_user.id and not (
                await event.get_sender()).bot:
            try:
                from userbot.modules.sql_helper.pm_permit_sql import is_approved
                from userbot.modules.sql_helper.globals import gvarstatus
            except AttributeError:
                return
            apprv = is_approved(event.chat_id)
            notifsoff = gvarstatus("NOTIF_OFF")

            # Bu bölüm basitçe akıl sağlığı kontrolüdür.
            # Eğer mesaj daha önceden onaylanmamış olarak gönderildiyse
            # flood yapmayı önlemek için unapprove mesajı göndermeyi durdurur.
            if not apprv and event.text != UNAPPROVED_MSG:
                if event.chat_id in LASTMSG:
                    prevmsg = LASTMSG[event.chat_id]
                    # Eğer önceden gönderilmiş mesaj farklıysa unapprove mesajı tekrardan gönderilir.
                    if event.text != prevmsg:
                        async for message in event.client.iter_messages(
                                event.chat_id,
                                from_user='me',
                                search=UNAPPROVED_MSG):
                            await message.delete()
                        await event.reply(UNAPPROVED_MSG)
                    LASTMSG.update({event.chat_id: event.text})
                else:
                    await event.reply(UNAPPROVED_MSG)
                    LASTMSG.update({event.chat_id: event.text})

                if notifsoff:
                    await event.client.send_read_acknowledge(event.chat_id)
                if event.chat_id not in COUNT_PM:
                    COUNT_PM.update({event.chat_id: 1})
                else:
                    COUNT_PM[event.chat_id] = COUNT_PM[event.chat_id] + 1

                if COUNT_PM[event.chat_id] > 4:
                    await event.respond(
                        "`Sən mənim PM'mi spamlayırsan, buda mənim xoşuma getmir.`\n"
                        "`İndi DTÖUserBot Tərəfindən BLOKLANDIN və SPAM olaraq işarətləndin, gələcəydə dəyişiklik olmadığı vaxta qədər..`"
                    )

                    try:
                        del COUNT_PM[event.chat_id]
                        del LASTMSG[event.chat_id]
                    except KeyError:
                        if BOTLOG:
                            await event.client.send_message(
                                BOTLOG_CHATID,
                                "PM sayğacı beyni gedib zəhmət olmasa botu yenidən başladın.",
                            )
                        LOGS.info(
                            "PM sayğacı beyni gedib zəhmət olmasa yenidən başladın.")
                        return

                    await event.client(BlockRequest(event.chat_id))
                    await event.client(ReportSpamRequest(peer=event.chat_id))

                    if BOTLOG:
                        name = await event.client.get_entity(event.chat_id)
                        name0 = str(name.first_name)
                        await event.client.send_message(
                            BOTLOG_CHATID,
                            "[" + name0 + "](tg://user?id=" +
                            str(event.chat_id) + ")" +
                            " istifadəçi kefimi pozdu. PM'ni məşğul etdiyi üçün bloklandı.",
                        )


@register(disable_edited=True, outgoing=True, disable_errors=True)
async def auto_accept(event):
    """ İlk mesaj yazan sizsizsə avtomatik icazə verər. """
    if not PM_AUTO_BAN:
        return
    self_user = await event.client.get_me()
    if event.is_private and event.chat_id != 777000 and event.chat_id != self_user.id and not (
            await event.get_sender()).bot:
        try:
            from userbot.modules.sql_helper.pm_permit_sql import is_approved
            from userbot.modules.sql_helper.pm_permit_sql import approve
        except AttributeError:
            return

        chat = await event.get_chat()
        if isinstance(chat, User):
            if is_approved(event.chat_id) or chat.bot:
                return
            async for message in event.client.iter_messages(event.chat_id,
                                                            reverse=True,
                                                            limit=1):
                if message.message is not UNAPPROVED_MSG and message.from_id == self_user.id:
                    try:
                        approve(event.chat_id)
                    except IntegrityError:
                        return

                if is_approved(event.chat_id) and BOTLOG:
                    await event.client.send_message(
                        BOTLOG_CHATID,
                        "#AVTOMATIK-İCAZE\n" + "İstifadəçisi: " +
                        f"[{chat.first_name}](tg://user?id={chat.id})",
                    )


@register(outgoing=True, pattern="^.notifoff$")
async def notifoff(noff_event):
    """ .notifoff . """
    try:
        from userbot.modules.sql_helper.globals import addgvar
    except AttributeError:
        await noff_event.edit("`Bot Non-SQL modunda çalışıyor!!`")
        return
    addgvar("NOTIF_OFF", True)
    await noff_event.edit("`PM icazəsi olmayan istifadəçilərin bildirişləri səssizə alındı!`")


@register(outgoing=True, pattern="^.notifon$")
async def notifon(non_event):
    """ .notifon . """
    try:
        from userbot.modules.sql_helper.globals import delgvar
    except:
        await non_event.edit("`Bot Non-SQL modunda işdəyir!!`")
        return
    delgvar("NOTIF_OFF")
    await non_event.edit("`PM icazəsi olmayan istifadəçilərin bildirə göndərməsinə icazə verildi!`")


@register(outgoing=True, pattern="^.approve$")
async def approvepm(apprvpm):
    """ .approve əmri mesaj göndərməyə icazə verər. """
    try:
        from userbot.modules.sql_helper.pm_permit_sql import approve
    except:
        await apprvpm.edit("`Bot Non-SQL modunda işdəyir!!`")
        return

    if apprvpm.reply_to_msg_id:
        reply = await apprvpm.get_reply_message()
        replied_user = await apprvpm.client.get_entity(reply.from_id)
        aname = replied_user.id
        name0 = str(replied_user.first_name)
        uid = replied_user.id

    else:
        aname = await apprvpm.client.get_entity(apprvpm.chat_id)
        name0 = str(aname.first_name)
        uid = apprvpm.chat_id

    try:
        approve(uid)
    except IntegrityError:
        await apprvpm.edit("`İstifadəçi hal-hazırda mesaj göndərə bilir | DTÖUserBot`")
        return

    await apprvpm.edit(f"[{name0}](tg://user?id={uid}) `istifadəçisi artıq sizə mesaj göndərə bilər!`")

    async for message in apprvpm.client.iter_messages(apprvpm.chat_id,
                                                      from_user='me',
                                                      search=UNAPPROVED_MSG):
        await message.delete()

    if BOTLOG:
        await apprvpm.client.send_message(
            BOTLOG_CHATID,
            "#İCAZEVERİLDİ\n" + "İstifadəçi: " + f"[{name0}](tg://user?id={uid})",
        )


@register(outgoing=True, pattern="^.disapprove$")
async def disapprovepm(disapprvpm):
    try:
        from userbot.modules.sql_helper.pm_permit_sql import dissprove
    except:
        await disapprvpm.edit("`Bot Non-SQL modunda işdəyir!!`")
        return

    if disapprvpm.reply_to_msg_id:
        reply = await disapprvpm.get_reply_message()
        replied_user = await disapprvpm.client.get_entity(reply.from_id)
        aname = replied_user.id
        name0 = str(replied_user.first_name)
        dissprove(replied_user.id)
    else:
        dissprove(disapprvpm.chat_id)
        aname = await disapprvpm.client.get_entity(disapprvpm.chat_id)
        name0 = str(aname.first_name)

    await disapprvpm.edit(
        f"[{name0}](tg://user?id={disapprvpm.chat_id}) `istifadəçisi artıq sizə mesaj göndərə bilməz.`")

    if BOTLOG:
        await disapprvpm.client.send_message(
            BOTLOG_CHATID,
            f"[{name0}](tg://user?id={disapprvpm.chat_id})"
            " istifadəçisinin mesaj atmaq icazəsi silindi.",
        )


@register(outgoing=True, pattern="^.block$")
async def blockpm(block):
    """ .block əmri insanları bloklayar. """
    if block.reply_to_msg_id:
        reply = await block.get_reply_message()
        replied_user = await block.client.get_entity(reply.from_id)
        aname = replied_user.id
        name0 = str(replied_user.first_name)
        await block.client(BlockRequest(replied_user.id))
        await block.edit("`Bloklandın!`")
        uid = replied_user.id
    else:
        await block.client(BlockRequest(block.chat_id))
        aname = await block.client.get_entity(block.chat_id)
        await block.edit("`Bloklandın!`")
        name0 = str(aname.first_name)
        uid = block.chat_id

    try:
        from userbot.modules.sql_helper.pm_permit_sql import dissprove
        dissprove(uid)
    except:
        pass

    if BOTLOG:
        await block.client.send_message(
            BOTLOG_CHATID,
            "#BLOKLANDI\n" + "İstifadəçi: " + f"[{name0}](tg://user?id={uid})",
        )


@register(outgoing=True, pattern="^.unblock$")
async def unblockpm(unblock):
    """ .unblock əmri blokdan çıxarar. """
    if unblock.reply_to_msg_id:
        reply = await unblock.get_reply_message()
        replied_user = await unblock.client.get_entity(reply.from_id)
        name0 = str(replied_user.first_name)
        await unblock.client(UnblockRequest(replied_user.id))
        await unblock.edit("`Blokdan çıxarıldı.`")

    if BOTLOG:
        await unblock.client.send_message(
            BOTLOG_CHATID,
            f"[{name0}](tg://user?id={replied_user.id})"
            " istifadəçisi blokdan çıxarıldı.",
        )


CMD_HELP.update({
    "pmpermit":
    "\
.approve\
\nİşlədilişi: Cavab verilən istifadəçiyə PM atma icazəsi verilir.\
\n\n.disapprove\
\nİşlədilişi: Cavab verilən istifadəçinin PM icazəsini silər.\
\n\n.block\
\nİşlədilişi: İstifadəçini bloklayar.\
\n\n.unblock\
\nİşlədilişi: İstifadəçini blokdan çıxarar.\
\n\n.notifoff\
\nİşlədilişi: İcazə verilməmiş istifadəçilərin mesajlarını təmizləyər ya da bildirişləri deaktiv edər.\
\n\n.notifon\
\nİşlədilişi: İcazə verilməmiş özel mesajların bildiriş gəlməsinə icazə verər."
})
