# -*- coding: utf-8 -*-
import copy
import re
import json


# set it to 0 to disable hightlight
# 将其设为0以禁用高亮
HIGHLIGHT_TIME = 15

here_user = 0


def process_coordinate(text):
	data = text[1:-1].replace('d', '').split(', ')
	data = [(x + 'E0').split('E') for x in data]
	return tuple([float(e[0]) * 10 ** int(e[1]) for e in data])


def process_dimension(text):
	return int(text.lstrip(re.match(r'[\w ]+: ', text).group()))


def display(server, name, position, dimension):
	x, y, z = position
	dimension_convert = {
		'minecraft:overworld': '0',
		'minecraft:the_nether': '-1',
		'minecraft:the_end': '1'
	}
	dimension_color = {
		'0': '§2',
		'-1': '§4',
		'1': '§5'
	}
	dimension_display = {
		'0': {'translate': 'createWorld.customize.preset.overworld'},
		'-1': {'translate': 'advancements.nether.root.title'},
		'1': {'translate': 'advancements.end.root.title'}
	}
	
	if dimension in dimension_convert:  # convert to 1.16 format
		dimension = dimension_convert[dimension]
	texts = [
		'',
		'§e{}§r @ '.format(name),
		dimension_color[dimension],  # hacky fix for voxelmap yeeting text color in translated text 
		dimension_display[dimension],
		' §b[x:{}, y:{}, z:{}]§r'.format(int(x), int(y), int(z))
	]
	if dimension in ['0', '-1']:  # coordinate convertion between overworld and nether
		dimension_opposite = '-1' if dimension == '0' else '0'
		x, z = (x / 8, z / 8) if dimension == '0' else (x * 8, z * 8)
		dimension_color[dimension_opposite],
		texts.extend([
			' §7->§r ',
			dimension_color[dimension_opposite],
			dimension_display[dimension_opposite],
			' ({}, {}, {})'.format(int(x), int(y), int(z))
		])
	server.execute('tellraw @a {}'.format(json.dumps(texts)))
	global HIGHLIGHT_TIME
	if HIGHLIGHT_TIME > 0:
		server.execute('effect give {} minecraft:glowing {} 0 true'.format(name, HIGHLIGHT_TIME))


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
