import discord
import datetime
import threading
import time
from collections import defaultdict
import asyncio
import os
from flask import Flask
from discord.ext import commands
from collections import deque
TARGET_ID = None
TARGET_ROLE_ID = None
TARGET_CHANNEL_ID = 1477240545695895594
ANONYMOUS_CHANNEL_ID = 1559179385255497728
voice_join_times = {}
voice_total_times = defaultdict(int)
voice_clients = {}
current_song = {}
loop_enabled = {}
queue = deque() 
playlist = deque()  
# deque 是双端队列，可以从两端添加和删除元素
# append(x): 从尾部添append(x): 从尾部添加元素 x。
# appendleft(x): 从头部添加元素 x。
# pop(): 从尾部移除并返回一个元素。
# popleft(): 从头部移除并返回一个元素。加元素 x。
intents = discord.Intents.all()
client = commands.Bot(command_prefix = '//', intents=intents)

app = Flask('')

@app.route('/')
def home():
  return "I am alive!"

def run():
  app.run(host='0.0.0.0', port=8080)

def keep_alive():
  t = threading.Thread(target=run)
  t.start()

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.command()
async def date(ctx):
    time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    formatted_time = time.strftime("%Y-%m-%d %A")
    await ctx.send(f'{formatted_time}')

@client.command()
async def time(ctx):
    time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    formatted_time = time.strftime("%I:%M:%S %p")
    await ctx.send(f'{formatted_time}')

@client.command()
async def tag(ctx,d: discord.Member = None):
    global TARGET_ID
    TARGET_ID = d.id
    await ctx.send(f'{d.display_name} 你中了')

@client.command()
async def tagr(ctx,r: discord.Role = None):
    global TARGET_ROLE_ID
    TARGET_ROLE_ID = r.id
    await ctx.send(f'{r.name} 你们中了')

@client.event
async def on_voice_state_update(member, before, after):
    global TARGET_ID, TARGET_ROLE_ID, TARGET_CHANNEL_ID
    joined_target_channel = (after.channel and after.channel.id == TARGET_CHANNEL_ID) and \
                            (before.channel is None or before.channel.id != TARGET_CHANNEL_ID)

    if not joined_target_channel:
        return

    exempt_role_ids = [1540752828107194399, 1475415200856539147]
    has_exempt_role = any(role.id in exempt_role_ids for role in member.roles)

    is_target_user = (member.id == TARGET_ID)
    has_target_role = any(role.id == TARGET_ROLE_ID for role in member.roles)

    if has_exempt_role:
        return

    if has_target_role or is_target_user:
        await member.move_to(None)

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.guild == None:
        target_channel = client.get_channel(ANONYMOUS_CHANNEL_ID)
        if target_channel:
            await target_channel.send(f"{message.author.name}说: {message.content}")
            await message.author.send('你的消息已发送到匿名频道。')
        return

    await client.process_commands(message)

@client.command()
async def cleartag(ctx):
    global TARGET_ID
    if TARGET_ID is None:
        await ctx.send(f'没人中了')
    else:
        TARGET_ID = None
        await ctx.send(f'你活了')

@client.command()
async def cleartagr(ctx):
    global TARGET_ROLE_ID
    TARGET_ROLE_ID = None
    if TARGET_ROLE_ID is None:
            await ctx.send(f'没人中了')
    else:
        TARGET_ROLE_ID = None
        await ctx.send(f'你活了')
        
@client.command()
async def delete(ctx,amount: int):
    if ctx.author == client.user:
        return
    if amount > 0:
        deleted = await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f" {len(deleted) - 1} 条消息不见了",delete_after=2)
    else:
        await ctx.send("你在叫什么",delete_after=2)

@client.command()
async def clear(ctx):
    if ctx.author == client.user:
        return
    await ctx.channel.purge(limit=None)

@client.command()
async def list(ctx):
    list_text = (
        "以下是可用的命令:\n"
        "//date - 显示当前日期\n"
        "//time - 显示当前时间\n"
        "//tag <@user> - 标记用户\n"
        "//tagr <@role> - 标记角色\n"
        "//delete <amount> - 删除消息\n"
        "//clear - 清空频道消息\n"
    )
    if ctx.author.id == 724888545080115280 or ctx.author.id == 952895320658968616:
            await ctx.send(list_text)
    else:
        await ctx.send("你在叫什么",delete_after=2)

@client.command()
async def shutdown(ctx):
    if ctx.author.id == 724888545080115280 or ctx.author.id == 952895320658968616:
        await client.close()
    else:
        await ctx.send("你在叫什么",delete_after=2)

@client.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("去 TM 的加入一个语音频道",delete_after=2)
        
if __name__ == '__main__':
  # 1. 启动保活服务
  keep_alive()
  # 2. 启动 Bot
  client.run(os.getenv('TOKEN'))

# Done at 2025/5/5 11:46 PM