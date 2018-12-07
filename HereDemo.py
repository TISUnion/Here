# -*- coding: utf-8 -*-

from imp import load_source
PlayerInfoAPI = load_source('PlayerInfoAPI', './plugins/PlayerInfoAPI.py')

def onServerInfo(server, info):
  HIGHLIGHT_ENABLE = True
  dimension_convert = {"0":"主世界","-1":"地狱","1":"末地"}
  if info.content.startswith('!!here'):
    result = PlayerInfoAPI.getPlayerInfo(server,info.player)
    position = result["Pos"]
    dimension = str(result["Dimension"])
    position_show = "["+str(int(position[0]))+","+str(int(position[1]))+","+str(int(position[2]))+"]"
    server.say("§e" + info.player + "§r 在 §2" + dimension_convert[dimension] + position_show + "§r 向各位打招呼")
    if(HIGHLIGHT_ENABLE):
      server.execute("effect give "+ info.player + " minecraft:glowing 15 1 true")
      server.tell(info.player,"您将会被高亮15秒")
