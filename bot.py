import discord
from discord import app_commands
from discord.ext import commands
import json

# Load config
with open('config.json') as f:
    config = json.load(f)

TOKEN = config['token']
REPORT_CHANNEL_ID = config['report_channel_id']
REPORT_LOG_CHANNEL_ID = config['report_log_channel_id']
ADMIN_ROLE_ID = config['admin_role_id']

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} siap digunakan!')
    try:
        synced = await bot.tree.sync()
        print(f"🔁 {len(synced)} command telah disinkronkan.")
    except Exception as e:
        print(f"❌ Gagal sync command: {e}")

@bot.tree.command(name="report", description="Laporkan user yang melanggar aturan")
@app_commands.describe(
    user="User yang ingin dilaporkan",
    reason="Alasan pelaporan"
)
async def report(interaction: discord.Interaction, user: discord.Member, reason: str):
    # Cek apakah perintah dikirim di channel report
    if interaction.channel_id != REPORT_CHANNEL_ID:
        await interaction.response.send_message(
            f"❌ Perintah ini hanya bisa digunakan di <#{REPORT_CHANNEL_ID}>.",
            ephemeral=True
        )
        return

    # Cegah user melaporkan diri sendiri
    if user.id == interaction.user.id:
        await interaction.response.send_message(
            "❌ Kamu tidak bisa melaporkan dirimu sendiri!",
            ephemeral=True
        )
        return

    # Cegah melaporkan bot atau admin (opsional)
    if user.bot:
        await interaction.response.send_message(
            "❌ Tidak bisa melaporkan bot!",
            ephemeral=True
        )
        return

    # Kirim log ke channel report-log
    log_channel = bot.get_channel(REPORT_LOG_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(
            title="🚨 Laporan Baru",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Pelapor", value=f"{interaction.user.mention} (`{interaction.user}`)", inline=False)
        embed.add_field(name="Target", value=f"{user.mention} (`{user}`)", inline=False)
        embed.add_field(name="Alasan", value=reason, inline=False)
        embed.add_field(name="Server", value=interaction.guild.name, inline=False)
        await log_channel.send(embed=embed)

    # Konfirmasi ke user
    await interaction.response.send_message(
        f"✅ Laporan terhadap {user.mention} telah dikirim ke tim admin.",
        ephemeral=True
    )

# Opsional: Cek apakah user adalah admin
def is_admin(member: discord.Member):
    return any(role.id == ADMIN_ROLE_ID for role in member.roles) or member.guild_permissions.administrator

# Opsional: Command hanya untuk admin (misalnya /clear-report)
@bot.tree.command(name="clear-report", description="Hapus semua pesan di channel report (admin only)")
async def clear_report(interaction: discord.Interaction):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ Kamu tidak memiliki izin!", ephemeral=True)
        return
    if interaction.channel_id == REPORT_CHANNEL_ID:
        await interaction.channel.purge(limit=100)
        await interaction.response.send_message("✅ Channel report telah dibersihkan.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Perintah ini hanya bisa digunakan di channel report.", ephemeral=True)

bot.run(TOKEN)