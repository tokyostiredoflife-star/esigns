import discord
from discord import app_commands
from discord.ext import commands
from pathlib import Path
import importlib
import sys
import io
import re
from PIL import Image, ImageFilter

BASE_DIR = Path(__file__).resolve().parent.parent
FONTS_DIR = BASE_DIR / "fonts"
STYLES_DIR = BASE_DIR / "commands" / "premstyles"
KEYS_FILE = BASE_DIR / "keys.txt"

BLUR_SCALE = 5


def load_redeemed_ids():
    ids = set()
    if not KEYS_FILE.exists():
        return ids
    with open(KEYS_FILE, 'r') as f:
        for line in f:
            parts = line.strip().split(":")
            if len(parts) == 2:
                ids.add(parts[1].strip())
    return ids


class PremiumFanSign(commands.Cog):
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
        module_path = f"commands.premstyles.{style_name}"
        if module_path in sys.modules:
            return sys.modules[module_path]
        return importlib.import_module(module_path)

    def can_use_premgen(self, interaction: discord.Interaction) -> bool:
        channel = interaction.channel
        ALLOWED_CATEGORY_ID = 1402021400507580466
        EXCLUDED_CHANNEL_ID = 1404173830666064002

        if channel.category and channel.category.id == ALLOWED_CATEGORY_ID:
            if channel.id != EXCLUDED_CHANNEL_ID:
                return True
        return False

    @app_commands.command(name="premgen", description="Generate a premium-style fansign (requires a premium key).")
    @app_commands.describe(
        text="Text to display (max 14 characters)",
        font="Font to use",
        style="Premium style layout"
    )
    @app_commands.checks.cooldown(1, 1.0)
    async def premgen(
        self,
        interaction: discord.Interaction,
        text: str,
        font: str,
        style: str
    ):
        if not self.can_use_premgen(interaction):
            await interaction.response.send_message(
                "You can only use this command in the allowed category channels (except the excluded channel).",
                ephemeral=True
            )
            return

        redeemed_ids = load_redeemed_ids()
        if str(interaction.user.id) not in redeemed_ids:
            await interaction.response.send_message(
                "You don't have premium access. Use a valid key with `/redeem` first.",
                ephemeral=True
            )
            return

        if len(text) > 14:
            await interaction.response.send_message("Text can only be 14 characters max.", ephemeral=True)
            return

        available_fonts = self.get_available_fonts()
        if font not in available_fonts:
            await interaction.response.send_message(
                f"Invalid font. Available fonts: {', '.join(available_fonts)}",
                ephemeral=True
            )
            return

        available_styles = self.get_available_styles()
        if style.lower() not in available_styles:
            await interaction.response.send_message(
                f"Invalid style. Available premium styles: {', '.join(available_styles)}",
                ephemeral=True
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
                await interaction.followup.send(
                    f"Style module missing function `{generate_func_name}`",
                    ephemeral=True
                )
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
                title="Your Premium Fansign",
                description="Generated with premium style access.",
                color=discord.Color.teal()
            )
            embed.add_field(name="Text", value=text, inline=True)
            embed.add_field(name="Font", value=font, inline=True)
            embed.add_field(name="Style", value=style, inline=True)
            embed.set_image(url=f"attachment://{file.filename}")
            embed.set_footer(text="Thank you for supporting this project.")

            await interaction.followup.send(
                content=f"Enjoy your premium fansign, {interaction.user.mention}.",
                embed=embed,
                file=file
            )

        except Exception as e:
            print(f"Error generating premium fansign: {e}")
            await interaction.followup.send(f"error: `{e}`", ephemeral=True)

    @premgen.error
    async def premgen_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.errors.CommandOnCooldown):
            embed = discord.Embed(
                title="Slow down...",
                description="You're doing that too fast. Try again in a few seconds.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Something went wrong.", ephemeral=True)
            raise error

    @premgen.autocomplete("font")
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

    @premgen.autocomplete("style")
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


async def setup(bot):
    await bot.add_cog(PremiumFanSign(bot))
