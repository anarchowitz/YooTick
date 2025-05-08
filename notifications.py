import datetime
import disnake
import aiocron
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

async def check_tickets_job(bot):
    print("Запуск проверки тикетов...")
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
            print(f"Пользователь {user_id} выполнил норму ({closed_tickets}/8)")
            continue

        try:
            user = await bot.fetch_user(user_id)
            await send_warning(user, closed_tickets)
        except disnake.NotFound:
            print(f"Пользователь с ID {user_id} не найден")
        except disnake.HTTPException as e:
            print(f"Ошибка получения пользователя {user_id}: {e}")

def setup_scheduler(bot):
    @aiocron.crontab('0 18 * * *', start=False)  # Каждый день в 18:00
    async def ticket_check_cron():
        try:
            await check_tickets_job(bot)
        except Exception as e:
            print(f"Ошибка в cron-задаче: {e}")
    ticket_check_cron.start()