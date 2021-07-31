# -*- coding: utf-8 -*-
import re
import os
import json

from typing import Any
from mcdreforged.api.rtext import *
from mcdreforged.api.types import ServerInterface, Info

PLUGIN_METADATA = {
	'id': 'here',
	'version': '1.1.0-alpha3',
	'name': 'Here',
	'author': [
		'Fallen_Breath',
		'nathan21hz'
   ],
	'link': 'https://github.com/TISUnion/Here'
}

# Configuration file path
# 配置文件路径
CONFIG_FILE = 'config/here.json'

# DO NOT change here!!! If you need to change the config value, pls change this in config file
# 这里别动！！！要改配置去配置文件里改
default_config = {
	'highlight_time': 15,
	'display_voxel_waypoint': True,
	'display_xaero_waypoint': True,
	'click_to_teleport': False
}

here_user = 0

dimension_display = {
		'0': 'createWorld.customize.preset.overworld',
		'-1': 'advancements.nether.root.title',
		'1': 'advancements.end.root.title'
	}

dimension_color = {
		'0': RColor.dark_green,
		'-1': RColor.dark_red,
		'1': RColor.dark_purple
	}


class Config:
	def __init__(self, file: str) -> None:
		self.file = file
		self.data = {}

	def __write_config(self, new_data = None):
		if isinstance(new_data, dict):
			self.data.update(new_data)
		with open(self.file, 'w', encoding='UTF-8') as f:
			json.dump(self.data, f, indent=4)

	def __get_config(self):
		with open(self.file, 'r', encoding='UTF-8') as f:
			self.data.update(json.load(f))

	def load(self, server: ServerInterface):
		if not os.path.isdir(os.path.dirname(self.file)):
			os.makedirs(os.path.dirname)
			server.logger.info('Config directory not found, created')
		if not os.path.isfile(self.file):
			self.__write_config(default_config)
			server.logger.info('Config file not found, using default')
		else:
			try:
				self.__get_config()
			except json.JSONDecodeError:
				self.__write_config(default_config)
				server.logger.info('Invalid config file, using default')

	def __getitem__(self, key: str) -> Any:
		ret = self.data.get(key)
		if ret == None and key in default_config.keys():
			ret = default_config[key]
			self.__write_config({key: ret})
		return ret

config = Config(CONFIG_FILE)


def process_coordinate(text: str) -> tuple:
	data = text[1:-1].replace('d', '').split(', ')
	data = [(x + 'E0').split('E') for x in data]
	return tuple([float(e[0]) * 10 ** int(e[1]) for e in data])


def process_dimension(text: str) -> str:
	return text.replace(re.match(r'[\w ]+: ', text).group(), '', 1)


def coordinate_text(x: str, y: str, z: str, dimension: str, opposite=False):
	dimension_coordinate_color = {
		'0': RColor.green,
		'-1': RColor.red,
		'1': RColor.light_purple
	}
	dimension_name = {
		'0': 'minecraft:overworld',
		'1': 'minecraft:the_end',
		'-1': 'minecraft:the_nether'
	}

	if opposite:
		dimension = '-1' if dimension == '0' else '0'
		x, z = (x / 8, z / 8) if dimension == '-1' else (x * 8, z * 8)

	pattern = RText('[{}, {}, {}]'.format(int(x), int(y), int(z)), dimension_coordinate_color[dimension])
	dim_text = RTextTranslation(dimension_display[dimension], color=dimension_color[dimension])

	return pattern.h(dim_text) if not config['click_to_teleport'] else pattern.h(
		dim_text + ': 点击以传送到' + pattern.copy()
		).c(RAction.suggest_command, 
		'/execute in {} run tp {} {} {}'.format(dimension_name[dimension], int(x), int(y), int(z)))


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
	
	if dimension in dimension_convert:  # convert from 1.16 format to pre 1.16 format
		dimension = dimension_convert[dimension]

	# text base
	texts = RTextList(
		'§e{}§r'.format(name),
		' @ ',
		RTextTranslation(dimension_display[dimension], color=dimension_color[dimension]),
		' ',
		coordinate_text(x, y, z, dimension)
	)

	# click event to add waypoint
	if config['display_voxel_waypoint']:
		texts.append( ' ',
			RText('[+V]', RColor.aqua).h('§bVoxelmap§r: 点此以高亮坐标点, 或者Ctrl点击添加路径点').c(
				RAction.run_command, '/newWaypoint [x:{}, y:{}, z:{}, dim:{}]'.format(
					int(x), int(y), int(z), dimension
				)))
	if config['display_xaero_waypoint']:
		texts.append( ' ',
			RText('[+X]', RColor.gold).h('§6Xaeros Minimap§r: 点击添加路径点').c(
				RAction.run_command, 'xaero_waypoint_add:{}:{}:{}:{}:{}:6:false:0:Internal_{}_waypoints'.format(
					name + "'s Location", name[0], int(x), int(y), int(z), dimension.replace('minecraft:', '').strip()
				)))

	# coordinate convertion between overworld and nether
	if dimension in ['0', '-1']:
		texts.append(
			' §7->§r ',
			coordinate_text(x, y, z, dimension, opposite=True)
			)

	server.say(texts)

	# highlight
	if config['highlight_time'] > 0:
		server.execute('effect give {} minecraft:glowing {} 0 true'.format(name, config['highlight_time']))


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
	config.load(server)
