import discord
from discord.ext import commands
import json
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

CONFIG_FILE = "config.json"

# ------------------------
# 설정 파일
# ------------------------

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"admins": []}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

config = load_config()

# ------------------------
# 봇 시작
# ------------------------

@bot.event
async def on_ready():
    print(f"{bot.user} 로그인 완료")

# ------------------------
# 명령어 목록
# ------------------------

@bot.command()
async def 명령어(ctx):
    embed = discord.Embed(title="📜 명령어 목록", color=0x5865F2)
    embed.add_field(name="!문의설정 #채널", value="문의 받을 채널 설정", inline=False)
    embed.add_field(name="!문의관리자 @유저", value="문의 관리자 추가", inline=False)
    embed.add_field(name="!문의열기", value="DM 문의 시작", inline=False)
    embed.add_field(name="!답장 @유저 내용", value="DM으로 답장 보내기", inline=False)
    embed.add_field(name="!문의종료 @유저", value="문의 종료 알림", inline=False)
    await ctx.send(embed=embed)

# ------------------------
# 문의 채널 설정
# ------------------------

@bot.command()
@commands.has_permissions(administrator=True)
async def 문의설정(ctx, channel: discord.TextChannel):
    config["문의채널"] = channel.id
    save_config(config)
    await ctx.send("✅ 문의 채널 설정 완료")

# ------------------------
# 관리자 추가
# ------------------------

@bot.command()
@commands.has_permissions(administrator=True)
async def 문의관리자(ctx, member: discord.Member):
    if "admins" not in config:
        config["admins"] = []

    if member.id not in config["admins"]:
        config["admins"].append(member.id)
        save_config(config)
        await ctx.send("✅ 관리자 추가 완료")
    else:
        await ctx.send("이미 관리자입니다.")

# ------------------------
# 문의 열기
# ------------------------

@bot.command()
async def 문의열기(ctx):
    await ctx.author.send("📩 문의 내용을 입력해주세요.")
    await ctx.send("DM을 확인해주세요.")

# ------------------------
# DM 수신
# ------------------------

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # DM일 경우
    if message.guild is None:
        config = load_config()
        channel_id = config.get("문의채널")

        if channel_id:
            channel = bot.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    title="📩 새로운 문의",
                    description=message.content,
                    color=0x2F3136
                )
                embed.set_footer(text=f"보낸 사람 ID: {message.author.id}")
                await channel.send(embed=embed)

    await bot.process_commands(message)

# ------------------------
# 답장 기능
# ------------------------

@bot.command()
async def 답장(ctx, member: discord.User, *, 내용):
    if ctx.author.id not in config.get("admins", []):
        return await ctx.send("관리자만 사용 가능합니다.")

    try:
        await member.send(f"📩 관리자 답장:\n{내용}")
        await ctx.send("✅ 답장 전송 완료")
    except:
        await ctx.send("❌ DM 전송 실패")

# ------------------------
# 문의 종료
# ------------------------

@bot.command()
async def 문의종료(ctx, member: discord.User):
    if ctx.author.id not in config.get("admins", []):
        return await ctx.send("관리자만 사용 가능합니다.")

    try:
        await member.send("📴 문의가 종료되었습니다.")
        await ctx.send("✅ 문의 종료 완료")
    except:
        await ctx.send("❌ 종료 DM 실패")

# ------------------------

bot.run(os.environ["TOKEN"])
