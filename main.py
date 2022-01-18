import discord
import os
import uuid
from replit import db
import keep_alive

command_list = '''Eu respondo você pelos seguintes comandos:
!ajuda - Listo todos os meus comandos.
!all_tasks - Listo todas as tasks semanais e a pontuação de cada uma.
!my_tasks - Listo as tasks que você já fez, as que faltam fazer, e a sua pontuação.
!do_task NUMERO - Diz pra mim qual o número da task que você fez.
!undo_task NUMERO - Puts, marcou errado? Fala pra mim o número que eu cancelo ela!
'''

adm_command_list = '''Aqui é o grupo dos adms e os comandos são tops!
!all_tasks - lista as tasks
!add_task PONTOS DESCRICAO - diga a pontuação e fale sobre a task
!del_task ID - deleta a task com o id indicado.
!reset_points - reseta as tasks de todo mundo.
!all_users - lista os usuarios e as pontuacoes de cada um.
!info_user USER_ID - mostra as tasks feitas do usuário de id indicado.
!clear_tasks - apaga todas as tasks (CUIDADO)
'''

client = discord.Client()


class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        if message.author == client.user:
            return

        # comandos de DM
        if message.author.dm_channel and message.channel.id == message.author.dm_channel.id:
            if message.content.startswith(('!ajuda', '!bot')):
                await message.channel.send(command_list)
                return
            if message.content.startswith('!all_tasks'):
                if 'tasks' not in db or len(db['tasks']) == 0:
                    await message.channel.send('Nenhuma task cadastrada!')
                    return
                task_list_message = [
                    f"{i+1}: {task['name']} - ({task['points']} pontos)"
                    for (i, task) in enumerate(db['tasks'].values())
                ]
                await message.channel.send('\n'.join(task_list_message))
                return
            if message.content.startswith('!my_tasks'):
                user = db['users'].get(str(message.author.id))
                if not user: 
                    await message.channel.send('Eita! não te encontramos! Vá no chat do grupo e manda um !bot por favor')
                    return
                tasks_done = [
                    f"- {i+1}: {task['name']} - ({task['points']} pontos)"
                    for i, (id, task) in enumerate(db['tasks'].items()) if id in user['tasks']
                ]
                if len(tasks_done) > 0:
                    tasks_done = '\n'.join(tasks_done)
                else:
                    tasks_done = '- Sem tasks feitas!'
                tasks_todo = [
                    f"- {i+1}: {task['name']} - ({task['points']} pontos)"
                    for i, (id, task) in enumerate(db['tasks'].items()) if id not in user['tasks']
                ]
                if len(tasks_todo) > 0:
                    tasks_todo = '\n'.join(tasks_todo)
                else:
                    tasks_todo = '- Sem tasks para fazer!'
                res = f'''Pontos: {user['points']}

Tasks feitas:
{tasks_done}

Tasks para fazer:
{tasks_todo}
'''
                await message.channel.send(res)
                return
            if message.content.startswith('!do_task'):
                message_list = message.content.split()
                if len(message_list) == 1:
                    await message.channel.send('Favor indicar número da task!')
                    return
                task_num = message_list[1]
                if not task_num.isdigit() or int(task_num) == 0:
                    await message.channel.send('Task não existe!')
                    return
                task_num = int(task_num)
                task_list = list(db['tasks'].items())
                if len(task_list) < task_num:
                    await message.channel.send('Task não existe!')
                    return
                task = task_list[task_num-1]
                if not task:
                    await message.channel.send('Task não existe!')
                    return
                user = db['users'].get(str(message.author.id))
                if not user: 
                    await message.channel.send('Eita! não te encontramos! Vá no chat do grupo e manda um !bot por favor')
                    return
                if task[0] in user['tasks']:
                    await message.channel.send('Task já foi feita!')
                    return
                user['tasks'].append(task[0])
                user['points'] += task[1]['points']
                await message.channel.send(f"Pronto, contabilizamos os seus {task[1]['points']} por você ter feito a task {task_num}: {task[1]['name']}")
                return

            if message.content.startswith('!undo_task'):
                message_list = message.content.split()
                if len(message_list) == 1:
                    await message.channel.send('Favor indicar número da task!')
                    return
                task_num = message_list[1]
                if not task_num.isdigit() or int(task_num) == 0:
                    await message.channel.send('Task não existe!')
                    return
                task_num = int(task_num)
                task_list = list(db['tasks'].items())
                if len(task_list) < task_num:
                    await message.channel.send('Task não existe!')
                    return
                task = task_list[task_num-1]
                if not task:
                    await message.channel.send('Task não existe!')
                    return
                user = db['users'].get(str(message.author.id))
                if not user: 
                    await message.channel.send('Eita! não te encontramos! Vá no chat do grupo e manda um !bot por favor')
                    return
                if task[0] not in user['tasks']:
                    await message.channel.send('Task não foi feita ainda!')
                    return
                user['tasks'].remove(task[0])
                user['points'] -= task[1]['points']
                await message.channel.send(f"Pronto, removemos a task {task_num}: {task[1]['name']}")
                return
            await message.channel.send('Opa, não reconheço esse comando. Manda um !ajuda para ver como posso interagir com você!')
            return
        else:
            # comandos de adm
            if len(message.channel.changed_roles) > 0 and filter(
                    lambda r: r.name == 'Bot Manager',
                    message.channel.changed_roles):
                if message.content.startswith(('!help','!ajuda')):
                    await message.channel.send(adm_command_list)
                    return
                if message.content.startswith('!all_tasks'):
                    if 'tasks' not in db or len(db['tasks']) == 0:
                        await message.channel.send('Nenhuma task cadastrada!')
                        return
                    task_list_message = [
                        f"{i+1}: {task['name']} - ({task['points']}) pontos - id: {id}"
                        for i, (id, task) in enumerate(db['tasks'].items())
                    ]
                    await message.channel.send('\n'.join(task_list_message))
                    return
                if message.content.startswith('!clear_tasks'):
                    await message.channel.send('Tasks apagadas!')
                    db['tasks'] = {}
                    for id in db['users'].keys():
                      db['users'][id]['points'] = 0
                      db['users'][id]['tasks'] = []
                    await message.channel.send('Tudo apagado :(')
                    return
                if message.content.startswith('!add_task'):
                    message_list = message.content.split(' ', 2)
                    if len(message_list) != 3:
                      await message.channel.send('Por favor, fornecer o número de pontos e a descrição da task nessa ordem.')
                      return
                    if not message_list[1].isdigit():
                      await message.channel.send('A pontuação precisa ser um número inteiro positivo.')
                      return
                    id = str(uuid.uuid4())
                    db['tasks'][id] = {
                      'points': int(message_list[1]),
                      'name': message_list[2]
                    }
                    await message.channel.send(f"A task {db['tasks'][id]['name']} de pontuação {db['tasks'][id]['points']} e id {id} foi adicionada com sucesso!")
                    return
                if message.content.startswith('!del_task'):
                    message_list = message.content.split(' ')
                    if len(message_list) != 2:
                        await message.channel.send('Por favor, fornecer o id da task a ser apagada')
                        return
                    task_id = message_list[1]
                    task = db['tasks'].get(task_id)
                    if not task:
                        await message.channel.send('Task não encontrada')
                        return
                    for (user_id, user) in db['users'].items():
                        if task_id in user['tasks']:
                            db['users'][user_id]['tasks'].remove(task_id)
                            db['users'][user_id]['points'] -= int(task['points'])
                    del db['tasks'][task_id]
                    await message.channel.send('Task apagada.')
                    return
                if message.content.startswith('!reset_points'):
                    for id in db['users'].keys():
                      db['users'][id]['points'] = 0
                      db['users'][id]['tasks'] = []
                    await message.channel.send('Pontos e tasks dos usuários resetados!')
                    return
                if message.content.startswith('!all_users'):
                    user_list_message = [f"{user['name']} - points: {user['points']} - id: {id}" for (id, user) in list(db['users'].items())]
                    if len(user_list_message) == 0:
                        await message.channel.send('Sem usuários cadastrados')
                        return
                    await message.channel.send('\n'.join(user_list_message))
                    return
                if message.content.startswith('!info_user'):
                    message_list = message.content.split(' ')
                    if len(message_list) != 2:
                        await message.channel.send('Por favor, fornecer o id do user')
                        return
                    user = db['users'].get(str(message_list[1]))
                    if not user: 
                        await message.channel.send('Usuário não encontrado')
                        return
                    tasks_done = [
                        f"- {i+1}: {task['name']} - ({task['points']} pontos)"
                        for i, (id, task) in enumerate(db['tasks'].items()) if id in user['tasks']
                    ]
                    if len(tasks_done) > 0:
                        tasks_done = '\n'.join(tasks_done)
                    else:
                        tasks_done = '- Sem tasks feitas!'
                    tasks_todo = [
                        f"- {i+1}: {task['name']} - ({task['points']} pontos)"
                        for i, (id, task) in enumerate(db['tasks'].items()) if id not in user['tasks']
                    ]
                    if len(tasks_todo) > 0:
                        tasks_todo = '\n'.join(tasks_todo)
                    else:
                        tasks_todo = '- Sem tasks para fazer!'
                    res = f'''Usuário: {user['display_name']} - {user['name']} - {message_list[1]}
Pontos: {user['points']}

Tasks feitas:
{tasks_done}

Tasks para fazer:
{tasks_todo}
'''
                    await message.channel.send(res)
                    return

            # comandos públicos
            if message.content.startswith('!bot'):
                await message.author.send(
                    f'Oi, {message.author.display_name}. Vi que me chamou! Vamos começar então!'
                )
                if 'users' not in db: db['users'] = {}
                if message.author.id not in db['users']:
                    db['users'][message.author.id] = {
                        'name': message.author.name,
                        'display_name': message.author.display_name,
                        'tasks': [],
                        'points': 0
                    }
                    await message.author.send(f'Pronto {message.author.display_name}, agora você já pode fazer tasks e interagir comigo!')
                await message.author.send(command_list)
                return
            if message.content.startswith(('!help', '!ajuda')):
                await message.channel.send(
                    'Opa, tudo bom? Eu sou o BOT da República NFT! Para interagir comigo, use o comando !bot que te chamarei na DM com mais informações!'
                )
                return



client = MyClient()
my_secret = os.environ['TOKEN']
keep_alive.keep_alive()
client.run(my_secret)
