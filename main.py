
import discord
from discord.ext import commands
import json
import os
import datetime

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= 환경변수 TOKEN =================
TOKEN = os.environ.get("TOKEN")

# ================= 기본 설정 =================
CATEGORY_NAME = "🎫 티켓"
STAFF_ROLE_NAME = "관리자"
LOG_CHANNEL_NAME = "티켓로그"
PAYMENT_INFO = "카카오뱅크 0000-00-000000 홍길동"

# ================= DB 생성 =================
if not os.path.exists("tickets.json"):
    with open("tickets.json", "w", encoding="utf-8") as f:
        json.dump({}, f)

def load_db():
    with open("tickets.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open("tickets.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# ================= 티켓 선택 =================
class TicketSelect(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="문의 유형을 선택하세요",
        custom_id="ticket_select",
        options=[
            discord.SelectOption(label="문의", emoji="❓"),
            discord.SelectOption(label="구매", emoji="🛒"),
            discord.SelectOption(label="신고", emoji="🚨"),
        ],
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):

        db = load_db()
        user_id = str(interaction.user.id)

        if user_id in db:
            await interaction.response.send_message("❌ 이미 열린 티켓이 있습니다.", ephemeral=True)
            return

        guild = interaction.guild
        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)

        if category is None:
            category = await guild.create_category(CATEGORY_NAME)

        staff_role = discord.utils.get(guild.roles, name=STAFF_ROLE_NAME)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_type = select.values[0]

        channel = await guild.create_text_channel(
            name=f"{ticket_type}-{interaction.user.name}",
            category=category,
            overwrites=overwrites,
        )

        db[user_id] = channel.id
        save_db(db)

        embed = discord.Embed(
            title=f"🎫 {ticket_type} 티켓",
            description=f"{interaction.user.mention} 님의 티켓이 생성되었습니다.",
            color=discord.Color.blurple(),
        )

        embed.add_field(name="📌 안내", value="상담원이 곧 도와드립니다.", inline=False)

        if ticket_type == "구매":
            embed.add_field(name="💳 결제 안내", value=PAYMENT_INFO, inline=False)

        embed.set_footer(text="디톤 티켓 시스템")

        mention = staff_role.mention if staff_role else ""

        await channel.send(content=mention, embed=embed, view=CloseView())
        await interaction.response.send_message("✅ 티켓이 생성되었습니다!", ephemeral=True)

        log_channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
        if log_channel:
            await log_channel.send(f"📊 티켓 생성 | {interaction.user} | {ticket_type}")


# ================= 티켓 닫기 =================
class CloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 티켓 닫기", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        db = load_db()
        user_id = None

        for uid, cid in db.items():
            if cid == interaction.channel.id:
                user_id = uid
                break

        if user_id:
            del db[user_id]
            save_db(db)

        messages = [msg async for msg in interaction.channel.history(limit=None, oldest_first=True)]
        log_text = ""

        for msg in messages:
            log_text += f"[{msg.created_at}] {msg.author}: {msg.content}\n"

        os.makedirs("logs", exist_ok=True)
        filename = f"logs/{interaction.channel.name}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(log_text)

        log_channel = discord.utils.get(interaction.guild.text_channels, name=LOG_CHANNEL_NAME)
        if log_channel:
            await log_channel.send(file=discord.File(filename))

        await interaction.response.send_message("⏳ 티켓을 종료합니다...", ephemeral=True)
        await interaction.channel.delete()


# ================= 패널 명령어 =================
@bot.command()
@commands.has_permissions(administrator=True)
async def 티켓패널(ctx):

    embed = discord.Embed(
        title="🎟 디톤 고객센터",
        description="아래 메뉴에서 문의 유형을 선택해주세요.",
        color=discord.Color.dark_theme(),
    )

    if ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)

    await ctx.send(embed=embed, view=TicketSelect())


# ================= 실행 =================
@bot.event
async def on_ready():
    bot.add_view(TicketSelect())
    bot.add_view(CloseView())
    print(f"봇 로그인 완료: {bot.user}")


bot.run(TOKEN)
