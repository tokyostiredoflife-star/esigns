import discord
from discord import app_commands
from discord.ext import commands
from pathlib import Path
import importlib
import sys
import re
import io
from PIL import Image, ImageFilter

BLUR_SCALE = 3

BASE_DIR = Path(__file__).resolve().parent.parent
FONTS_DIR = BASE_DIR / "fonts"
STYLES_DIR = BASE_DIR / "commands" / "styles"

class FanSign(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_available_fonts(self):
        return [f.stem for f in FONTS_DIR.iterdir() if f.suffix.lower() in {'.ttf', '.otf'}]

    def get_available_styles(self):
        def natural_sort_key(s):
            return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

        return sorted([
            f.stem for f in STYLES_DIR.iterdir()
            if f.is_file() and f.suffix == ".py" and not f.stem.startswith("__")
        ], key=natural_sort_key)

    def import_style_module(self, style_name: str):
        module_path = f"commands.styles.{style_name}"
        if module_path in sys.modules:
            return sys.modules[module_path]
        return importlib.import_module(module_path)

    @app_commands.command(name="fansign", description="Generate a fansign with custom text.")
    @app_commands.describe(
        text="Text to display (max 14 characters)",
        font="Font to use (filename from fonts folder)",
        style="Choose a style layout"
    )
    @app_commands.checks.cooldown(1, 3.0)
    async def fansign(
        self,
        interaction: discord.Interaction,
        text: str,
        font: str,
        style: str
    ):
        if len(text) > 14:
            await interaction.response.send_message(
                "bro the text can only be 14 characters or less read next time🤦", ephemeral=True
            )
            return

        available_fonts = self.get_available_fonts()
        if font not in available_fonts:
            await interaction.response.send_message(
                f"invalid font. available fonts: {', '.join(available_fonts)}", ephemeral=True
            )
            return

        available_styles = self.get_available_styles()
        if style.lower() not in available_styles:
            await interaction.response.send_message(
                f"invalid style. available styles: {', '.join(available_styles)}", ephemeral=True
            )
            return

        await interaction.response.defer()

        try:
            style_module = self.import_style_module(style.lower())
            generate_func_name = f"generate_fansign_{style.lower()}"
            if hasattr(style_module, generate_func_name):
                generate_func = getattr(style_module, generate_func_name)
                out_path = await generate_func(interaction.user.id, text, font)
            else:
                await interaction.followup.send(f"style module missing function `{generate_func_name}`", ephemeral=True)
                return

            try:
                with Image.open(out_path) as img:
                    if img.mode not in ("RGBA", "RGB"):
                        img = img.convert("RGBA")

                    radius = max(0.0, float(BLUR_SCALE) / 5.0)

                    blurred = img.filter(ImageFilter.GaussianBlur(radius=radius))

                    img_buffer = io.BytesIO()
                    blurred.save(img_buffer, format="PNG")
                    img_buffer.seek(0)

                    filename = out_path.name
                    if not filename.lower().endswith(".png"):
                        filename = Path(filename).with_suffix(".png").name

                    file = discord.File(img_buffer, filename=filename)
            except Exception as img_err:
                print(f"Warning: could not blur image, sending original. Error: {img_err}")
                file = discord.File(str(out_path), filename=out_path.name)

            embed = discord.Embed(
                title="Your Fansign from .gg/esigns ",
                description="Generated with love from [**.gg/esigns**](https://discord.gg/esigns) \nJoin us now at **.gg/esigns**!",
                color=discord.Color.purple()
            )
            embed.add_field(name="Text", value=text, inline=True)
            embed.add_field(name="Font", value=font, inline=True)
            embed.add_field(name="Style", value=style + "\n\n[**.gg/esigns**](https://discord.gg/esigns)", inline=True)
            embed.set_image(url=f"attachment://{file.filename}")
            embed.set_footer(text=".gg/esigns • Join the original fansign community!")

            view = discord.ui.View()
            view.add_item(discord.ui.Button(
                label="Donate",
                custom_id="donate_button",
                style=discord.ButtonStyle.primary
            ))
            view.add_item(discord.ui.Button(
                label="Contribute",
                custom_id="contribute_button",
                style=discord.ButtonStyle.secondary
            ))

            await interaction.followup.send(
                content=f"here you go {interaction.user.mention} brought to you by .gg/esigns",
                embeds=[embed],
                file=file,
                view=view
            )

        except Exception as e:
            print(f"Error generating fansign: {e}")
            await interaction.followup.send(f"error: `{e}`", ephemeral=True)

    @fansign.error
    async def fansign_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.errors.CommandOnCooldown):
            embed = discord.Embed(
                title="You're too fast...",
                description="slow down here bud, we only allow you to generate a new one every 3 seconds or it could maybe crash the bot",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("something went wrong.", ephemeral=True)
            raise error

    @fansign.autocomplete("font")
    async def font_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        fonts = self.get_available_fonts()
        return [
            app_commands.Choice(name=f, value=f)
            for f in fonts if current.lower() in f.lower()
        ][:25]

    @fansign.autocomplete("style")
    async def style_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        styles = self.get_available_styles()
        return [
            app_commands.Choice(name=s, value=s)
            for s in styles if current.lower() in s.lower()
        ][:25]

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if not interaction.type.name == "component":
            return

        if interaction.data.get("custom_id") == "donate_button":
            try:
                await interaction.user.send(
                    "**Thank you for supporting us!**\n\n"
                    "**LTC:** `LeDwnDrxEe9J6eq5gec3bL8tdkUzzadQvo`\n"
                    "**BTC:** `bc1q26c78yj60stne4fw0allksdsvxxnv7dnvh32nv`\n"
                    "**SOL:** `CxcyRKWqJq9JqHhB7t8RS4631AqTUC3xs8vJyWngwFm5`\n"
                    "**USDT (ERC20):** `0xe69719B096b44341d5bE5e7b218474d4616ab331`\n"
                    "**Gift Cards:** rewarble, giftmecrypto (dm <@110332657337913344> to donate with gift cards)\n\n"
                    "If you donated, DM <@110332657337913344> to claim your donator role."
                )
                await interaction.response.send_message("check your DMs for donation info", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message("couldn't DM you. enable DMs from server members", ephemeral=True)

        elif interaction.data.get("custom_id") == "contribute_button":
            await interaction.response.send_message(
                "to contribute you must be a woman or a man. by contributing you give us a free fan sign to use for our service.\n"
                "DM <@110332657337913344> to contribute. You will also get a Contributor role if you actually contribute.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(FanSign(bot))
