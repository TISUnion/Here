# -*- coding: utf-8 -*-

import json
import re

def onServerInfo(server, info):
  if (info.isPlayer == 0):
    if("following entity data" in info.content):
      name = info.content.split(":")[0].split(" ")[0]
      position = info.content.split(":")[1].strip().replace("d","")
      position = re.sub("\.\d*","",position)
      server.say("§e" + name + "§r 在 §2" + position + "§r 向各位打招呼")
    pass
  else:
    if info.content.startswith('!!here'):
      server.execute("data get entity "+info.player+" Pos")
