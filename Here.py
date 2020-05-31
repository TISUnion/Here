# -*- coding: utf-8 -*-
import copy
import re

# set it to 0 to disable hightlight
# 将其设为0以禁用高亮
HIGHLIGHT_TIME = 15

here_user = 0


def process_coordinate(text):
	data = text[1:-1].replace('d', '').split(', ')
	data = [(x + 'E0').split('E') for x in data]
	return tuple([int(float(e[0]) * 10 ** int(e[1])) for e in data])


def process_dimension(text):
	return int(text.lstrip(re.match(r'[\w ]+: ', text).group()))


def display(server, name, position, dimension):
	global HIGHLIGHT_TIME
	dimension_display = {0: '"translate":"createWorld.customize.preset.overworld","color":"dark_green"', -1: '"translate":"advancements.nether.root.title","color":"dark_red"', 1: '"translate":"advancements.end.root.title","color":"dark_purple"', 'minecraft:overworld': '"translate":"createWorld.customize.preset.overworld","color":"dark_green"', 'minecraft:the_nether': '"translate":"advancements.nether.root.title","color":"dark_red"', 'minecraft:the_end': '"translate":"advancements.end.root.title","color":"dark_purple"'}
	position_show = '[x:{}, y:{}, z:{}]'.format(*position)
	server.execute('tellraw @a ["",{"text":"' + name + ' ","color":"yellow"},{"text":"@ ","color":"white"},{' + dimension_display[dimension] + '},{"text":" ' + position_show + '","color":"aqua"}]')
	if HIGHLIGHT_TIME > 0:
		server.execute('effect give {} minecraft:glowing {} 0 true'.format(name, HIGHLIGHT_TIME))
		server.tell(name, '你将会被高亮{}秒'.format(HIGHLIGHT_TIME))


def on_info(server, info):
	if info.is_player and info.content == '!!here':
		if hasattr(server, 'MCDR') and server.is_rcon_running():
			name = info.player
			position = process_coordinate(re.search(r'\[.*\]', server.rcon_query('data get entity {} Pos'.format(name))).group())
			dimension = process_dimension(server.rcon_query('data get entity {} Dimension'.format(name)))
			display(server, name, position, dimension)
		else:
			global here_user
			here_user += 1
			server.execute('data get entity ' + info.player)
	if not info.is_player and here_user > 0 and re.match(r'\w+ has the following entity data: ', info.content) is not None:
		name = info.content.split(' ')[0]
		dimension = re.search(r'(?<= Dimension: )(.*?),', info.content).group().replace('"', '').replace(',', '')
		position_str = re.search(r'(?<=Pos: )\[.*?\]', info.content).group()
		position = process_coordinate(position_str)
		display(server, name, position, dimension)
		here_user -= 1


def onServerInfo(server, info):
	info2 = copy.deepcopy(info)
	info2.is_player = info2.isPlayer
	on_info(server, info2)


def on_load(server, old):
	server.add_help_message('!!here', '广播坐标并高亮玩家')
