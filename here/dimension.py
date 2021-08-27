from abc import ABC

from mcdreforged.api.all import *

OVERWORLD = 'minecraft:overworld'
NETHER = 'minecraft:the_nether'
END = 'minecraft:the_end'
REG_TO_ID = {
	OVERWORLD: 0,
	NETHER: -1,
	END: 1
}
ID_TO_REG = dict([(v, k) for k, v in REG_TO_ID.items()])


class Dimension(ABC):
	def get_id(self) -> str:  # 0
		raise NotImplementedError()

	def get_reg_key(self) -> str:  # minecraft:overworld
		raise NotImplementedError()

	def get_color(self) -> RColor:
		return {
			OVERWORLD: RColor.dark_green,
			NETHER: RColor.dark_red,
			END: RColor.dark_purple
		}.get(self.get_reg_key(), RColor.gray)

	def get_coordinate_color(self) -> RColor:
		return {
			OVERWORLD: RColor.green,
			NETHER: RColor.red,
			END: RColor.light_purple
		}.get(self.get_reg_key(), RColor.white)

	def get_rtext(self) -> RTextBase:
		raise NotImplementedError()

	def has_opposite(self) -> bool:
		raise NotImplementedError()

	def get_opposite(self) -> 'Dimension':
		raise NotImplementedError()


class LegacyDimension(Dimension):
	def __init__(self, dim_id: int):
		assert isinstance(dim_id, int) and -1 <= dim_id <= 1
		self.dim_id = dim_id

	def get_id(self) -> int:
		return self.dim_id

	def get_reg_key(self) -> str:
		return ID_TO_REG[self.dim_id]

	def get_rtext(self) -> RTextBase:
		return RTextTranslation({
			0: 'createWorld.customize.preset.overworld',
			-1: 'advancements.nether.root.title',
			1: 'advancements.end.root.title'
		}[self.dim_id]).set_color(self.get_color())

	def has_opposite(self) -> bool:
		return self.dim_id in (0, -1)

	def get_opposite(self) -> 'Dimension':
		# 0 -> -1
		# -1 -> 0
		return LegacyDimension(-1 - self.dim_id)


class CustomDimension(Dimension):
	def __init__(self, reg_key: str):
		self.reg_key = reg_key

	def get_id(self) -> str:
		raise RuntimeError('Custom dimension {} does not have integer id'.format(self.reg_key))

	def get_reg_key(self) -> str:
		return self.reg_key

	def get_rtext(self) -> RTextBase:
		return RText(self.reg_key).set_color(self.get_color())

	def has_opposite(self) -> bool:
		return False

	def get_opposite(self) -> 'Dimension':
		raise RuntimeError('Custom dimension {} does not have opposite dimension'.format(self.reg_key))


def get_dimension(text: str) -> Dimension:
	"""
	text can be:
	- int id: 0
	- str registry key: minecraft:overworld
	"""
	try:
		return LegacyDimension(int(text))
	except:
		pass
	if text in REG_TO_ID:
		return LegacyDimension(REG_TO_ID[text])
	return CustomDimension(text)
