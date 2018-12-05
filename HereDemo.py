# -*- coding: utf-8 -*-

import PlayerInfoAPI

def onServerInfo(server, info):
  HIGHLIGHT_ENABLE = True
  dimension_convert = {"0":"主世界","-1":"地狱","1":"末地"}
  if info.content.startswith('!!here'):
    result = PlayerInfoAPI.getPlayerInfo(server,info.player)
    position = result["Pos"]
    dimension = result["Dim"]
    position_show = "["+str(position[0])+","+str(position[1])+","+str(position[2])+"]"
    server.say("§e" + info.player + "§r 在 §2" + dimension_convert[dimension] + position_show + "§r 向各位打招呼")
    if(HIGHLIGHT_ENABLE):
      server.execute("effect give "+ info.player + " minecraft:glowing 15 1 true")
      server.tell(info.player,"您将会被高亮15秒")
