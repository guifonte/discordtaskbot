import discord
import os
import uuid
from replit import db
import keep_alive

command_list = '''Eu respondo você pelos seguintes comandos:
**!ajuda** - Listo todos os meus comandos.
**!tarefas** - Listo todas as tarefas semanais e a pontuação de cada uma.
**!minhas-tarefas** - Listo as tarefas que você já fez, as que faltam fazer, e a sua pontuação.
**!fazer-tarefa** NÚMERO - Diz pra mim qual o número da tarefa que você fez.
**!desfazer-tarefa** NÚMERO - Puts, marcou errado? Fala pra mim o número que eu cancelo ela!
'''

adm_command_list = '''Aqui é o grupo dos administradores e os comandos são tops!
**!ajuda** - Listo todos os meus comandos de administrador.
**!tarefas** - lista as tarefas.
**!adicionar-tarefa** PONTOS DESCRICAO - diga a pontuação e fale sobre a tarefa
**!apagar-tarefa** ID - deleta a tarefa com o id indicado.
**!editar-tarefa** ID PONTOS DESCRIÇÃO - edita a tarefa com o id indicado.
**!resetar-pontos** - reseta as tarefas de todo mundo.
**!usuarios** - lista os usuários e as pontuações de cada um.
**!info-usuario** USER_ID - mostra as tarefas feitas do usuário de id indicado.
**!limpar-tarefas** - apaga todas as tarefas (CUIDADO)
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
            if message.content.startswith('!tarefas'):
                if 'tasks' not in db or len(db['tasks']) == 0:
                    await message.channel.send('Nenhuma tarefa cadastrada!')
                    return
                task_list_message = [
                    f"{i+1}: {task['name']} - ({task['points']} pontos)"
                    for (i, task) in enumerate(db['tasks'].values())
                ]
                await message.channel.send('\n'.join(task_list_message))
                return
            if message.content.startswith('!minhas-tarefas'):
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
                    tasks_done = '- Sem tarefas feitas!'
                tasks_todo = [
                    f"- {i+1}: {task['name']} - ({task['points']} pontos)"
                    for i, (id, task) in enumerate(db['tasks'].items()) if id not in user['tasks']
                ]
                if len(tasks_todo) > 0:
                    tasks_todo = '\n'.join(tasks_todo)
                else:
                    tasks_todo = '- Sem tarefas para fazer!'
                res = f'''Pontos: {user['points']}

Tarefas feitas:
{tasks_done}

Tarefas para fazer:
{tasks_todo}
'''
                await message.channel.send(res)
                return
            if message.content.startswith('!fazer-tarefa'):
                message_list = message.content.split()
                if len(message_list) == 1:
                    await message.channel.send('Favor indicar número da tarefa!')
                    return
                task_num = message_list[1]
                if not task_num.isdigit() or int(task_num) == 0:
                    await message.channel.send('Tarefa não existe!')
                    return
                task_num = int(task_num)
                task_list = list(db['tasks'].items())
                if len(task_list) < task_num:
                    await message.channel.send('Tarefa não existe!')
                    return
                task = task_list[task_num-1]
                if not task:
                    await message.channel.send('Tarefa não existe!')
                    return
                user = db['users'].get(str(message.author.id))
                if not user: 
                    await message.channel.send('Eita! não te encontramos! Vá no chat do grupo e manda um !bot por favor')
                    return
                if task[0] in user['tasks']:
                    await message.channel.send('Tarefa já foi feita!')
                    return
                user['tasks'].append(task[0])
                user['points'] += task[1]['points']
                await message.channel.send(f"Pronto, contabilizamos os seus {task[1]['points']} por você ter feito a tarefa {task_num}: {task[1]['name']}")
                return

            if message.content.startswith('!desfazer-tarefa'):
                message_list = message.content.split()
                if len(message_list) == 1:
                    await message.channel.send('Favor indicar número da tarefa!')
                    return
                task_num = message_list[1]
                if not task_num.isdigit() or int(task_num) == 0:
                    await message.channel.send('Tarefa não existe!')
                    return
                task_num = int(task_num)
                task_list = list(db['tasks'].items())
                if len(task_list) < task_num:
                    await message.channel.send('Tarefa não existe!')
                    return
                task = task_list[task_num-1]
                if not task:
                    await message.channel.send('Tarefa não existe!')
                    return
                user = db['users'].get(str(message.author.id))
                if not user: 
                    await message.channel.send('Eita! não te encontramos! Vá no chat do grupo e manda um !bot por favor')
                    return
                if task[0] not in user['tasks']:
                    await message.channel.send('Tarefa não foi feita ainda!')
                    return
                user['tasks'].remove(task[0])
                user['points'] -= task[1]['points']
                await message.channel.send(f"Pronto, removemos a Tarefa {task_num}: {task[1]['name']}")
                return
            await message.channel.send('Opa, não reconheço esse comando. Manda um !ajuda para ver como posso interagir com você!')
            return
        else:
            # comandos de adm
            if len(message.channel.changed_roles) > 0 and len(list(filter(
                    lambda r: r.name == 'Bot Manager',
                    message.channel.changed_roles))) > 0:
                if message.content.startswith(('!help','!ajuda')):
                    await message.channel.send(adm_command_list)
                    return
                if message.content.startswith('!tarefas'):
                    if 'tasks' not in db or len(db['tasks']) == 0:
                        await message.channel.send('Nenhuma tarefa cadastrada!')
                        return
                    task_list_message = [
                        f"{i+1}: {task['name']} - ({task['points']}) pontos - id: {id}"
                        for i, (id, task) in enumerate(db['tasks'].items())
                    ]
                    await message.channel.send('\n'.join(task_list_message))
                    return
                if message.content.startswith('!limpar-tarefas'):
                    await message.channel.send('Tarefas apagadas!')
                    db['tasks'] = {}
                    for id in db['users'].keys():
                      db['users'][id]['points'] = 0
                      db['users'][id]['tasks'] = []
                    await message.channel.send('Tudo apagado :(')
                    return
                if message.content.startswith('!adicionar-tarefa'):
                    message_list = message.content.split(' ', 2)
                    if len(message_list) != 3:
                      await message.channel.send('Por favor, fornecer o número de pontos e a descrição da tarefa nessa ordem.')
                      return
                    if not message_list[1].isdigit():
                      await message.channel.send('A pontuação precisa ser um número inteiro positivo.')
                      return
                    id = str(uuid.uuid4())
                    db['tasks'][id] = {
                      'points': int(message_list[1]),
                      'name': message_list[2]
                    }
                    await message.channel.send(f"A tarefa {db['tasks'][id]['name']} de pontuação {db['tasks'][id]['points']} e id {id} foi adicionada com sucesso!")
                    return
                if message.content.startswith('!remover-tarefa'):
                    message_list = message.content.split(' ')
                    if len(message_list) != 2:
                        await message.channel.send('Por favor, fornecer o id da tarefa a ser apagada')
                        return
                    task_id = message_list[1]
                    task = db['tasks'].get(task_id)
                    if not task:
                        await message.channel.send('Tarefa não encontrada')
                        return
                    for (user_id, user) in db['users'].items():
                        if task_id in user['tasks']:
                            db['users'][user_id]['tasks'].remove(task_id)
                            db['users'][user_id]['points'] -= int(task['points'])
                    del db['tasks'][task_id]
                    await message.channel.send('Tarefa apagada.')
                    return
                if message.content.startswith('!resetar-pontos'):
                    for id in db['users'].keys():
                      db['users'][id]['points'] = 0
                      db['users'][id]['tasks'] = []
                    await message.channel.send('Pontos e tarefas dos usuários resetados!')
                    return
                if message.content.startswith('!usuarios'):
                    user_list_message = [f"{user['name']} - points: {user['points']} - id: {id}" for (id, user) in list(db['users'].items())]
                    if len(user_list_message) == 0:
                        await message.channel.send('Sem usuários cadastrados')
                        return
                    await message.channel.send('\n'.join(user_list_message))
                    return
                if message.content.startswith('!info-usuario'):
                    message_list = message.content.split(' ')
                    if len(message_list) != 2:
                        await message.channel.send('Por favor, fornecer o id do usuário')
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
                        tasks_done = '- Sem tarefas feitas!'
                    tasks_todo = [
                        f"- {i+1}: {task['name']} - ({task['points']} pontos)"
                        for i, (id, task) in enumerate(db['tasks'].items()) if id not in user['tasks']
                    ]
                    if len(tasks_todo) > 0:
                        tasks_todo = '\n'.join(tasks_todo)
                    else:
                        tasks_todo = '- Sem tarefas para fazer!'
                    res = f'''Usuário: {user['display_name']} - {user['name']} - {message_list[1]}
Pontos: {user['points']}

Tarefas feitas:
{tasks_done}

Tarefas para fazer:
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
