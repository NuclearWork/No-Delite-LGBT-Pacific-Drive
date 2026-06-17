import os
from PIL import Image

mapping = {
    'Flag-Abrosexual.png': (0, 0, 192, 128),
    'Flag-Agender.png': (384, 0, 192, 128),
    'Flag-Asexual.png': (192, 0, 192, 128),
    'Flag-BLM.png': (0, 768, 192, 256),
    'Flag-Bigender_Redesign.png': (576, 0, 192, 128),
    'Flag-Bisexual.png': (0, 128, 192, 128),
    'Flag-Demisexual.png': (192, 128, 192, 128),
    'Flag-Gay_Man.png': (384, 128, 192, 128),
    'Flag-Genderfluid.png': (576, 256, 192, 128),
    'Flag-Genderflux.png': (384, 384, 192, 128),
    'Flag-Genderqueer.png': (0, 256, 192, 128),
    'Flag-Intersex.png': (384, 256, 192, 128),
    'Flag-Lesbian_5_Stripe.png': (192, 512, 192, 128),
    'Flag-Lgbtq.png': (576, 128, 192, 128),
    'Flag-Lgbtq_progress.png': (192, 384, 192, 128),
    'Flag-Neutrois.png': (576, 384, 192, 128),
    'Flag-NonBinary.png': (384, 512, 192, 128),
    'Flag-Pangender.png': (192, 256, 192, 128),
    'Flag-Pansexual.png': (0, 384, 192, 128),
    'Flag-Polysexual.png': (192, 640, 192, 128),
    'Flag-Queer.png': (0, 512, 192, 128),
    'Flag-Straight_Ally.png': (0, 640, 192, 128),
    'Flag-Transgender.png': (384, 640, 192, 128),
}

atlas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))

for name, (x, y, w, h) in mapping.items():
    path = os.path.join("original_pngs", name)
    if os.path.exists(path):
        img = Image.open(path).convert("RGBA")
        img_resized = img.resize((w, h), Image.Resampling.LANCZOS)
        atlas.paste(img_resized, (x, y), img_resized)

atlas.save("T_Flags_01_D_reconstructed.png")
atlas.save("T_Flags_01_D.png") # So that auto_paste2.py works again
print("Reconstructed original atlas.")
