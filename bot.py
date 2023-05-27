import logging
import os
import datetime
import asyncio

from pyrogram import filters
from pyrogram.types import (InlineKeyboardMarkup,InlineKeyboardButton)
from pyrogram.client import Client

from sql import Base, Groups, engine
from sqlalchemy.orm import Session

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

app = Client(
    os.environ['BOT_NAME'],
    api_id=os.environ['API_ID'],
    api_hash=os.environ['API_HASH'],
    bot_token=os.environ['BOT_TOKEN'],
    workdir="/db"
)

bot_id=int(os.environ['BOT_ID'])
admin_group=int(os.environ['ADMIN_GROUP'])

@app.on_message(filters.command("status", "/"))
async def bot_status(c, m):
    await m.reply_text(f"{os.environ['BOT_NAME']} Online")

@app.on_message(filters.command("id", "/"))
async def status(c, m):
    await m.reply_text(m.chat.id)

@app.on_message(filters.new_chat_members)
async def me_invited_or_joined(c, m):
    if m.new_chat_members[0].id == bot_id:
        logging.info(f'bot added to group {m.chat.title} ({m.chat.id})')
        logging.debug(m)
        now = datetime.datetime.now()
        
        with Session(engine) as s:
            results = s.query(Groups).filter_by(group_id=m.chat.id).filter_by(group_deleted=True).all()
            if results:
                await app.send_message(m.chat.id, text=f"Oh Oh, deine Gruppe ist schon bekannt und es gibt ein Problem. Bitte wende dich an die Admins der DACH Gruppe. Deine ID ist die {m.chat.id}")
                await app.leave_chat(m.chat.id)
                return
            else:
                with Session(engine) as session:
                    new_group = Groups(group_name=m.chat.title, group_id=m.chat.id, group_joined=now, group_active=False, group_deleted=False)
                    session.add(new_group)
                    session.commit()
                await c.send_message(
                    admin_group, 
                    f"Neue Gruppe Meldet sich an: {m.chat.title} ({m.chat.id})",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Zulassen", callback_data=f'accept+{m.chat.id}'),
                        InlineKeyboardButton("Ablehnen", callback_data=f'decline+{m.chat.id}')
                    ]])
                )
        return

@app.on_callback_query()
async def bot_to_group_check(c, m):
    logging.info(f'got new callback {m.data}')
    logging.debug(m)

    if m.data == "ok":
        await app.answer_callback_query(m.id, text="Keine Aktion durchgeführt")
        return
    
    group_query = int(m.data.split('+')[1])
    answer = str(m.data.split('+')[0])

    if answer == "accept":
        with Session(engine) as s:
            results = s.query(Groups).filter_by(group_id=group_query).all()
            if results:
                results[0].group_active = True
                s.commit()
        await app.edit_message_reply_markup(
            m.message.chat.id, m.message.id,
            InlineKeyboardMarkup([[
                InlineKeyboardButton("Angenommen - ablehnen?", callback_data=f"decline+{group_query}")]]))
        await app.answer_callback_query(m.id, text="Gruppe wurde hinzugefügt")
        await app.send_message(group_query, text="Danke, deine Gruppe wurde angenommen und ist nun auf der DACH Liste zu finden.")
        logging.info(f'request accepted from {m.from_user.id}')
        return
    
    if answer == "decline":
        with Session(engine) as s:
            results = s.query(Groups).filter_by(group_id=group_query).all()
            if results:
                results[0].group_deleted = True
                s.commit()
        await app.edit_message_reply_markup(
            m.message.chat.id, m.message.id,
            InlineKeyboardMarkup([[
                InlineKeyboardButton("Abgehlent - annehmen?", callback_data=f"release+{group_query}")]]))
        await app.answer_callback_query(m.id, text="Gruppe wurde abgehlent")
        await app.send_message(group_query, text="Tut mir leid, deine Gruppe wurde abgelehnt")
        await app.leave_chat(group_query)
        logging.info(f'request declined from {m.from_user.id}')
        return
    
    if answer == "release":
        with Session(engine) as s:
            result = s.query(Groups).filter_by(group_id=group_query).first()
            if result:
                s.delete(result)
                s.commit()
        await app.edit_message_reply_markup(
            m.message.chat.id, m.message.id,
            InlineKeyboardMarkup([[
                InlineKeyboardButton("Angenommen - ablehnen?", callback_data=f"decline+{group_query}")]]))
        await app.answer_callback_query(m.id, text="Gruppe wurde hinzugefügt")
        await app.send_message(group_query, text="Danke, deine Gruppe wurde angenommen und ist nun auf der DACH Liste zu finden.")
        logging.info(f'request released from {m.from_user.id}')
        return

@app.on_message(filters.command("group_list", "/"))
async def send_group_list(c, m):
    reply_text = []
    with Session(engine) as s:
        active_groups = s.query(Groups).filter(Groups.group_active == True).order_by(Groups.group_name).all()
        for group in active_groups:
            x = await app.get_chat(group.group_id)
            reply_text.append(f"[{group.group_name}](t.me/{x.username})")
        
    await m.reply_text("\n".join(reply_text), disable_web_page_preview=True)

@app.on_message(filters.command("release", "/"))
async def release_group(c, m):
    reply_text = []
    with Session(engine) as s:
        deleted_groups = s.query(Groups).filter(Groups.group_deleted == True).order_by(Groups.group_name).all()
        for group in deleted_groups:
            x = await app.get_chat(group.group_id)
            reply_text.append(f"[{group.group_name}](t.me/{x.username})")  
    await m.reply_text("\n".join(reply_text), disable_web_page_preview=True)



if __name__ == "__main__":
    logging.info("Bot is Online")
    Base.metadata.create_all(engine)
    app.run()