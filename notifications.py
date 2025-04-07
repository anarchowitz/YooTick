import datetime, asyncio, disnake
from database import Database

db = Database("database.db")

async def job(bot):
    db = Database("database.db")
    db.cursor.execute("SELECT username FROM date_stats WHERE date = ?", (datetime.date.today().strftime("%d.%m.%Y"),))
    staff_members = db.cursor.fetchall()
    for staff_member in staff_members:
        db.cursor.execute("SELECT closed_tickets FROM date_stats WHERE username = ? AND date = ?", (staff_member[0], datetime.date.today().strftime("%d.%m.%Y")))
        closed_tickets = db.cursor.fetchone()
        if closed_tickets is not None and closed_tickets[0] < 8:
            db.cursor.execute("SELECT user_id FROM staff_list WHERE username = ?", (staff_member[0],))
            user_id = db.cursor.fetchone()
            if user_id is not None:
                user_id = user_id[0]
                user = await bot.fetch_user(user_id)
                if user is not None:
                    embed = disnake.Embed(
                        title=" Предупреждение",
                        description="Вы не выполнили дневной план по тикетам. (8 тикетов)",
                        color=0xFF3030
                    )
                    embed.add_field(
                        name=" Внимание!",
                        value="Если вы не выполните дневной план по тикетам, вы **возможно** можете получить штраф. Если не отписывали АФК.",
                        inline=False
                    )
                    embed.set_footer(text="Пожалуйста, соблюдайте требования по тикетам.")
                    embed.set_author(name='Yooma Anti-Fine', icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
                    try:
                        await user.send(embed=embed)
                    except disnake.HTTPException as e:
                        if e.status == 403:
                            print(f"Не удалось отправить сообщение пользователю {user_id} из-за блокировки личных сообщений")

now = datetime.datetime.now()
target_time = now.replace(hour=18, minute=0, second=0, microsecond=0)

if now > target_time:
    target_time += datetime.timedelta(days=1)

async def run_schedule(bot):
    global target_time
    while True:
        await asyncio.sleep(1)
        if datetime.datetime.now() >= target_time:
            await job(bot)
            target_time += datetime.timedelta(days=1)