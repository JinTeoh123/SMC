import discord
import datetime
import asyncio
import yt_dlp
import random
import nacl
import os
from discord.ext import commands
from collections import deque
TARGET_ID = None
TARGET_ROLE_ID = None
TARGET_CHANNEL_ID = 1477240545695895594
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
ytdl_opts = {
    'noplaylist': True,
    'extract_flat': True,
    'quite': True,
}
ydl_opts = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'noplaylist': True,
}
ytdl = yt_dlp.YoutubeDL(ytdl_opts)

def shuffle_playlist(list):
    random.shuffle(list)
    return list

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.command()
async def date(ctx):
    time = datetime.datetime.now()
    formatted_time = time.strftime("%Y-%m-%d %A")
    await ctx.send(f'{formatted_time}')

@client.command()
async def time(ctx):
    time = datetime.datetime.now()
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
    await ctx.send(f'你们活了')

@client.command()
async def play(ctx, url):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            i = ydl.extract_info(url, download=False)
            url2 = i['url']
            s = discord.FFmpegPCMAudio(url2)
            ctx.voice_client.play(s)
            print(f"正在播放: {url}")
    else:
        await ctx.send("去 TM 的加入一个语音频道",delete_after=2)

@client.command()
async def add_queue(ctx, url):
    queue.append(url)
    await ctx.send(f"已添加到队列: {url}")

@client.command()
async def add_playlist(ctx,f : str,playlist_url : str):
    a = 0
    with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False) #提取的是播放列表的所有讯息
        if f == 'base' or f == 'b':
            for entry in info['entries']: #info['entries'] 是提取播放列表中的一个视频的所有信息要 for 才能提取全部
                url = entry['url'] #这才从频的所有信息中把 url 提取出来
                queue.append(url)
                a += 1
            await ctx.send(f"已添加 {a} 首歌曲到队列")
        elif f == 'shuffle' or f == 's':
            for entry in info['entries']: #info['entries'] 是提取播放列表中的一个视频的所有信息要 for 才能提取全部
                url = entry['url'] #这才从频的所有信息中把 url 提取出来
                playlist.append(url)
                shuffle_playlist(playlist) #打乱顺序
            for url in playlist:
                queue.append(url)
                a += 1
            await ctx.send(f"已添加打乱顺序的 {a} 首歌曲到队列")

@client.command()
async def show_q(ctx):
    if queue:
        queue_list = "\n".join(queue)
        await ctx.send(f"队列:\n{queue_list}")
    else:
        await ctx.send("队列是空的",delete_after=2)

@client.command()
async def clear_q(ctx):
    queue.clear()
    await ctx.send("队列已清空")   

@client.command()
async def play_q(ctx):
    if not ctx.voice_client:
        channel = ctx.author.voice.channel
        await channel.connect()
    if ctx.voice_client and ctx.voice_client.is_connected():
        if queue:
            url = queue.popleft()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                i = ydl.extract_info(url, download=False)
                url2 = i['url']
                ctx.voice_client.play(
                discord.FFmpegPCMAudio(url2),
                after=lambda e: asyncio.run_coroutine_threadsafe(play_q(ctx), client.loop)
            )
        else:
            ctx.voice_client.leave()
            await ctx.send("已经播完咯")

@client.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
    else:
        await ctx.send("你在叫什么",delete_after=2)

@client.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
    else:
        await ctx.send("你在吵什么",delete_after=2)

@client.command()
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.leave()
    else:
        await ctx.send("你在叫什么",delete_after=2)

@client.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await play_q(ctx)
        await ctx.send("我已经跳过了这首歌",delete_after=1)
    else:
        await ctx.send("你在叫什么",delete_after=2)       

@client.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("我都没进怎样出",delete_after=2)

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
async def loop(ctx):
    if not ctx.voice_client:
        await ctx.send("我都没进语音频道，怎么循环",delete_after=2)
        return
    guild_id = ctx.guild.id
    if guild_id in current_song:
        loop_enabled[guild_id] = not loop_enabled.get(guild_id, False) #guild_id是‘东西’
    #loop_enabled.get是提取loop_enabled里有没有东西，有东西代表开着，通过 not 反转还给loop_enabled，即为loop_enabled = false,关闭循环
    #如果loop_enabled没有东西，代表没开着，反转后为true，即为loop_enabled = true,开启循环
        status = '已开启' if loop_enabled[guild_id] else '已关闭'
        await ctx.send(f'单曲循环{status}')
    else:
        await ctx.send('当前没有正在播放的歌曲。')

@client.command()
async def list(ctx):
    list_text = (
        "以下是可用的命令:\n"
        "//date - 显示当前日期\n"
        "//time - 显示当前时间\n"
        "//play <url> - 播放音频\n"
        "//add_queue <url> - 将音频添加到队列\n"
        "//add_playlist <base/b/shuffle/s> <playlist_url> - 添加播放列表中的所有音频到队列,可选择是否打乱顺序\n"
        "//show_q - 显示队列\n"
        "//clear_q - 清空队列\n"
        "//play_q - 播放队列中的音频\n"
        "//pause - 暂停播放\n"
        "//resume - 恢复播放\n"
        "//stop - 停止播放并离开语音频道\n"
        "//skip - 跳过当前音频\n"
        "//leave - 离开语音频道\n"
        "//delete <amount> - 删除消息\n"
        "//clear - 清空频道消息\n"
        "//loop - 切换循环播放\n"
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
        
client.run(os.getenv("TOKEN"))

# Done at 2025/5/5 11:46 PM