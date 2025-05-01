import datetime
import asyncio
import disnake
from database import Database

db = Database("database.db")

async def send_warning(user, closed_tickets):
    embed = disnake.Embed(
        title="Предупреждение",
        description=f"Вы не выполнили дневной план по тикетам. ({closed_tickets}/8)",
        color=0xFF3030
    )
    embed.add_field(
        name="Внимание!",
        value="Если вы не выполните дневной план по тикетам, вы **возможно** можете получить штраф. Если не отписывали АФК.",
        inline=False
    )
    embed.set_footer(text="Пожалуйста, соблюдайте требования по тикетам.")
    embed.set_author(
        name='Yooma Anti-Fine',
        icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg"
    )

    try:
        await user.send(embed=embed)
    except disnake.Forbidden:
        print(f"Не удалось отправить сообщение пользователю {user.id} (закрытые ЛС)")
    except disnake.HTTPException as e:
        print(f"Ошибка при отправке сообщения пользователю {user.id}: {e}")

async def job(bot):
    today = datetime.date.today().strftime("%d.%m.%Y")
    query = """
        SELECT 
            sl.user_id,
            COALESCE(ds.closed_tickets, 0) as closed_tickets
        FROM staff_list sl
        LEFT JOIN date_stats ds 
            ON sl.username = ds.username 
            AND ds.date = ?
        WHERE 
            sl.daily_quota = 1
    """
    
    db.cursor.execute(query, (today,))
    staff_members = db.cursor.fetchall()

    for user_id, closed_tickets in staff_members:
        if closed_tickets >= 8:
            continue

        try:
            user = await bot.fetch_user(user_id)
        except disnake.NotFound:
            print(f"Пользователь с ID {user_id} не найден")
            continue
        except disnake.HTTPException as e:
            print(f"Ошибка получения пользователя {user_id}: {e}")
            continue

        await send_warning(user, closed_tickets)

async def run_schedule(bot):
    while True:
        now = datetime.datetime.now()
        target_time = now.replace(hour=18, minute=0, second=0, microsecond=0)
        if now >= target_time:
            target_time += datetime.timedelta(days=1)
        await asyncio.sleep((target_time - now).total_seconds())
        await job(bot)