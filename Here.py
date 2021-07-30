# -*- coding: utf-8 -*-
import re
import json

from mcdreforged.api.rtext import *
from mcdreforged.api.types import ServerInterface, Info

PLUGIN_METADATA = {
	'id': 'here',
	'version': '1.1.0-alpha1',
	'name': 'Here',
	'author': [
		'Fallen_Breath',
		'nathan21hz'
   ],
	'link': 'https://github.com/TISUnion/Here'
}

# set it to 0 to disable hightlight
# 将其设为0以禁用高亮
HIGHLIGHT_TIME = 15

# set it to True to enable Xaero's Minimap waypoint
# 将其设为True以显示Xaero的小地图/Voxelmap的路径点
XAERO_WAYPOINT = True
VOXEL_WAYPOINT = True


here_user = 0


def process_coordinate(text: str) -> tuple:
	data = text[1:-1].replace('d', '').split(', ')
	data = [(x + 'E0').split('E') for x in data]
	return tuple([float(e[0]) * 10 ** int(e[1]) for e in data])


def process_dimension(text: str) -> str:
	return text.replace(re.match(r'[\w ]+: ', text).group(), '', 1)


def display(server: ServerInterface, name: str, position: str, dimension: str):
	x, y, z = position
	dimension_convert = {
		'minecraft:overworld': '0',
		'"minecraft:overworld"': '0',
		'minecraft:the_nether': '-1',
		'"minecraft:the_nether"': '-1',
		'minecraft:the_end': '1',
		'"minecraft:the_end"': '1'
	}
	dimension_color = {
		'0': RColor.dark_green,
		'-1': RColor.dark_red,
		'1': RColor.dark_purple
	}
	dimension_coordinate_color = {
		'0': RColor.green,
		'-1': RColor.red,
		'1': RColor.light_purple
	}
	dimension_display = {
		'0': 'createWorld.customize.preset.overworld',
		'-1': 'advancements.nether.root.title',
		'1': 'advancements.end.root.title'
	}
	if dimension in dimension_convert:  # convert from 1.16 format to pre 1.16 format
		dimension = dimension_convert[dimension]

	# text base
	texts = RTextList(
		'§e{}§r'.format(name),
		' @ ',
		RTextTranslation(dimension_display[dimension], color=dimension_color[dimension]),
		RText(' [{}, {}, {}]'.format(int(x), int(y), int(z)), dimension_coordinate_color[dimension])
	)

	# click event to add waypoint
	if VOXEL_WAYPOINT:
		texts.append( ' ',
			RText('[+V]', RColor.aqua).h('§bVoxelmap§r: 点此以高亮坐标点, 或者Ctrl点击添加路径点').c(
				RAction.run_command, '/newWaypoint [x:{}, y:{}, z:{}, dim:{}]'.format(
					int(x), int(y), int(z), dimension
				))
			)
	if XAERO_WAYPOINT:
		texts.append( ' ',
			RText('[+X]', RColor.gold).h('§6Xaeros Minimap§r: 点击添加路径点').c(
				RAction.run_command, 'xaero_waypoint_add:{}:{}:{}:{}:{}:6:false:0:Internal_{}_waypoints'.format(
					name + "'s Location", name[0], int(x), int(y), int(z), dimension.replace('minecraft:', '').strip()
				)
			)
		)
	
	if dimension in ['0', '-1']:  # coordinate convertion between overworld and nether
		dimension_opposite = '-1' if dimension == '0' else '0'
		x, z = (x / 8, z / 8) if dimension == '0' else (x * 8, z * 8)
		texts.append(
			' §7->§r ',
			RText('[{}, {}, {}]'.format(int(x), int(y), int(z)), dimension_coordinate_color[dimension_opposite]).h(
				RTextTranslation(dimension_display[dimension_opposite], color=dimension_color[dimension_opposite])
			)
		)

	server.say(texts)

	# highlight
	global HIGHLIGHT_TIME
	if HIGHLIGHT_TIME > 0:
		server.execute('effect give {} minecraft:glowing {} 0 true'.format(name, HIGHLIGHT_TIME))


def on_info(server: ServerInterface, info: Info):
	global here_user
	if info.is_player and info.content == '!!here':
		if hasattr(server, 'MCDR') and server.is_rcon_running():
			name = info.player
			position = process_coordinate(re.search(r'\[.*\]', server.rcon_query('data get entity {} Pos'.format(name))).group())
			dimension = process_dimension(server.rcon_query('data get entity {} Dimension'.format(name)))
			display(server, name, position, dimension)
		else:
			here_user += 1
			server.execute('data get entity ' + info.player)
	if not info.is_player and here_user > 0 and re.match(r'\w+ has the following entity data: ', info.content) is not None:
		name = info.content.split(' ')[0]
		dimension = re.search(r'(?<= Dimension: )(.*?),', info.content).group().replace('"', '').replace(',', '')
		position_str = re.search(r'(?<=Pos: )\[.*?\]', info.content).group()
		position = process_coordinate(position_str)
		display(server, name, position, dimension)
		here_user -= 1


def on_load(server: ServerInterface, old):
	server.register_help_message('!!here', '广播坐标并高亮玩家')
