import re

from mcdreforged.api.all import *

from here.dimension import get_dimension, Dimension, LegacyDimension
from here.position import Position


class Config(Serializable):
	highlight_time: int = 15
	display_voxel_waypoint: bool = True
	display_xaero_waypoint: bool = True
	click_to_teleport: bool = False
	use_rcon_if_possible: bool = True


config: Config
CONFIG_FILE = 'config/here.json'
here_user = 0


def process_coordinate(text: str) -> Position:
	data = text[1:-1].replace('d', '').split(', ')
	data = [(x + 'E0').split('E') for x in data]
	assert len(data) == 3
	return Position(*[float(e[0]) * 10 ** int(e[1]) for e in data])


def process_dimension(text: str) -> str:
	return text.replace(re.match(r'[\w ]+: ', text).group(), '', 1).strip('"\' ')


def coordinate_text(x: float, y: float, z: float, dimension: Dimension):
	coord = RText('[{}, {}, {}]'.format(int(x), int(y), int(z)), dimension.get_coordinate_color())
	if config.click_to_teleport:
		return (
			coord.h(dimension.get_rtext() + ': 点击以传送到' + coord.copy()).
			c(RAction.suggest_command, '/execute in {} run tp {} {} {}'.format(dimension.get_reg_key(), int(x), int(y), int(z)))
		)
	else:
		return coord.h(dimension.get_rtext())


def __display(server: ServerInterface, name: str, position: Position, dimension_str: str):
	x, y, z = position
	dimension = get_dimension(dimension_str)

	# basic text: someone @ dimension [x, y, z]
	texts = RTextList(RText(name, RColor.yellow), ' @ ', dimension.get_rtext(), ' ', coordinate_text(x, y, z, dimension))

	# click event to add waypoint
	if config.display_voxel_waypoint:
		texts.append(' ', RText('[+V]', RColor.aqua).h('§bVoxelmap§r: 点此以高亮坐标点, 或者Ctrl点击添加路径点').c(
			RAction.run_command, '/newWaypoint x:{}, y:{}, z:{}, dim:{}'.format(
				int(x), int(y), int(z), dimension.get_reg_key()
			)
		))
	if config.display_xaero_waypoint:
		command = "xaero_waypoint_add:{}'s Location:{}:{}:{}:{}:6:false:0".format(name, name[0], int(x), int(y), int(z))
		if isinstance(dimension, LegacyDimension):
			command += ':Internal_{}_waypoints'.format(dimension.get_reg_key().replace('minecraft:', '').strip())
		texts.append(' ',  RText('[+X]', RColor.gold).h('§6Xaeros Minimap§r: 点击添加路径点').c(RAction.run_command, command))

	# coordinate conversion between overworld and nether
	if dimension.has_opposite():
		oppo_dim, oppo_pos = dimension.get_opposite(position)
		arrow = RText('->', RColor.gray)
		texts.append(RText.format(
			' {} {}',
			arrow.copy().h(RText.format('{} {} {}', dimension.get_rtext(), arrow, oppo_dim.get_rtext())),
			coordinate_text(oppo_pos.x, oppo_pos.y, oppo_pos.z, oppo_dim)
		))

	server.say(texts)

	# highlight
	if config.highlight_time > 0:
		server.execute('effect give {} minecraft:glowing {} 0 true'.format(name, config.highlight_time))


def display(server: ServerInterface, name: str, position: Position, dimension_str: str):
	try:
		__display(server, name, position, dimension_str)
	except:
		server.logger.exception('Error displaying coordinate information')


def on_info(server: PluginServerInterface, info: Info):
	global here_user
	if info.is_player and info.content.find('!!here') != -1:
		if server.is_rcon_running() and config.use_rcon_if_possible:
			name = info.player
			position = process_coordinate(re.search(r'\[.*]', server.rcon_query('data get entity {} Pos'.format(name))).group())
			dimension = process_dimension(server.rcon_query('data get entity {} Dimension'.format(name)))
			display(server, name, position, dimension)
		else:
			here_user += 1
			server.execute('data get entity ' + info.player)
	if not info.is_player and here_user > 0 and re.match(r'\w+ has the following entity data: ', info.content) is not None:
		name = info.content.split(' ')[0]
		dimension = re.search(r'(?<= Dimension: )(.*?),', info.content).group().replace('"', '').replace("'", '').replace(',', '')
		position_str = re.search(r'(?<=Pos: )\[.*?]', info.content).group()
		position = process_coordinate(position_str)
		display(server, name, position, dimension)
		here_user -= 1


def on_load(server: PluginServerInterface, old):
	server.register_help_message('!!here', '广播坐标并高亮玩家')
	global config
	config = server.load_config_simple(CONFIG_FILE, target_class=Config, in_data_folder=False)
