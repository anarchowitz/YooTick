# maded by. . . . . . . ANARCHOWITZ
# . . . . . . . . . . .,'´`. ,'``;
# . . . . . . . . . .,`. . .`—–'..
# . . . . . . . . . .,. . . . . .~ .`- .
# . . . . . . . . . ,'. . . . . . . .o. .o__
# . . . . . . . . _l. . . . . . . . . . . .
# . . . . . . . _. '`~-.. . . . . . . . . .,'
# . . . . . . .,. .,.-~-.' -.,. . . ..'–~`
# . . . . . . /. ./. . . . .}. .` -..,/
# . . . . . /. ,'___. . :/. . . . . .
# . . . . /'`-.l. . . `'-..'........ . .
# . . . ;. . . . . . . . . . . . .)-.....l
# . . .l. . . . .' —........-'. . . ,'
# . . .',. . ,....... . . . . . . . . .,'
# . . . .' ,/. . . . `,. . . . . . . ,'
# . . . . .. . . . . .. . . .,.- '
# . . . . . ',. . . . . ',-~'`. (.))
# . . . . . .l. . . . . ;. . . /__
# . . . . . /. . . . . /__. . . . .)
# . . . . . '-.. . . . . . .)
# . . . . . . .' - .......-`
version='2.3.6'
import os, json, datetime, requests

import disnake
from disnake.ext import commands
import asyncio  

intents = disnake.Intents.default() 
intents.message_content = True

class ButtonView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

class PersistentViewBot(commands.Bot):
    def __init__(self, activity=None):
        super().__init__(command_prefix='$', intents=intents, activity=activity)
        
        self.config_file = 'config.json'
        with open(self.config_file, 'r') as f:
            self.config = json.load(f)
        
        self.persistent_views_added = self.sent_message = self.config.get('sent_message', False)
        self.ticket_counter = self.config.get('ticket_counter', 0)
        self.staff_members = self.config.get('staff_members', {})
        self.dev_members = self.config.get('dev_members', [])
        self.TICKET_CHANNEL_ID = self.config.get('TICKET_CHANNEL_ID')
        self.REQUEST_CHANNEL_ID = self.config.get('REQUEST_CHANNEL_ID')
        self.CATEGORY_ID = self.config.get('CATEGORY_ID')
        self.config.setdefault('alert_settings', {})
        for staff_member in self.config.get('staff_members', {}):
            self.config['alert_settings'].setdefault(staff_member, True)
        
        self.config.setdefault('date_stats', {})

    def config_clear(self, user=None):
        staff_members = self.config.get('staff_members', {})
        if user:
            if user.lower() in staff_members:
                staff_members[user.lower()]['claimed_tickets'] = []
                staff_members[user.lower()]['claimed_ticket_users'] = {}
                self.config['staff_members'] = staff_members
                with open(self.config_file, 'w') as f:
                    json.dump(self.config, f, indent=4)
                return f"Мусор в конфиге для {user} был очищен."
            else:
                return f"Пользователь - {user} не был найден в списке staff."
        else:
            for staff_member in staff_members:
                staff_members[staff_member]['claimed_tickets'] = []
                staff_members[staff_member]['claimed_ticket_users'] = {}
            self.config['staff_members'] = staff_members
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            return "Мусор в конфиге для всех сотрудников был очищен."
    async def on_ready(self):
        if not self.persistent_views_added:
            self.persistent_views_added = True

        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            self.config.update(config)

        channel = self.get_channel(self.TICKET_CHANNEL_ID)
        if channel:
            if not self.config.get('sent_message', False):
                await asyncio.sleep(5)
                embed = disnake.Embed(
                    title="Создание обращения в клиентскую поддержку",
                    description="Мы настоятельно рекомендуем **подробно** описывать ваши просьбы или проблемы. Это поможет нам оказать вам **быструю и эффективную помощь**.\n\n"
                                "▎Важные моменты:\n"
                                "- Не открывайте тикеты, которые не соответствуют указанной теме или не связаны с описанной проблемой.\n"
                                "- Укажите все необходимые данные, чтобы мы могли оперативно решить ваш вопрос.\n"
                                "- Соблюдайте правила общения, чтобы избежать блокировки доступа к созданию запросов.\n\n"
                                "**Несоблюдение этих правил может привести к наказанию**.",
                    color=disnake.Color.from_rgb(119, 137, 253)
                )
                embed.set_author(name='Yooma Support', icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
                embed.set_thumbnail(url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
                view = disnake.ui.View()
                button = disnake.ui.Button(label='Задать вопрос', style=disnake.ButtonStyle.green, emoji='📨', custom_id='create_ticket')
                view.add_item(button)
                message = await channel.send(embed=embed, view=view) # type: ignore

                self.config['sent_message'] = True
                with open(self.config_file, 'r+') as f:
                    config_data = json.load(f)
                    config_data['sent_message'] = True
                    f.seek(0)
                    json.dump(config_data, f, indent=4)
                    f.truncate()

        print(f"Новая сессия входа {self.user} (ID: {self.user.id})\n------") 

    async def on_message(self, message):
        if message.author == self.user:
            return

        if isinstance(message.channel, disnake.DMChannel):
            if message.content.startswith('$ss'):
                if message.author.name.lower() in 'anarchowitz':
                    args = message.content.split()
                    if len(args) > 1:
                        target_member = args[1]
                        staff_members = bot.config.get('staff_members', {})
                        average_ratings = bot.config.get('average_ratings', {})
                        if target_member in staff_members:
                            stats = staff_members[target_member]
                            closed_tickets = stats.get('closed_tickets', 0)
                            average_rating = average_ratings.get(target_member, 'Нет оценки')
                            
                            embed = disnake.Embed(
                                title=f"Статистика для `{target_member}`",
                                color=disnake.Color.from_rgb(119, 137, 253)
                            )
                            embed.add_field(name="Закрытых тикетов", value=closed_tickets, inline=False)
                            embed.add_field(name="Средняя оценка", value=average_rating, inline=False)
                            
                            await message.channel.send(embed=embed)
                        else:
                            await message.channel.send(f"Пользователь `{target_member}` не найден в списке сотрудников.")
                    else:
                        staff_members = bot.config.get('staff_members', {})
                        average_ratings = bot.config.get('average_ratings', {})
                        sorted_staff_members = sorted(staff_members.items(), key=lambda x: x[1].get('closed_tickets', 0), reverse=True)
                        embed = disnake.Embed(
                            title="Общая статистика закрытых тикетов",
                            color=disnake.Color.from_rgb(119, 137, 253)
                        )
                        for i, (staff_member, stats) in enumerate(sorted_staff_members):
                            closed_tickets = stats.get('closed_tickets', 0)
                            average_rating = average_ratings.get(staff_member, 'Нет оценки')
                            embed.add_field(name=f"Топ {i+1}: `{staff_member}`", value=f"Закрытых тикетов: {closed_tickets}\nСредняя оценка: {average_rating}", inline=False)
                        await message.channel.send(embed=embed)
                else:
                    pass
        
        if message.content.startswith('$message'):
            if message.guild is not None:
                await message.author.send("Эта команда доступна только в личных сообщениях с ботом!")
                return
            if message.author.name.lower() not in bot.config.get('dev_members', []):
                await message.author.send("Эта команда доступна только для разработчиков!")
                return
            parts = message.content.split(' ', 2)
            if len(parts) < 3:
                await message.author.send("Использование: $message <user_id> <сообщение>")
                return
            try:
                user_id = int(parts[1])
            except ValueError:
                await message.author.send("ID пользователя должно быть числом.")
                return
            msg = parts[2]
            try:
                user = await bot.fetch_user(user_id)
                await user.send(msg)
                await message.author.send(f"Сообщение отправлено {user.name}.")
            except disnake.NotFound:
                await message.author.send("Пользователь не найден.")
            except Exception as e:
                await message.author.send("Не удалось отправить сообщение: " + str(e))

        if message.content.startswith('$help'):
            await message.delete()
            args = message.content.split()
            if len(args) < 2:
                await message.channel.send("Пожалуйста, укажите 'staff' или 'dev' после команды $help.")
                return
            role_type = args[1].lower()
            embed = disnake.Embed(
                title=f"Рабочие команды для {role_type}",
                color=disnake.Color.from_rgb(119, 137, 253)
            )
            staff_commands = [
                ("$claim", "`Взять тикет на себя. [danger]`"),
                ("$close", "`Закрыть тикет. [danger]`"),
                ("$alert", "`Получать информацию по поставленным лайкам/дизлайкам`"),
                ("$info", "`Информация про бота.`"),
                ("$price", "`Информация по цена докупки/заморозки/перенос (для ст. админов)`"),
                ("$list_rights", "`Информация про всех участников с правами.`"),
                ("$list_helper", "`Информация про быстрые сокращение (формы) по словам.`"),
                ("$rate_check", "`Просмотр лайков/дизлайков конкретного человека/всех сотрудников.`"),
                ("$rate_top", "`Просмотр общего рейтинга всех сотрудников.`"),
                ("$clear_tickets", "`Очистить список созданных тикетов людьми (created_tickets.json) [danger].`"),
            ]
            dev_commands = [
                ("$add_rights", "`Добавить права пользователю.`"),
                ("$del_rights", "`Убрать права у пользователя.`"),
                ("$edit_rights", "`Изменение в конфиге значений для определенного сотрудника.`"),
                ("$add_staff_role", "`Добавить роль в список staff_roles.`"),
                ("$del_staff_role", "`Убрать роль из списка staff_roles.`"),
                ("$secret_stats", "`Показать статистику количество закрытых тикетов..`"),
                ("$stats", "`Показать скрытую статистику количество закрытых тикетов.`"),
                ("$date_stats", "`Показать статистику закрытых тикетов за дату.`"),
                ("$set", "`Установить количество закрытых тикетов для staff_member.`"),
                ("$sum", "`Прибавить/убавить количество закрытых тикетов для staff_member.`"),
                ("$rate_clear", "`Очистить оценки конкретному сотруднику/всем.`"),
                ("$edit_rate", "`Изменение лайков/дизлайков конкретному сотруднику.`"),
                ("$date_set_stats", "`Установить количество закрытых тикетов за дату.`"),
                ("$config_clear", "`Очистка конфига от лишнего мусора (Рекомендуется: когда тикетов нету) [danger].`"),
                ("$config_date_clear", "`Очистить даты в date_stats конфиге. [danger] `"),
                ("$claimedticket_clear", "`Очистка в конфиге claimed_tickets [danger]`"),
                ("$oldupdate_clear", "`Не помню но нужно первым делом после обновы 2.2 прописать [danger]`"),
                ("$tickets_num", "`Установить количество созданных тикетов.`"),
                ("$primetime", "`Установить рабочее время.`"),
                ("$price_set", "`Изменение информации цен докупки/заморозки/перенос (для ст. админов)`")
            ]
            if role_type == "staff":
                commands = staff_commands
                if message.author.name.lower() not in self.config.get('staff_members', {}):
                    await message.channel.send("Эта команда доступна только для staff_members!")
                    return
            elif role_type == "dev":
                commands = dev_commands
                if message.author.name.lower() not in self.config.get('dev_members', {}):
                    await message.channel.send("Эта команда доступна только для dev_members!")
                    return
            else:
                await message.channel.send("Пожалуйста, укажите 'staff' или 'dev' после команды $help.")
                return
            for command, description in commands:
                embed.add_field(name=command, value=description, inline=False)
            await message.author.send(embed=embed)
            await message.channel.send("Отправил список команд в личные сообщения.")
        
        if message.content.startswith('$ticketban'):
            await message.delete()
            if message.author.name.lower() in bot.staff_members:
                args = message.content.split()
                if len(args) == 3:
                    username = args[1].lower()
                    duration = args[2].lower()
                    if duration.endswith('d'):
                        duration_in_seconds = int(duration[:-1]) * 86400
                    elif duration.endswith('h'):
                        duration_in_seconds = int(duration[:-1]) * 3600
                    else:
                        await message.channel.send("Неправильный формат времени. Используйте 'd' для дней или 'h' для часов.")
                        return
                    with open('created_tickets.json', 'r+') as f:
                        try:
                            created_tickets = json.load(f)
                        except json.JSONDecodeError:
                            created_tickets = {}
                        if username not in created_tickets:
                            created_tickets[username] = {'banned_until': datetime.datetime.now().timestamp() + duration_in_seconds, 'banned_by': message.author.name}
                        else:
                            created_tickets[username]['banned_until'] = datetime.datetime.now().timestamp() + duration_in_seconds
                            created_tickets[username]['banned_by'] = message.author.name
                        f.seek(0)
                        json.dump(created_tickets, f)
                        f.truncate()
                        await message.channel.send(f"Пользователь {username} забанен в тикетах на {duration}")
                else:
                    await message.channel.send("Неправильный синтаксис. Используйте `$ticketban <username> <duration>`")
            else:
                await message.channel.send("Эта команда доступна только для разработчиков!")
        
        if message.content.startswith('$ticketunban'):
            await message.delete()
            if message.author.name.lower() in bot.staff_members:
                args = message.content.split()
                if len(args) == 2:
                    username = args[1].lower()
                    with open('created_tickets.json', 'r+') as f:
                        try:
                            created_tickets = json.load(f)
                        except json.JSONDecodeError:
                            created_tickets = {}
                        if username in created_tickets:
                            del created_tickets[username]
                            f.seek(0)
                            json.dump(created_tickets, f)
                            f.truncate()
                            await message.channel.send(f"Пользователь {username} разбанен в тикетах.")
                        else:
                            await message.channel.send(f"Пользователь {username} не найден в списке созданных тикетов.")
                else:
                    await message.channel.send("Неправильный синтаксис. Используйте `$ticketunban <username>`")
            else:
                await message.channel.send("Эта команда доступна только для разработчиков!")
        if message.content.startswith('$alert'):
            await message.delete()
            if message.author.name.lower() in bot.config.get('staff_members', {}):
                args = message.content.split()
                if len(args) == 2:
                    staff_member = message.author.name.lower()
                    if args[1].lower() == 'on':
                        if 'alert_settings' not in bot.config:
                            bot.config['alert_settings'] = {}
                        bot.config['alert_settings'][staff_member] = True
                        with open('config.json', 'w') as f:
                            json.dump(bot.config, f)
                        await message.channel.send(f"Уведомления включены для {staff_member}")
                    elif args[1].lower() == 'off':
                        if 'alert_settings' not in bot.config:
                            bot.config['alert_settings'] = {}
                        bot.config['alert_settings'][staff_member] = False
                        with open('config.json', 'w') as f:
                            json.dump(bot.config, f)
                        await message.channel.send(f"Уведомления выключены для {staff_member}")
                    else:
                        await message.channel.send("Неправильный синтаксис. Используйте `$alert on` или `$alert off`")
                else:
                    await message.channel.send("Неправильный синтаксис. Используйте `$alert on` или `$alert off`")
            else:
                await message.channel.send("Эта команда доступна только для сотрудников!")
        
        if message.content.startswith('$price_set'):
            await message.delete()
            if message.author.name.lower() in bot.dev_members:
                args = message.content.split()
                if len(args) > 1:
                    service_type = args[1].lower()
                    if service_type == 'vip':
                        if len(args) == 6:
                            medium_price = args[2]
                            platinum_price = args[3]
                            crystal_price = args[4]
                            crystal_plus_price = args[5]
                            if 'prices' not in bot.config:
                                bot.config['prices'] = {}
                            bot.config['prices']['vip'] = {
                                'medium': medium_price,
                                'platinum': platinum_price,
                                'crystal': crystal_price,
                                'crystal+': crystal_plus_price
                            }
                            with open(bot.config_file, 'w') as f:
                                json.dump(bot.config, f, indent=4)
                            await message.channel.send("Успешно установлено значение цен для VIP.")
                        else:
                            await message.channel.send("Неправильный синтаксис. Используйте `$price_set vip <medium_price> <platinum_price> <crystal_price> <crystal_plus_price>`")
                    elif service_type == 'admin':
                        if len(args) == 5:
                            admin_1lvl_price = args[2]
                            admin_2lvl_price = args[3]
                            sponsor_price = args[4]
                            if 'prices' not in bot.config:
                                bot.config['prices'] = {}
                            bot.config['prices']['admin'] = {
                                '1lvl': admin_1lvl_price,
                                '2lvl': admin_2lvl_price,
                                'sponsor': sponsor_price
                            }
                            with open(bot.config_file, 'w') as f:
                                json.dump(bot.config, f, indent=4)
                            await message.channel.send("Успешно установлено значение цен для ADMIN.")
                        else:
                            await message.channel.send("Неправильный синтаксис. Используйте `$price_set admin <admin_1lvl_price> <admin_2lvl_price> <sponsor_price>`")
                    elif service_type == 'services':
                        if len(args) == 8:  # Увеличиваем количество аргументов до 8
                            transfer_price = args[2]
                            unfreeze_admin_1_price = args[3]
                            unfreeze_admin_2lvl_price = args[4]
                            unfreeze_sponsor_price = args[5]
                            unmute_site_price = args[6]  # Новая услуга: размут в чате на сайте
                            unban_ds_price = args[7]     # Новая услуга: разбан в дискорде
                            if 'prices' not in bot.config:
                                bot.config['prices'] = {}
                            bot.config['prices']['services'] = {
                                'transfer': transfer_price,
                                'unfreeze_admin_1': unfreeze_admin_1_price,
                                'unfreeze_admin_2lvl': unfreeze_admin_2lvl_price,
                                'unfreeze_sponsor': unfreeze_sponsor_price,
                                'unmute_site': unmute_site_price,  # Добавляем новую услугу
                                'unban_ds': unban_ds_price         # Добавляем новую услугу
                            }
                            with open(bot.config_file, 'w') as f:
                                json.dump(bot.config, f, indent=4)
                            await message.channel.send("Успешно установлено значение цен для SERVICES.")
                        else:
                            await message.channel.send("Неправильный синтаксис. Используйте `$price_set services <transfer_price> <unfreeze_admin_1_price> <unfreeze_admin_2lvl_price> <unfreeze_sponsor_price> <unmute_site_price> <unban_ds_price>`")
                    else:
                        await message.channel.send("Неправильный тип услуги. Используйте `vip`, `admin` или `services`.")
                else:
                    await message.channel.send("Неправильный синтаксис. Используйте `$price_set <service_type> <prices>`")
            else:
                await message.channel.send("Эта команда доступна только для разработчиков!")
        elif message.content.startswith('$price'):
            await message.delete()
            embed = disnake.Embed(
                title="Выберите категорию для просмотра быстрых цен",
                description="Пожалуйста, выберите категорию, чтобы увидеть цены.",
                color=disnake.Color.from_rgb(119, 137, 253)
            )
            view = disnake.ui.View()
            vip_button = disnake.ui.Button(label='ВИП', style=disnake.ButtonStyle.blurple, emoji='💎', custom_id='vip_service')
            admin_button = disnake.ui.Button(label='АДМ', style=disnake.ButtonStyle.blurple, emoji='👮', custom_id='admin_service')
            services_button = disnake.ui.Button(label='СЕРВИСЫ', style=disnake.ButtonStyle.blurple, emoji='🛠️', custom_id='services')
            view.add_item(vip_button)
            view.add_item(admin_button)
            view.add_item(services_button)
            await message.channel.send(embed=embed, view=view)
        if message.content.startswith('$claim'):
            await message.delete()
            if "ticket" in message.channel.name.lower() and message.author.name.lower() in self.config.get('staff_members', {}): # type: ignore
                await self.claim_ticket(message)
            elif "ticket" not in message.channel.name.lower(): # type: ignore
                await message.channel.send("Эта команда доступна только в каналах с названием содержащим слово 'ticket'!")
            else:
                await message.channel.send("Эта команда доступна только для staff_members!")

        elif message.content.startswith('$close'):
            await message.delete()
            if "ticket" in message.channel.name.lower() and message.author.name.lower() in self.config.get('staff_members', {}): # type: ignore
                await self.close_ticket(message)
            elif "ticket" not in message.channel.name.lower(): # type: ignore
                await message.channel.send("Эта команда доступна только в каналах с названием содержащим слово 'ticket'!")
            else:
                await message.channel.send("Эта команда доступна только для staff_members!")
    
        if message.content.startswith('$add_rights'): 
            await message.delete() 
            if message.author.name.lower() in bot.dev_members: 
                args = message.content.split() 
                if len(args) == 4:
                    nickname = args[1] 
                    role = args[2] 
                    user_id = args[3]
                    if role.lower() == 'staff': 
                        bot.config['staff_members'][nickname] = {'name': nickname, 'id': int(user_id), 'claimed_tickets': [], 'closed_tickets': 0}
                    elif role.lower() == 'dev': 
                        bot.config['dev_members'].append(nickname) 
                    else: 
                        await message.channel.send("Неправильная роль. Пишите 'staff' или 'dev'.") 
                    with open(bot.config_file, 'w') as f: 
                        json.dump(bot.config, f, indent=4) 
                    await message.channel.send(f"Добавлена у `{nickname}` роль: `{role}`") 
                else: 
                    await message.channel.send("Неправильный синтаксис. Используйте `$add_rights <nickname> <role> <user_id>`") 
            else: 
                await message.channel.send("Эта команда доступна только для разработчиков!") 
        
        if message.content.startswith('$del_rights'):
            await message.delete()
            if message.author.name.lower() in self.dev_members:
                args = message.content.split()
                if len(args) == 3:
                    username = args[1]
                    role = args[2]
                    if role.lower() == 'staff':
                        if username in self.config['staff_members']:
                            del self.config['staff_members'][username]
                        else:
                            await message.channel.send(f"{username} нету в staff_member списке.")
                    elif role.lower() == 'dev':
                        if username in self.dev_members:
                            self.dev_members.remove(username)
                        else:
                            await message.channel.send(f"{username} нету в dev_members списке.")
                    else:
                        await message.channel.send("Неправильная роль. Пишите 'staff' или 'dev'.")
                    with open(self.config_file, 'w') as f:
                        json.dump(self.config, f, indent=4)
                    await message.channel.send(f"Убрана у `{username}` роль `{role}`")
                else:
                    await message.channel.send("Неправильный синтаксис. Используйте $del_rights <username> <role>")
            else:
                await message.channel.send("Эта команда доступна только для разработчиков!")
        if message.content.startswith('$edit_rights'):
            await message.delete()
            if message.author.name.lower() in bot.dev_members:
                args = message.content.split()
                if len(args) >= 2:
                    nickname = args[1].lower()
                    if nickname in bot.config['staff_members']:
                        if len(args) == 2:
                            user_data = bot.config['staff_members'][nickname]
                            await message.channel.send(f"Текущие данные для `{nickname}`:")
                            for key, value in user_data.items():
                                if key not in ["claimed_tickets", "claimed_ticket_users", "closed_tickets"]:
                                    await message.channel.send(f"{key}: {value}")
                        elif len(args) >= 3:
                            action = args[2].lower()
                            if action == 'edit':
                                if len(args) == 4:
                                    await message.channel.send("Неправильный синтаксис. Используйте `$edit_rights <nickname> edit <key> <value>`.")
                                elif len(args) == 5:
                                    key = args[3].lower()
                                    value = args[4]
                                    if key in bot.config['staff_members'][nickname]:
                                        bot.config['staff_members'][nickname][key] = value
                                        await message.channel.send(f"Значение `{key}` для `{nickname}` изменено на `{value}`.")
                                    else:
                                        await message.channel.send(f"Ключ `{key}` не найден в данных для `{nickname}`.")
                            elif action == 'add':
                                if len(args) == 4:
                                    await message.channel.send("Неправильный синтаксис. Используйте `$edit_rights <nickname> add <key> <value>`.")
                                elif len(args) == 5:
                                    key = args[3].lower()
                                    value = args[4]
                                    if key not in bot.config['staff_members'][nickname]:
                                        bot.config['staff_members'][nickname][key] = value
                                        await message.channel.send(f"Новое значение `{key}` для `{nickname}` добавлено с значением `{value}`.")
                                    else:
                                        await message.channel.send(f"Ключ `{key}` уже существует в данных для `{nickname}`.")
                            else:
                                await message.channel.send("Неправильное действие. Используйте `edit` или `add`.")
                        else:
                            await message.channel.send("Неправильный синтаксис. Используйте `$edit_rights <nickname> <action> <key> <value>`.")
                    else:
                        await message.channel.send(f"Пользователь `{nickname}` не найден в списке staff.")
                else:
                    await message.channel.send("Неправильный синтаксис. Используйте `$edit_rights <nickname> <action> <key> <value>`.")

                with open(bot.config_file, 'w') as f:
                    json.dump(bot.config, f, indent=4)
            else:
                await message.channel.send("Эта команда доступна только для разработчиков!")
                if message.content.startswith('$add_staff_role'):
                    await message.delete()
                    if message.author.name.lower() in bot.dev_members:
                        args = message.content.split()
                        if len(args) == 2:
                            role_id = args[1]
                            try:
                                role_id = int(role_id)
                                bot.config['staff_roles'].append(role_id)
                                with open(bot.config_file, 'w') as f:
                                    json.dump(bot.config, f, indent=4, )
                                await message.channel.send(f"Роль айди: `{role_id}` была добавлена к staff_roles.")
                            except ValueError:
                                await message.channel.send("Неправильная айди роли. Введите правильный айди.")
                        else:
                            await message.channel.send("Неправильный синтаксис. Используйте `$add_staff_role <role_id>`")
                    else:
                        await message.channel.send("Эта команда доступна только для разработчиков!")

        if message.content.startswith('$del_staff_role'):
            await message.delete()
            if message.author.name.lower() in bot.dev_members:
                args = message.content.split()
                if len(args) == 2:
                    role_id = args[1]
                    try:
                        role_id = int(role_id)
                        if role_id in bot.config['staff_roles']:
                            bot.config['staff_roles'].remove(role_id)
                            with open(bot.config_file, 'w') as f:
                                json.dump(bot.config, f, indent=4, )
                            await message.channel.send(f"Роль айди: `{role_id}` была убрана из staff_roles")
                        else:
                            await message.channel.send(f"Роль айди: `{role_id}` не находится в staff_roles")
                    except ValueError:
                        await message.channel.send("Неправильная айди роли. Введите правильный айди.")
                else:
                    await message.channel.send("Неправильный синтаксис. Используйте `$del_staff_role <role_id>`")
            else:
                await message.channel.send("Эта команда доступна только для разработчиков!")
        
        if message.content.startswith('$info'):
            await message.delete()
            author_name = message.author.name.lower()
            staff_members = bot.config.get('staff_members', {})
            if author_name in staff_members:
                sorted_staff_members = sorted(staff_members.items(), key=lambda x: x[1].get('closed_tickets', 0), reverse=True)
                embed = disnake.Embed(
                    title="Информация про бота",
                    color=disnake.Color.from_rgb(119, 137, 253)
                )
                embed.add_field(name="Версия ЮТика", value=version, inline=False)
                embed.add_field(name="Всего тикетов", value=f"{bot.ticket_counter}", inline=False)
                embed.add_field(name="Время работы", value=f"{bot.config.get('primetime', {}).get('start', 'Unknown')} - {bot.config.get('primetime', {}).get('end', 'Unknown')}", inline=False)
                embed.add_field(name="Активных тикетов", value=f"{len([channel for channel in bot.get_all_channels() if 'ticket' in channel.name.lower()])}", inline=False)
                embed.set_footer(
                    text="maded by anarchowitz ",
                    icon_url="https://downloader.disk.yandex.com/preview/e7bec6580696944ad49039332e71c023ac8d13baf9841d96653d7fdc759cd75e/6705e21f/1PtBsEqXKP1JKP6WCfZ_saYALCuLK5fhR2ZTiKfroCRvtqZHpiv1yjtsIUsGHYgYvMhuTlGwx0NcYtEOYN_WVA%3D%3D?uid=0&filename=fc4cd000b95dfcb37a5467ff6f15638b.png&disposition=inline&hash=&limit=0&content_type=image%2Fpng&owner_uid=0&tknv=v2&size=2048x2048",
                )
                await message.channel.send(embed=embed)
            else:
                await message.channel.send(f"Эта команда доступна только для staff_members!")

        if message.content.startswith('$list_rights'):
            await message.delete()
            if message.author.name.lower() in bot.config.get('staff_members', {}):
                staff_members = bot.config.get('staff_members', {})
                dev_members = bot.config.get('dev_members', [])
                embed = disnake.Embed(
                    title="Список прав доступа",
                    color=disnake.Color.from_rgb(119, 137, 253)
                )
                embed.add_field(name="Staff Members", value='\n'.join(staff_members.keys()), inline=False)
                embed.add_field(name="Dev Members", value='\n'.join(dev_members), inline=False)
                await message.channel.send(embed=embed)
            else:
                await message.channel.send("Эта команда доступна только для staff_members!")

        if message.content.startswith('$list_helper'):
            await message.delete()
            if message.author.name.lower() in bot.config.get('staff_members', {}):
                staff_members = bot.config.get('staff_members', {})
                dev_members = bot.config.get('dev_members', [])
                embed = disnake.Embed(
                    title="Список быстрых ответов",
                    color=disnake.Color.from_rgb(119, 137, 253)
                )
                embed.add_field(
                    name="`.админчат`",
                    value="Форма о кратком гайде по отправлению сообщения в админчат кс2",
                    inline=False
                )
                embed.add_field(
                    name="`.ссылкасайт`",
                    value="Форма о кратком гайде по отправлению личной ссылки на профиль сайта",
                    inline=False
                )
                embed.add_field(
                    name="`.обнова`",
                    value="Форма о том, что вышла обнова в кс и сервера не доступны",
                    inline=False
                )
                embed.add_field(
                    name="`.жалоба`",
                    value="Форма о том, что жалоба передана в админ чат",
                    inline=False
                )
                embed.add_field(
                    name="`.баг`",
                    value="Форма о том, что информация о баге - передана разработчику",
                    inline=False
                )
                embed.add_field(
                    name="`.скинрейв`",
                    value="Форма выдачи токенов за регистрацию на скинрейве",
                    inline=False
                )
                embed.add_field(
                    name="`.коины`",
                    value="Форма о том, что делать с коинами",
                    inline=False
                )
                embed.add_field(
                    name="`.соцсети`",
                    value="Форма о наших соцсетях",
                    inline=False
                )
                embed.add_field(
                    name="`.промоввод`",
                    value="Форма о том, как ввести промокод.",
                    inline=False
                )
                embed.add_field(
                    name="`.блекджек`",
                    value="Форма о том, как играть в блекджек.",
                    inline=False
                )
                await message.channel.send(embed=embed)
            else:
                await message.channel.send("Эта команда доступна только для staff_members!")   
            
        
        if message.content.startswith('$date_set_stats'):
            await message.delete()
            if message.author.name.lower() in bot.dev_members:
                args = message.content.split()
                if len(args) == 4:
                    date_str = args[1]
                    staff_member = args[2].lower()
                    closed_tickets = int(args[3])
                    if date_str == 'all' and staff_member == 'all':
                        for date_key in bot.config.get('date_stats', {}).keys():
                            bot.config['date_stats'][date_key] = {k: closed_tickets for k in bot.config['staff_members']}
                    elif date_str == 'all':
                        for date_key in bot.config.get('date_stats', {}).keys():
                            if staff_member in bot.config['staff_members']:
                                bot.config['date_stats'][date_key][staff_member] = closed_tickets
                    elif staff_member == 'all':
                        if date_str in bot.config.get('date_stats', {}):
                            bot.config['date_stats'][date_str] = {k: closed_tickets for k in bot.config['staff_members']}
                        else:
                            bot.config['date_stats'][date_str] = {k: closed_tickets for k in bot.config['staff_members']}
                    else:
                        date_obj = datetime.datetime.strptime(date_str, '%d.%m.%Y').date()
                        date_str = date_obj.isoformat()
                        if date_str in bot.config.get('date_stats', {}):
                            bot.config['date_stats'][date_str][staff_member] = closed_tickets
                        else:
                            bot.config['date_stats'][date_str] = {staff_member: closed_tickets}
                    with open(bot.config_file, 'w') as f:
                        json.dump(bot.config, f, indent=4)
                    await message.channel.send(f"Для `{staff_member}` в дату: `{date_str}` было установлено закрытых тикетов {closed_tickets}.")
                else:
                    await message.channel.send("Неправильный синтаксис. Используйте `$date_set_stats <date/all> <staff_member/all> <closed_tickets>`")
            else:
                await message.channel.send("Эта команда доступна только для разработчиков!")
        
        if message.content.startswith('$date_stats'):
            await message.delete()
            if message.author.name.lower() in bot.dev_members:
                args = message.content.split()
                if len(args) == 2:
                    date_str = args[1]
                    try:
                        date_obj = datetime.datetime.strptime(date_str, '%d.%m.%Y').date()
                        date_str = date_obj.isoformat()
                        if date_str in bot.config.get('date_stats', {}):
                            date_stats = bot.config['date_stats'][date_str]
                            sorted_date_stats = sorted(date_stats.items(), key=lambda x: x[1], reverse=True)
                            embed = disnake.Embed(
                                title=f"Статистика закрытых тикетов за `{date_str}`",
                                color=disnake.Color.from_rgb(119, 137, 253)
                            )
                            for staff_member, closed_tickets in sorted_date_stats:
                                embed.add_field(name=f"`{staff_member}`", value=f"Закрытых тикетов: {closed_tickets}", inline=False)
                            await message.channel.send(embed=embed)
                        else:
                            await message.channel.send(f"Нет статистики для даты `{date_str}`")
                    except ValueError:
                        await message.channel.send("Неправильный формат даты. Используйте DD.MM.YYYY")
                else:
                    await message.channel.send("Неправильный синтаксис. Используйте `$date_stats <date>`")
            else:
                await message.channel.send("Эта команда доступна только для разработчиков!")
        
        elif message.content.startswith('$rate_top'):
            await message.delete()
            if message.author.name.lower() in bot.config.get('staff_members', {}):
                args = message.content.split()
                staff_members = bot.config.get('staff_members', {})
                if len(args) > 1:
                    target_member = args[1].lower()
                    if target_member in staff_members:
                        target_stats = staff_members[target_member]
                        target_closed_tickets = target_stats.get('closed_tickets', 0)
                        target_likes = target_stats.get('likes', 0)
                        target_dislikes = target_stats.get('dislikes', 0)
                        target_score = target_likes - target_dislikes
                        embed = disnake.Embed(
                            title=f"Статистика для `{target_member}`",
                            color=disnake.Color.from_rgb(119, 137, 253)
                        )
                        embed.add_field(name="Закрытые тикеты", value=f"{target_closed_tickets}", inline=False)
                        embed.add_field(name="Общий рейтинг", value=f"{target_score}", inline=False)
                        embed.add_field(name="Лайки", value=f"{target_likes}", inline=False)
                        embed.add_field(name="Дизлайки", value=f"{target_dislikes}", inline=False)
                        await message.channel.send(embed=embed)
                    else:
                        await message.channel.send(f"Пользователь `{target_member}` не найден в списке сотрудников.")
                else:
                    staff_scores = {}
                    for staff_member, stats in staff_members.items():
                        closed_tickets = stats.get('closed_tickets', 0)
                        likes = stats.get('likes', 0)
                        dislikes = stats.get('dislikes', 0)
                        score = likes - dislikes
                        staff_scores[staff_member] = score
                    sorted_staff_members = sorted(staff_scores.items(), key=lambda x: x[1], reverse=True)
                    embed = disnake.Embed(
                        title="Общий рейтинг сотрудников",
                        color=disnake.Color.from_rgb(119, 137, 253)
                    )
                    for i, (staff_member, score) in enumerate(sorted_staff_members):
                        embed.add_field(name=f"{i + 1}. `{staff_member}`", value=f"Общий рейтинг: {score}", inline=False)
                    await message.channel.send(embed=embed)
            else:
                await message.channel.send("Эта команда доступна только для разработчиков!")

        if message.content.startswith('$secret_stats'):
            await message.delete()
            if message.author.name.lower() in bot.dev_members:
                args = message.content.split()
                if len(args) > 1:
                    target_member = args[1]
                    staff_members = bot.config.get('staff_members', {})
                    if target_member in staff_members:
                        stats = staff_members[target_member]
                        closed_tickets = stats.get('closed_tickets', 0)
                        likes = stats.get('likes', 0)
                        dislikes = stats.get('dislikes', 0)
                        target_score = likes - dislikes
                        embed = disnake.Embed(
                            title=f"**Статистика для `{target_member}`**",
                            color=disnake.Color.from_rgb(119, 137, 253)
                        )
                        embed.add_field(name="Закрытых тикетов", value=closed_tickets, inline=False)
                        embed.add_field(name="Общий рейтинг", value=target_score, inline=False)
                        embed.add_field(name="Лайки", value=likes, inline=False)
                        embed.add_field(name="Дизлайки", value=dislikes, inline=False)
                        await message.channel.send(embed=embed)
                    else:
                        await message.channel.send(f"Пользователь `{target_member}` не найден в списке сотрудников.")
                else:
                    staff_members = bot.config.get('staff_members', {})
                    sorted_staff_members = sorted(staff_members.items(), key=lambda x: x[1].get('closed_tickets', 0), reverse=True)
                    embed = disnake.Embed(
                        title="Общая статистика закрытых тикетов",
                        color=disnake.Color.from_rgb(119, 137, 253)
                    )
                    for i, (staff_member, stats) in enumerate(sorted_staff_members):
                        closed_tickets = stats.get('closed_tickets', 0)
                        likes = stats.get('likes', 0)
                        dislikes = stats.get('dislikes', 0)
                        score = likes - dislikes
                        embed.add_field(name=f"**Топ {i+1}**: `{staff_member}`", value=f"Закрытых тикетов: {closed_tickets}\nОбщий рейтинг: {score}\nЛайки: {likes}\nДизлайки: {dislikes}", inline=False)
                    await message.channel.send(embed=embed)
            else:
                await message.channel.send("Эта команда доступна только для разработчиков!")
        
        if message.content.startswith('$stats'):
            await message.delete()
            if message.author.name.lower() in bot.dev_members:
                args = message.content.split()
                staff_members = bot.config.get('staff_members', {})
                sorted_staff_members = sorted(staff_members.items(), key=lambda x: x[1].get('closed_tickets', 0), reverse=True)
                embed = disnake.Embed(
                    title="Общая скрытая статистика закрытых тикетов",
                    color=disnake.Color.from_rgb(119, 137, 253)
                )
                for i, (staff_member, stats) in enumerate(sorted_staff_members):
                    closed_tickets = stats.get('closed_tickets', 0)
                    likes = stats.get('likes', 0)
                    dislikes = stats.get('dislikes', 0)
                    score = likes - dislikes
                    embed.add_field(name=f"**Топ {i+1}**: `{staff_member}`", value=f"Общий рейтинг: {score}\nЛайки: {likes}\nДизлайки: {dislikes}", inline=False)
                await message.channel.send(embed=embed)
            else:
                await message.channel.send("Эта команда доступна только для разработчиков!")
        
        if message.content.startswith('$primetime'):
            await message.delete()
            if message.author.name.lower() in self.dev_members:
                args = message.content.split()
                if len(args) == 3:
                    start_time = args[1]
                    end_time = args[2]
                    self.config['primetime'] = {'start': start_time, 'end': end_time}
                    with open(self.config_file, 'w') as f:
                        json.dump(self.config, f, indent=4)
                    await message.channel.send(f"Рабочее время установлено: `{start_time}` - `{end_time}`")
                else:
                    await message.channel.send("Неправильный синтаксис. Используйте $primetime `<start_time>` `<end_time>`\n (e.g $primetime 10:00 20:00)")
            else:
                await message.channel.send("Эта команда доступна только для разработчиков!")

        if message.content.startswith('$tickets_num'):
            await message.delete()
            if message.author.name.lower() in bot.dev_members:
                args = message.content.split()
                if len(args) == 2:
                    try:
                        ticket_counter = int(args[1])
                        bot.config['ticket_counter'] = ticket_counter
                        with open(bot.config_file, 'w') as f:
                            json.dump(bot.config, f)
                        await message.channel.send(f"Значение созданных было установленно в значение: `{ticket_counter}`.")
                    except ValueError:
                        await message.channel.send("Неправильное количество. (no int)")
                else:
                    await message.channel.send("Неправильный синтаксис. Используйте `$tickets_num <ticket_counter>`")
            else:
                await message.channel.send("Эта команда доступна только для разработчиков!")
        
        if message.content.startswith('$set'):
            await message.delete()
            if message.author.name.lower() in bot.dev_members:
                args = message.content.split()
                if len(args) == 3:
                    staff_member = args[1]
                    try:
                        closed_tickets = int(args[2])
                        staff_members = bot.config.get('staff_members', {})
                        if staff_member.lower() == 'all':
                            for member in staff_members:
                                staff_members[member]['closed_tickets'] = closed_tickets
                        elif staff_member.lower() in [member.lower() for member in staff_members]:
                            staff_members[staff_member.lower()]['closed_tickets'] = closed_tickets
                            bot.config['staff_members'] = staff_members
                            with open(bot.config_file, 'w') as f:
                                json.dump(bot.config, f)
                            await message.channel.send(f"Установленно для `{staff_member}` в значение `{closed_tickets}`")
                        else:
                            await message.channel.send(f"{staff_member} не из списка staff_member")
                    except ValueError:
                        await message.channel.send("Неправильное количество. (no int)")
                else:
                    await message.channel.send("Неправильный синтаксис. Используйте `$set <staff_member> <closed_tickets>` или `$set all <closed_tickets>`")
            else:
                await message.channel.send("Эта команда доступна только для разработчиков!")
        
        if message.content.startswith('$sum'):
            await message.delete()
            if message.author.name.lower() in self.dev_members:
                args = message.content.split()
                if len(args) == 3:
                    staff_member = args[1].lower()
                    operation = args[2]
                    staff_members = self.config.get('staff_members', {})
                    if staff_member in staff_members:
                        try:
                            value = int(operation)
                            staff_members[staff_member]['closed_tickets'] += value
                            self.config['staff_members'] = staff_members
                            with open(self.config_file, 'w') as f:
                                json.dump(self.config, f, indent=4)
                            await message.channel.send(f"Успешно изменено значение для `{staff_member}` на `{operation}`")
                        except ValueError:
                            await message.channel.send("Неправильная операция. Используйте **целое** число")
                    else:
                        await message.channel.send(f"`{staff_member}` не из списка staff_member")
                else:
                    await message.channel.send("Неправильный синтаксис. Используйте `$sum <staff_member> <+число/-число>`")
            else:
                await message.channel.send("Эта команда доступна только для разработчиков!")

        if message.content.startswith('$config_clear'):
            await message.delete()
            if message.author.name.lower() in bot.dev_members:
                args = message.content.split()
                if len(args) > 1:
                    user = args[1].lower()
                    if user == 'all':
                        await message.channel.send(bot.config_clear())
                    else:
                        await message.channel.send(bot.config_clear(user))
                else:
                    await message.channel.send("Укажите пользователя или `all`, чтобы очистить `claimed_tickets | claimed_ticket_users` и пользователей.")
            else:
                await message.channel.send("Эта команда доступна только для разработчиков!")
        
        if message.content.startswith('$clear_tickets'):
            await message.delete()
            if message.author.name.lower() in self.staff_members:
                args = message.content.split()
                if len(args) > 1:
                    user = args[1].lower()
                    if user == 'all':
                        with open('created_tickets.json', 'w') as f:
                            json.dump({}, f)
                        await message.channel.send("Файл `created_tickets.json` очищен полностью.")
                    else:
                        with open('created_tickets.json', 'r+') as f:
                            try:
                                created_tickets = json.load(f)
                            except json.JSONDecodeError:
                                created_tickets = {}
                            if user in created_tickets:
                                del created_tickets[user]
                                f.seek(0)
                                json.dump(created_tickets, f)
                                f.truncate()
                                await message.channel.send(f"Запись пользователя `{user}` удалена из `created_tickets.json`.")
                            else:
                                await message.channel.send(f"Пользователь `{user}` не найден в `created_tickets.json`.")
                else:
                    await message.channel.send("Укажите ник пользователя или `all`, чтобы очистить `created_tickets.json`.")
            else:
                await message.channel.send("Эта команда доступна только для разработчиков!")
        
        if message.content.startswith('$rate_check'):
            await message.delete()
            args = message.content.split()
            if len(args) == 1:
                user_name = message.author.name.lower()
            else:
                user_name = args[1].lower()
            staff_members = bot.config.get('staff_members', {})
            if user_name in staff_members:
                likes = staff_members[user_name].get('likes', 0)
                dislikes = staff_members[user_name].get('dislikes', 0)
                rating = likes - dislikes
                embed = disnake.Embed(
                    title=f"Рейтинг {user_name}",
                    description=f"👍 Лайки: {likes}\n👎 Дизлайки: {dislikes}\n\n📊 Общий рейтинг: {rating}",
                    color=disnake.Color.from_rgb(119, 137, 253)
                )
                await message.channel.send(embed=embed)
            else:
                await message.channel.send(f"У {user_name} нет рейтинга, так как он не является сотрудником.")
        if message.content.startswith('$rate_clear'):
            await message.delete()
            if message.author.name.lower() in self.config.get('dev_members', []):
                staff_members = self.config.get('staff_members', {})
                for staff_member in staff_members:
                    staff_members[staff_member]['likes'] = 0
                    staff_members[staff_member]['dislikes'] = 0
                self.config['staff_members'] = staff_members
                with open(self.config_file, 'w') as f:
                    json.dump(self.config, f, indent=4)
                await message.channel.send("Оценки всех сотрудников были очищены.")
            else:
                await message.channel.send("У вас нет прав для использования этой команды")
        if message.content.startswith('$edit_rate'):
            await message.delete()
            user_name = message.author.name.lower()
            if message.author.name.lower() in self.config.get('dev_members', []):
                parts = message.content.split()
                if len(parts) != 4:
                    await message.channel.send("Неверный формат. Используйте: $edit_rate +(число) like (ник) или $edit_rate -(число) dislike (ник).")
                    return
                change_value = parts[1]
                rate_type = parts[2].lower()
                target_user_name = parts[3].lower()
                if target_user_name not in staff_members:
                    await message.channel.send("Целевой пользователь не найден.")
                    return
                likes = staff_members[target_user_name].get('likes', 0)
                dislikes = staff_members[target_user_name].get('dislikes', 0)
                if rate_type == 'like':
                    if change_value.startswith('+'):
                        likes += int(change_value[1:])
                    elif change_value.startswith('-'):
                        likes -= int(change_value[1:])
                elif rate_type == 'dislike':
                    if change_value.startswith('+'):
                        dislikes += int(change_value[1:])
                    elif change_value.startswith('-'):
                        dislikes -= int(change_value[1:])
                else:
                    await message.channel.send("Неверный тип рейтинга. Используйте 'like' или 'dislike'.")
                    return
                staff_members[target_user_name]['likes'] = likes
                staff_members[target_user_name]['dislikes'] = dislikes
                rating = likes - dislikes
                embed = disnake.Embed(
                    title=f"Рейтинг пользователя {target_user_name}",
                    description=f"👍 Лайки: {likes}\n👎 Дизлайки: {dislikes}\n\n📊 Общий рейтинг: {rating}",
                    color=disnake.Color.from_rgb(119, 137, 253)
                )
                await message.channel.send(embed=embed)
            else:
                await message.channel.send("У вас нет прав для изменения рейтинга.")
        
        if message.content.startswith('$config_date_clear'):
            await message.delete()
            if message.author.name.lower() in self.dev_members:
                self.config['date_stats'] = {}
                with open(self.config_file, 'w') as f:
                    json.dump(self.config, f, indent=4)
                await message.channel.send("Даты в date_stats были успешно очищены.")
            else:
                await message.channel.send("Эта команда доступна только для разработчиков!")

        if message.content.startswith('$claimedticket_clear'):
            if message.author.name.lower() in self.config.get('dev_members', []):
                self.config['claimed_tickets'] = {}
                with open(self.config_file, 'w') as f:
                    json.dump(self.config, f, indent=4)
                await message.channel.send("Данные о claimed_tickets были очищены.")
            else:
                await message.channel.send("Эта команда доступна только для разработчиков!")
        
        if message.content.startswith('$oldupdate_clear'):
            if message.author.name.lower() in self.config.get('dev_members', []):
                if 'ratings' in self.config:
                    del self.config['ratings']
                if 'average_ratings' in self.config:
                    del self.config['average_ratings']
                if 'user_ratings' in self.config:
                    del self.config['user_ratings']
                if 'qa_enabled' in self.config:
                    del self.config['qa_enabled']
                with open(self.config_file, 'w') as f:
                    json.dump(self.config, f, indent=4)
                if 'staff_members' not in self.config:
                    self.config['staff_members'] = []

                staff_members_dict = {}
                for member in self.config['staff_members']:
                    if isinstance(member, str):
                        staff_members_dict[member] = {'id': None, 'name': member, 'claimed_tickets': [], 'closed_tickets': 0}
                    elif isinstance(member, dict):
                        staff_members_dict[member['name']] = member

                self.config['staff_members'] = staff_members_dict
                with open(self.config_file, 'w') as f:
                    json.dump(self.config, f, indent=4)

                await message.channel.send("старая хуйня была удалена жоск <2.3 upd")
            else:
                await message.channel.send("Эта команда доступна только для разработчиков!")
#фаст ансверс биндс
        if message.content.startswith('.скинрейв'):
            if message.author.name.lower() in bot.config.get('staff_members', {}):
                await message.delete()
                await message.channel.send(f"Что бы мы вам помогли, уточните.\n1) Как давно вы зарегистрировались на SkinRave?\n2) Авторизировались ли вы под своим Steam аккаунтом?\n3) Ссылка на ваш аккаунт на сайте (yooma.su)\n4) Скриншот профиля на SkinRave. \n\n-# Отправил - {message.author.name}")
            else:
                pass
        if message.content.startswith('.админчат'):
            if message.author.name.lower() in bot.config.get('staff_members', {}):
                await message.delete()
                await message.channel.send(f'Чтобы написать сообщение в админ-чат.\n1) Откройте командный чат в игре (по умолчанию клавиша "U").\n2) Начните своё сообщение с символа @\nНапример: @Привет \n\n-# Отправил - {message.author.name}')
            else:
                pass
        if message.content.startswith('.ссылкасайт'):
            if message.author.name.lower() in bot.config.get('staff_members', {}):
                await message.delete()
                await message.channel.send(f'Чтобы получить ссылку на ваш профиль на сайте, выполните следующие шаги:\n1) Справа вверху нажмите на свой ник и аватарку (находится справа от баланса).\n2) В появившемся меню нажмите кнопку "Мой профиль".\n3) Скопируйте ссылку из адресной строки. \n\n-# Отправил - {message.author.name}')
            else:
                pass
        if message.content.startswith('.обнова'):
            if message.author.name.lower() in bot.config.get('staff_members', {}):
                await message.delete()
                await message.channel.send(f"Последнее обновление CS2 сломало работу серверов. Нужно время, чтобы решить проблемы и баги. Спасибо за понимание 💕 \n\n-# Отправил - {message.author.name}")
            else:
                pass

        if message.content.startswith('.жалоба'):
            if message.author.name.lower() in bot.config.get('staff_members', {}):
                await message.delete()
                await message.channel.send(f"Спасибо! Передали ваше обращение Администрации! \n\n-# Отправил - {message.author.name}")
            else:
                pass

        if message.content.startswith('.баг'):
            if message.author.name.lower() in bot.config.get('staff_members', {}):
                await message.delete()
                await message.channel.send(f"Спасибо! Передали информацию разработчику! \n\n-# Отправил - {message.author.name}")
            else:
                pass
            

        if message.content.startswith('.коины'):
            if message.author.name.lower() in bot.config.get('staff_members', {}):
                await message.delete()
                await message.channel.send(f"Коины используются на серверах.\nДля того чтобы их потратить используйте команду !shop на любом сервере проекта. \n\n-# Отправил - {message.author.name}")
            else:
                pass
        
        if message.content.startswith('.соцсети'):
            if message.author.name.lower() in bot.config.get('staff_members', {}):
                await message.delete()
                await message.channel.send(f"Все ссылки на наши актуальные соц. сети:\n\nDiscord: <https://ds.yooma.su>\nTelegram: <https://t.me/yoomasu>\nВКонтакте: <https://vk.com/yoomasu>\n\n-# Отправил - {message.author.name}")
            else:
                pass
        
        if message.content.startswith('.промоввод'):
            if message.author.name.lower() in bot.config.get('staff_members', {}):
                await message.delete()
                await message.channel.send(f'Для того чтобы активировать промокод, вам нужно нажать на свою аватарку в правом верхнем углу сайта и выбрать "ввести промокод".\n\n-# Отправил - {message.author.name}')
            else:
                pass
        
        if message.content.startswith('.блекджек'):
            if message.author.name.lower() in bot.config.get('staff_members', {}):
                await message.delete()
                await message.channel.send(f'Чтобы открыть игру, вам нужно написать команду !bj в чат игры на сервере\nПоcле этого в чате появится ссылка на игру. Вам необходимо выделить ее мышкой и нажать ПКМ, затем "Копировать выделенный текст".\nДалее зайти в обычный браузер (или в Steam браузер) и ввести эту ссылку туда, откроется игра\n\n-# Отправил - {message.author.name}')
            else:
                pass

    async def claim_ticket(self, message):
        user = message.author
        channel = message.channel
        self.ticket_counter += 1

        with open(self.config_file, 'w') as f:
            self.config['ticket_counter'] = self.ticket_counter
            json.dump(self.config, f, indent=4)

        ticket_channel = message.channel
        staff_members = bot.config.get('staff_members', {})
        staff_member_name = staff_members.get(user.name.lower(), {}).get('name', 'unknown')
        await ticket_channel.edit(name=f"{staff_member_name.lower()}-ticket-{ticket_channel.name.split('-')[-1]}")


        staff_members = self.config.get('staff_members', {})
        staff_members[user.name.lower()]['claimed_tickets'] = staff_members[user.name.lower()].get('claimed_tickets', []) + [ticket_channel.id]
        staff_members[user.name.lower()]['claimed_ticket_users'] = staff_members[user.name.lower()].get('claimed_ticket_users', {})
        staff_members[user.name.lower()]['claimed_ticket_users'][ticket_channel.id] = user.name.lower()
        self.config['staff_members'] = staff_members
        with open(self.config_file, 'w') as f:
            json.dump({str(k): v for k, v in self.config.items()}, f, indent=4, )

        info_embed = disnake.Embed(
            description=f"Успешно взялся за тикет - {user.mention}",
            color=disnake.Color.from_rgb(251, 254, 50)
        )
        await ticket_channel.send(embed=info_embed)

    async def close_ticket(self, message):  
        channel = message.channel
        user = message.author
        if "ticket" not in channel.name.lower():
            await message.channel.send("Эта команда доступна только в каналах с названием содержащим слово 'ticket'!")
            return
        staff_members = self.config.get('staff_members', {})
        ticket_claimer = None
        for staff_member, stats in staff_members.items():
            if channel.id in stats.get('claimed_tickets', []):
                ticket_claimer = staff_member
                break
        if ticket_claimer:
            staff_members[ticket_claimer]['closed_tickets'] = staff_members[ticket_claimer].get('closed_tickets', 0) + 1
            self.config['staff_members'] = staff_members
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)

            current_date = datetime.date.today().isoformat()
            if current_date not in self.config.get('date_stats', {}):
                self.config['date_stats'][current_date] = {}
            self.config['date_stats'][current_date][ticket_claimer] = self.config['date_stats'][current_date].get(ticket_claimer, 0) + 1
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)

            embed1 = disnake.Embed(
                description=f"Тикет был закрыт - {user.mention}",
                color=disnake.Color.from_rgb(251, 254, 50)
            )
            embed2 = disnake.Embed(
                description=f"Тикет будет удален через несколько секунд",
                color=disnake.Color.from_rgb(239, 82, 80)
            )
            await channel.send(embed=embed1)
            await channel.send(embed=embed2)
            await asyncio.sleep(4)
            await channel.delete()

    async def on_interaction(self, interaction: disnake.Interaction):
        if interaction.type == disnake.InteractionType.component:
            if interaction.data.custom_id == 'create_ticket': # type: ignore
                await self.create_ticket(interaction)
            elif interaction.component.custom_id == 'vip_service': # type: ignore
                embed = disnake.Embed(
                    title="Цены на VIP",
                    description="Цены на VIP услуги:",
                    color=disnake.Color.from_rgb(119, 137, 253)
                )
                
                vip_prices = bot.config.get('prices', {}).get('vip', {})
                vip_description = f"Medium - {vip_prices.get('medium', 'Нет цены')}\n"
                vip_description += f"Platinum - {vip_prices.get('platinum', 'Нет цены')}\n"
                vip_description += f"Crystal - {vip_prices.get('crystal', 'Нет цены')}\n"
                vip_description += f"Crystal+ - {vip_prices.get('crystal+', 'Нет цены')}\n"
                vip_description += "\n"
                if vip_prices.get('medium') and vip_prices.get('platinum'):
                    medium_price = vip_prices.get('medium', 'Нет цены').replace('р', '').replace('.', '')
                    platinum_price = vip_prices.get('platinum', 'Нет цены').replace('р', '').replace('.', '')
                    if medium_price != 'Нет цены' and platinum_price != 'Нет цены':
                        vip_description += f"**Докуп с Medium на Platinum:** {int(platinum_price) - int(medium_price)}р\n"
                vip_description += "\n"
                if vip_prices.get('medium') and vip_prices.get('crystal'):
                    medium_price = vip_prices.get('medium', 'Нет цены').replace('р', '').replace('.', '')
                    crystal_price = vip_prices.get('crystal', 'Нет цены').replace('р', '').replace('.', '')
                    if medium_price != 'Нет цены' and crystal_price != 'Нет цены':
                        vip_description += f"**Докуп с Medium на Crystal:** {int(crystal_price) - int(medium_price)}р\n"
                vip_description += "\n"
                if vip_prices.get('platinum') and vip_prices.get('crystal'):
                    platinum_price = vip_prices.get('platinum', 'Нет цены').replace('р', '').replace('.', '')
                    crystal_price = vip_prices.get('crystal', 'Нет цены').replace('р', '').replace('.', '')
                    if platinum_price != 'Нет цены' and crystal_price != 'Нет цены':
                        vip_description += f"**Докуп с Platinum на Crystal:** {int(crystal_price) - int(platinum_price)}р\n"
                vip_description += "\n"
                if vip_prices.get('crystal') and vip_prices.get('crystal+'):
                    crystal_price = vip_prices.get('crystal', 'Нет цены').replace('р', '').replace('.', '')
                    crystal_plus_price = vip_prices.get('crystal+', 'Нет цены').replace('р', '').replace('.', '')
                    if crystal_price != 'Нет цены' and crystal_plus_price != 'Нет цены':
                        vip_description += f"**Докуп с Crystal на Crystal+:** {int(crystal_plus_price) - int(crystal_price)}р\n"
                embed.add_field(name="ВИП", value=vip_description, inline=False)
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
            elif interaction.component.custom_id == 'admin_service': # type: ignore
                embed = disnake.Embed(
                    title="Цены на АДМ",
                    description="Цены на АДМ услуги:",
                    color=disnake.Color.from_rgb(119, 137, 253)
                )
                admin_prices = bot.config.get('prices', {}).get('admin', {})
                admin_description = f"1lvl - {admin_prices.get('1lvl', 'Нет цены')}\n"
                admin_description += f"2lvl - {admin_prices.get('2lvl', 'Нет цены')}\n"
                admin_description += f"Sponsor - {admin_prices.get('sponsor', 'Нет цены')}\n"
                admin_description += "\n"
                if admin_prices.get('1lvl') and admin_prices.get('2lvl'):
                    admin_1lvl_price = admin_prices.get('1lvl', 'Нет цены').replace('р', '').replace('.', '')
                    admin_2lvl_price = admin_prices.get('2lvl', 'Нет цены').replace('р', '').replace('.', '')
                    if admin_1lvl_price != 'Нет цены' and admin_2lvl_price != 'Нет цены':
                        admin_description += f"**Докуп с 1lvl на 2lvl:** {int(admin_2lvl_price) - int(admin_1lvl_price)}р\n"
                admin_description += "\n"
                if admin_prices.get('1lvl') and admin_prices.get('sponsor'):
                    admin_1lvl_price = admin_prices.get('1lvl', 'Нет цены').replace('р', '').replace('.', '')
                    sponsor_price = admin_prices.get('sponsor', 'Нет цены').replace('р', '').replace('.', '')
                    if admin_1lvl_price != 'Нет цены' and sponsor_price != 'Нет цены':
                        admin_description += f"**Докуп с 1lvl на Sponsor:** {int(sponsor_price) - int(admin_1lvl_price)}р\n"
                admin_description += "\n"
                if admin_prices.get('2lvl') and admin_prices.get('sponsor'):
                    admin_2lvl_price = admin_prices.get('2lvl', 'Нет цены').replace('р', '').replace('.', '')
                    sponsor_price = admin_prices.get('sponsor', 'Нет цены').replace('р', '').replace('.', '')
                    if admin_2lvl_price != 'Нет цены' and sponsor_price != 'Нет цены':
                        admin_description += f"**Докуп с 2lvl на Sponsor:** {int(sponsor_price) - int(admin_2lvl_price)}р\n"
                embed.add_field(name="АДМ", value=admin_description, inline=False)
                await interaction.response.send_message(embed=embed, ephemeral=True)

            elif interaction.component.custom_id == 'services':  # type: ignore
                embed = disnake.Embed(
                    title="Цены на СЕРВИСЫ",
                    description="Цены на сервисы:",
                    color=disnake.Color.from_rgb(119, 137, 253)
                )
                services_prices = bot.config.get('prices', {}).get('services', {})
                services_description = f"**Перенос вип/адм:** {services_prices.get('transfer', 'Нет цены')}\n"
                services_description += f"**Разморозка прав 1лвл:** {services_prices.get('unfreeze_admin_1', 'Нет цены')}\n"
                services_description += f"**Разморозка прав 2лвл:** {services_prices.get('unfreeze_admin_2lvl', 'Нет цены')}\n"
                services_description += f"**Разморозка прав спонсора:** {services_prices.get('unfreeze_sponsor', 'Нет цены')}\n"
                services_description += f"**Размут в чате на сайте:** {services_prices.get('unmute_site', 'Нет цены')}\n"  # Новая услуга
                services_description += f"**Разбан в дискорде:** {services_prices.get('unban_ds', 'Нет цены')}\n"           # Новая услуга
                
                embed.add_field(name="СЕРВИСЫ", value=services_description, inline=False)
                await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def create_ticket(self, interaction: disnake.Interaction):
        if interaction.user.name.lower() in self.config.get('dev_members', {}):
            pass
        elif interaction.user.name.lower() in self.config.get('staff_members', {}):
            await interaction.response.send_message(":x: / Вы не можете создавать тикеты, так как вы являетесь сотрудником.", ephemeral=True) # type: ignore
            return
        await interaction.response.defer()
        creating_ticket_msg = await interaction.followup.send(f":small_blue_diamond:  / **Создаю тикет...**", ephemeral=True)
        user = interaction.user
        creator_id = interaction.user.id
        guild = interaction.guild
        category = guild.get_channel(self.CATEGORY_ID) # type: ignore
        self.ticket_counter += 1
        
        with open(self.config_file, 'w') as f:
            self.config['ticket_counter'] = self.ticket_counter
            json.dump(self.config, f, indent=4)

        with open('created_tickets.json', 'r+') as f:
            try:
                created_tickets = json.load(f)
            except json.JSONDecodeError:
                created_tickets = {}

            user_name = interaction.user.name.replace('.', '') 
            if user_name in created_tickets and created_tickets[user_name].get('banned_until'):
                banned_until = created_tickets[user_name]['banned_until']
                banned_by = created_tickets[user_name].get('banned_by', 'Неизвестно')
                if banned_until > datetime.datetime.now().timestamp():
                    await creating_ticket_msg.edit(rf":small_orange_diamond:  \ Вы забанены в тикетах до **{datetime.datetime.fromtimestamp(banned_until).strftime('%Y-%m-%d %H:%M:%S')}**Заблокировал вас: {banned_by}") # type: ignore
                    return
                else:
                    del created_tickets[user_name]['banned_until']
                    del created_tickets[user_name]['banned_by']
                    f.seek(0)
                    json.dump(created_tickets, f)
                    f.truncate()
            user_name = interaction.user.name.replace('.', '') 
            if user_name in created_tickets and created_tickets[user_name]['ticket_id'] is not None:
                await creating_ticket_msg.edit(rf":small_orange_diamond:  \ **Вы уже создали тикет**. Ждите ответа от нашего персонала.") # type: ignore
                return

            ticket_channel = await category.create_text_channel(f"ticket-{self.ticket_counter}") # type: ignore
            await ticket_channel.set_permissions(guild.default_role, read_messages=False) # type: ignore
            staff_roles = self.config.get('staff_roles', [])
            for role_id in staff_roles:
                role = guild.get_role(role_id) # type: ignore
                if role:
                    await ticket_channel.set_permissions(role, read_messages=True, send_messages=True, mention_everyone=True)
            await ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True) # type: ignore
            

            created_tickets[user_name] = {'ticket_id': ticket_channel.id, 'creator_id': interaction.user.id}
            f.seek(0)
            json.dump(created_tickets, f, indent=4)
            f.truncate()

        embed = disnake.Embed(
            title="Спасибо за ваше обращение в клиентскую поддержку!",
            description="Спасибо за ваше обращение. Пожалуйста, **опишите суть вашей проблемы подробнее**, чтобы мы могли оказать вам **наилучшее решение**.\n\n"
            "▎Важные моменты:\n"
            "- Не открывайте тикеты, которые не соответствуют указанной теме или не связаны с описанной проблемой.\n"
            "- Укажите все необходимые данные, чтобы мы могли оперативно решить ваш вопрос.\n"
            "- Соблюдайте правила общения, чтобы избежать блокировки доступа к созданию запросов.\n\n"
            "**Несоблюдение этих правил может привести к наказанию**.",
            color=disnake.Color.from_rgb(119, 137, 253)
        )
        embed.set_author(name='Yooma Support', icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
        embed.set_thumbnail(url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
        view = ButtonView()
        take_ticket_button = disnake.ui.Button(label='Взять тикет', style=disnake.ButtonStyle.blurple, emoji='📝')
        close_ticket_button = disnake.ui.Button(label='Закрыть тикет', style=disnake.ButtonStyle.red, emoji='🔒')
        view.add_item(take_ticket_button)   
        view.add_item(close_ticket_button)

        await ticket_channel.send(user.mention, embed=embed, view=view)
        current_time = datetime.datetime.now()
        primetime = self.config.get('primetime')
        if primetime:
            start_time = datetime.datetime.strptime(primetime['start'], '%H:%M').time()
            end_time = datetime.datetime.strptime(primetime['end'], '%H:%M').time()
            if start_time <= current_time.time() <= end_time:
                pass
            else:
                await ticket_channel.send(f"{interaction.user.mention}, В данный момент нерабочее время, и время ответа может занять больше времени, чем обычно.\nПожалуйста, оставайтесь на связи, и мы ответим вам, как только сможем.")
        else:
            pass    
        await creating_ticket_msg.edit(rf":tickets:  \ **Ваш тикет был создан - **{ticket_channel.mention}") # type: ignore

        take_ticket_lock = asyncio.Lock()

        async def take_ticket_callback(interaction: disnake.Interaction):
            user = interaction.user
            self.ticket_claimer_id = interaction.user.id # type: ignore
            staff_members = bot.config.get('staff_members', {})

            if user.name.lower() not in staff_members:
                await interaction.response.send_message("У вас нет прав для совершения данного действия.", ephemeral=True)
                return

            ticket_channel = interaction.channel

            async with take_ticket_lock:
                ticket_claimed = bot.config.get('claimed_tickets', {}).get(ticket_channel.id)
                if ticket_claimed:
                    await interaction.response.send_message("Этот тикет уже взят другим сотрудником.", ephemeral=True)
                    return
                
                staff_member_name = staff_members[user.name.lower()].get('name', 'unknown')

                await ticket_channel.edit(name=f"{staff_member_name.lower()}-ticket-{ticket_channel.name.split('-')[-1]}") # type: ignore

                bot.config.setdefault('claimed_tickets', {})[ticket_channel.id] = user.name.lower()
                staff_members[user.name.lower()]['claimed_tickets'] = staff_members[user.name.lower()].get('claimed_tickets', []) + [ticket_channel.id]

                with open(bot.config_file, 'w') as f:
                    json.dump(bot.config, f, indent=4)

                await interaction.message.edit(view=None) # type: ignore
                close_button = disnake.ui.Button(label="Закрыть тикет", style=disnake.ButtonStyle.red, emoji='🔒')
                close_button.callback = close_ticket_callback
                view = disnake.ui.View(timeout=None)
                view.add_item(close_button)
                await interaction.message.edit(view=view) # type: ignore

                info_embed = disnake.Embed(
                    description=f"Успешно взялся за тикет - {user.mention}",
                    color=disnake.Color.from_rgb(251, 254, 50)
                )
                await ticket_channel.send(embed=info_embed)

                await interaction.response.defer()

        async def close_ticket_callback(interaction: disnake.Interaction):
            ticket_channel = interaction.channel
            user = interaction.user

            channel_name = ticket_channel.name # type: ignore
            staff_member_name = None
            if '-' in channel_name:
                parts = channel_name.split('-')
                staff_member_name = parts[0]

            confirmation_embed = disnake.Embed(
                title="Подтверждение",
                description="Вы уверены что хотите закрыть тикет?",
                color=disnake.Color.from_rgb(119, 137, 253)
            )

            view = ButtonView()

            view.clear_items()

            button_close = disnake.ui.Button(label='Закрыть', style=disnake.ButtonStyle.red, emoji='🔒')
            button_close_with_reason = disnake.ui.Button(label='Закрыть с причиной', style=disnake.ButtonStyle.red, emoji='🔒')
            button_cancel = disnake.ui.Button(label='Отмена', style=disnake.ButtonStyle.gray, emoji='🚫')
            view.add_item(button_close)
            view.add_item(button_close_with_reason)
            view.add_item(button_cancel)
    
            await interaction.response.send_message(embed=confirmation_embed, view=view)

            async def close_callback(interaction: disnake.Interaction):
                channel = interaction.channel
                user = interaction.user
                staff_members = bot.config.get('staff_members', {})

                ticket_claimer = None
                for staff_member, stats in staff_members.items():
                    if channel.id in stats.get('claimed_tickets', []):
                        ticket_claimer = staff_member
                        break

                if ticket_claimer:
                    staff_members[ticket_claimer]['claimed_tickets'].remove(channel.id)

                    staff_members[ticket_claimer]['closed_tickets'] = staff_members[ticket_claimer].get('closed_tickets', 0) + 1
                    bot.config['staff_members'] = staff_members
                    with open(bot.config_file, 'w') as f:
                        json.dump(bot.config, f)

                    current_date = datetime.date.today().isoformat()
                    if current_date not in bot.config.get('date_stats', {}):
                        bot.config['date_stats'][current_date] = {}
                    bot.config['date_stats'][current_date][ticket_claimer] = bot.config['date_stats'][current_date].get(ticket_claimer, 0) + 1
                    with open(bot.config_file, 'w') as f:
                        json.dump(bot.config, f)

                    with open(bot.config_file, 'r') as f:
                        config = json.load(f)
                    config['ticket_counter'] -= 1
                    with open(bot.config_file, 'w') as f:
                        json.dump(config, f)

                with open('created_tickets.json', 'r+') as f:
                    try:
                        created_tickets = json.load(f)
                    except json.JSONDecodeError:
                        created_tickets = {}

                    for user_name, ticket_info in created_tickets.items():
                        if ticket_info['ticket_id'] == channel.id:
                            if ticket_claimer:
                                creator = bot.get_user(ticket_info['creator_id']) or await bot.fetch_user(ticket_info['creator_id'])
                                if creator:
                                    server_name = "yooma.su"
                                    ticket_id = f"**#{channel.name.split('-')[-1]}**" #type: ignore
                                    opened_by = creator.mention
                                    closed_by = interaction.user.mention
                                    embed = disnake.Embed(
                                        title="Ваш тикет был закрыт",
                                        timestamp=datetime.datetime.now(),
                                        color=disnake.Color.from_rgb(119, 137, 253)
                                    )
                                    embed.add_field(name=":id: Ticket ID", value=ticket_id, inline=True)
                                    embed.add_field(name=":unlock: Открыл", value=opened_by, inline=True)
                                    embed.add_field(name=":lock: Закрыл", value=closed_by, inline=True)
                                    embed.add_field(name="", value="", inline=False)
                                    embed.add_field(name=":mag_right: Взял тикет", value=f"<@{staff_members[ticket_claimer]['id']}>", inline=True)
                                    embed.add_field(name="Пожалуйста оцените работу сотрудника", value="", inline=False)
                                    embed.set_author(name=server_name, icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")

                                    thumbs_down = disnake.ui.Button(label='', style=disnake.ButtonStyle.red, emoji='👎🏻')
                                    thumbs_up = disnake.ui.Button(label='', style=disnake.ButtonStyle.green, emoji='👍🏻')

                                    view = ButtonView()
                                    view.add_item(thumbs_down)
                                    view.add_item(thumbs_up)

                                    async def like_callback(interaction):
                                        if ticket_claimer not in staff_members:
                                            staff_members[ticket_claimer] = {'likes': 0, 'dislikes': 0}
                                            
                                        if 'likes' not in staff_members[ticket_claimer]:
                                            staff_members[ticket_claimer]['likes'] = 0
                                        staff_members[ticket_claimer]['likes'] += 1 

                                        bot.config['staff_members'] = staff_members 
                                        with open(bot.config_file, 'w') as f: 
                                            json.dump(bot.config, f) 

                                        await interaction.message.edit(view=None)
                                        await interaction.response.send_message("Ваш 👍🏻 был учтён. Спасибо за обратную связь!", ephemeral=True)

                                        user_id = bot.config['staff_members'][ticket_claimer]['id']
                                        user = bot.get_user(int(user_id)) or await bot.fetch_user(int(user_id))
                                        if user:
                                            if bot.config.get('alert_settings', {}).get(ticket_claimer, False):
                                                await user.send(f"Вам поставили: 👍🏻 . Поставил оценку {interaction.user.mention}")
                                        else:
                                            pass

                                    async def dislike_callback(interaction):
                                        if ticket_claimer not in staff_members:
                                            staff_members[ticket_claimer] = {'likes': 0, 'dislikes': 0}
                                            
                                        if 'dislikes' not in staff_members[ticket_claimer]:
                                            staff_members[ticket_claimer]['dislikes'] = 0
                                        staff_members[ticket_claimer]['dislikes'] += 1 

                                        bot.config['staff_members'] = staff_members 
                                        with open(bot.config_file, 'w') as f: 
                                            json.dump(bot.config, f) 

                                        await interaction.message.edit(view=None)
                                        await interaction.response.send_message("Ваш 👎🏻 был учтён. Спасибо за обратную связь!", ephemeral=True)
                                        user_id = bot.config['staff_members'][ticket_claimer]['id']
                                        user = bot.get_user(int(user_id)) or await bot.fetch_user(int(user_id))
                                        if user:
                                            if bot.config.get('alert_settings', {}).get(ticket_claimer, False):
                                                await user.send(f"Вам поставили: 👎🏻 . Поставил оценку {interaction.user.mention}")
                                        else:
                                            pass
                                    thumbs_down.callback = dislike_callback
                                    thumbs_up.callback = like_callback
                                    await creator.send(embed=embed, view=view)
                            del created_tickets[user_name]
                            f.seek(0)
                            json.dump(created_tickets, f)
                            f.truncate()
                            break

                embed1 = disnake.Embed(
                    description=f"Тикет был закрыт - {user.mention}",
                    color=disnake.Color.from_rgb(251, 254, 50)
                )
                embed2 = disnake.Embed(
                    description=f"Тикет будет удален через несколько секунд",
                    color=disnake.Color.from_rgb(239, 82, 80)
                )
                await interaction.response.defer()
                await interaction.message.delete() # type: ignore # type: ignore
                await channel.send(embed=embed1)
                await channel.send(embed=embed2)
                await asyncio.sleep(4)
                await channel.delete() # type: ignore
                
            
            async def close_with_reason_callback(interaction: disnake.Interaction):
                staff_members = bot.config.get('staff_members', {}) 
                if interaction.user.name.lower() not in staff_members:
                    await interaction.response.send_message("У вас нет прав для совершения данного действия.", ephemeral=True)
                    return
                else:
                    user = interaction.user
                    staff_members = bot.config.get('staff_members', {})

                    current_date = datetime.date.today().isoformat()
                    if current_date not in bot.config.get('date_stats', {}):
                        bot.config['date_stats'][current_date] = {}
                    bot.config['date_stats'][current_date][user.name.lower()] = bot.config['date_stats'][current_date].get(user.name.lower(), 0) + 1
                    staff_members[user.name.lower()]['closed_tickets'] = staff_members[user.name.lower()].get('closed_tickets', 0) + 1
                    bot.config['staff_members'] = staff_members
                    with open(bot.config_file, 'w') as f:
                        json.dump(bot.config, f)
                    await interaction.response.send_modal(
                        title="Причина закрытия тикета",
                        custom_id="close_with_reason",
                        components=[
                            disnake.ui.TextInput(
                                style=disnake.TextInputStyle.paragraph,
                                label="Причина",
                                placeholder="Введите причину закрытия тикета",
                                custom_id="reason",
                            )
                        ]
                    )


            @bot.event
            async def on_modal_submit(interaction: disnake.ModalInteraction):
                if interaction.data.custom_id == "close_with_reason":
                    for component in interaction.data['components'][0]['components']:
                        if component['custom_id'] == 'reason':
                            reason = component['value']
                            break

                    channel = interaction.channel
                    user = interaction.user
                    staff_members = bot.config.get('staff_members', {})

                    ticket_claimer = None
                    for staff_member, stats in staff_members.items():
                        if channel.id in stats.get('claimed_tickets', []):
                            ticket_claimer = staff_member
                            break

                    if ticket_claimer:
                        staff_members[ticket_claimer]['claimed_tickets'].remove(channel.id)

                        #staff_members[ticket_claimer]['closed_tickets'] = staff_members[ticket_claimer].get('closed_tickets', 0) + 1
                        bot.config['staff_members'] = staff_members
                        with open(bot.config_file, 'w') as f:
                            json.dump(bot.config, f)

                        current_date = datetime.date.today().isoformat()
                        if current_date not in bot.config.get('date_stats', {}):
                            bot.config['date_stats'][current_date] = {}
                        #bot.config['date_stats'][current_date][ticket_claimer] = bot.config['date_stats'][current_date].get(ticket_claimer, 0) + 1
                        with open(bot.config_file, 'w') as f:
                            json.dump(bot.config, f)

                        with open(bot.config_file, 'r') as f:
                            config = json.load(f)
                        #config['ticket_counter'] -= 1
                        with open(bot.config_file, 'w') as f:
                            json.dump(config, f)

                    with open('created_tickets.json', 'r+') as f:
                        try:
                            created_tickets = json.load(f)
                        except json.JSONDecodeError:
                            created_tickets = {}

                        for user_name, ticket_info in created_tickets.items():
                            if ticket_info['ticket_id'] == channel.id:
                                if ticket_claimer:
                                    creator = bot.get_user(ticket_info['creator_id']) or await bot.fetch_user(ticket_info['creator_id'])
                                    server_name = "yooma.su"
                                    ticket_id = f"**#{channel.name.split('-')[-1]}**" #type: ignore
                                    opened_by = creator.mention
                                    closed_by = interaction.user.mention
                                    claimed_by = ticket_claimer
                                    embed = disnake.Embed(
                                        title="Ваш тикет был закрыт",
                                        timestamp=datetime.datetime.now(),
                                        color=disnake.Color.from_rgb(119, 137, 253)
                                    )
                                    embed.add_field(name=":id: Ticket ID", value=ticket_id, inline=True)
                                    embed.add_field(name=":unlock: Открыл", value=opened_by, inline=True)
                                    embed.add_field(name=":lock: Закрыл", value=closed_by, inline=True)
                                    embed.add_field(name="", value="", inline=False)
                                    embed.add_field(name=":mag_right: Взял тикет", value=f"<@{staff_members[ticket_claimer]['id']}>", inline=True)
                                    embed.add_field(name=":pencil: Сообщение", value=reason, inline=False)
                                    embed.add_field(name="Пожалуйста оцените работу сотрудника", value="", inline=False)
                                    embed.set_author(name=server_name, icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")

                                    thumbs_down = disnake.ui.Button(label='', style=disnake.ButtonStyle.red, emoji='👎🏻')
                                    thumbs_up = disnake.ui.Button(label='', style=disnake.ButtonStyle.green, emoji='👍🏻')

                                    view = ButtonView()
                                    view.add_item(thumbs_down)
                                    view.add_item(thumbs_up)

                                    async def like_callback(interaction):
                                        if ticket_claimer not in staff_members:
                                            staff_members[ticket_claimer] = {'likes': 0, 'dislikes': 0}
                                        
                                        if 'likes' not in staff_members[ticket_claimer]:
                                            staff_members[ticket_claimer]['likes'] = 0
                                        staff_members[ticket_claimer]['likes'] += 1 

                                        bot.config['staff_members'] = staff_members 
                                        with open(bot.config_file, 'w') as f: 
                                            json.dump(bot.config, f) 

                                        await interaction.message.edit(view=None)
                                        await interaction.response.send_message("Ваш 👍🏻 был учтён. Спасибо за обратную связь!", ephemeral=True)

                                    async def dislike_callback(interaction):
                                        if ticket_claimer not in staff_members:
                                            staff_members[ticket_claimer] = {'likes': 0, 'dislikes': 0}
                                        
                                        if 'dislikes' not in staff_members[ticket_claimer]:
                                            staff_members[ticket_claimer]['dislikes'] = 0
                                        staff_members[ticket_claimer]['dislikes'] += 1 

                                        bot.config['staff_members'] = staff_members 
                                        with open(bot.config_file, 'w') as f: 
                                            json.dump(bot.config, f) 

                                        await interaction.message.edit(view=None)
                                        await interaction.response.send_message("Ваш 👎🏻 был учтён. Спасибо за обратную связь!", ephemeral=True)
                                    thumbs_down.callback = dislike_callback
                                    thumbs_up.callback = like_callback
                                    await creator.send(embed=embed, view=view)
                                del created_tickets[user_name]
                                f.seek(0)
                                json.dump(created_tickets, f)
                                f.truncate()
                                break

                    embed1 = disnake.Embed(
                        description=f"Тикет был закрыт - {user.mention}",
                        color=disnake.Color.from_rgb(251, 254, 50)
                    )
                    embed2 = disnake.Embed(
                        description=f"Тикет будет удален через несколько секунд",
                        color=disnake.Color.from_rgb(239, 82, 80)
                    )
                    await interaction.response.defer()
                    await interaction.message.delete() # type: ignore
                    await channel.send(embed=embed1)
                    await channel.send(embed=embed2)
                    await asyncio.sleep(4)
                    await channel.delete() # type: ignore
                
            async def cancel_callback(interaction: disnake.Interaction):
                await interaction.message.delete() # type: ignore     

            button_close_with_reason.callback = close_with_reason_callback
            button_close.callback = close_callback
            button_cancel.callback = cancel_callback


        take_ticket_button.callback = take_ticket_callback
        close_ticket_button.callback = close_ticket_callback

bot = PersistentViewBot(activity=disnake.Activity(type=disnake.ActivityType.competing, name="yooma.su"))

if __name__ == "__main__":
    bot.run("MTI3Mzk1NzgzNTI1MTc4MTY0Mg.GQXk0n.2okk4H31AB54DXaa7bllRyMdyp7cK61IcS3MJo")