import os
import urllib.request

IMAGES_TO_DOWNLOAD = {
    'dior_sauvage.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/DIOR_20-_20SauvageEDT_a2097c45-d917-4e40-9352-04648721c747.jpg?v=1775848714',
    'dior_miss_dior.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/missdiorbloomingbouquet-woman.jpg?v=1775844475',
    'dior_jadore.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/Dior_J_adore_b0570ace-43d0-496b-b924-e7027d8f16bf.jpg?v=1775848609',
    'dior_fahrenheit.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/diorfahrenheit-man.jpg?v=1775841593',
    'armani_acqua_di_gio.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/giorgioarmaniacquadigioleparfumedition2023-man.jpg?v=1775842365',
    'armani_acqua_di_gioia.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/GiorgioArmaniAcquaDiGioia_2000w01_5fbd2fb1-8ebc-47b9-8667-7e404dfa002c.jpg?v=1775837421',
    'dg_light_blue_pour_homme.jpg': 'https://cdn.shopify.com/s/files/1/0580/7420/2293/files/02zw8bpypw.png?v=1761157818',
    'dg_light_blue_pour_femme.jpg': 'https://cdn.shopify.com/s/files/1/0580/7420/2293/files/01_f447b927-9a6b-4eff-8b18-9a3aaff00151.png?v=1776704793',
    'versace_eros.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/VersaceErosEDP100ml-man.jpg?v=1775845836',
    'versace_eros_pour_femme.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/versacerosfemme-woman_dae05311-e0c3-4558-8e52-2fd433855cd4.jpg?v=1775845835',
    'spicebomb.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/spicebombextreme-man.jpg?v=1775845476',
    'flowerbomb.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/victorrolfflowerbombextremeintense_orig03_c270ddec-f9a7-4588-9220-6f16af5298c5.jpg?v=1775848640',
    'carolina_herrera_bad_boy.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/CHBadBoyCobaltEdition-man.jpg?v=1775839962',
    'carolina_herrera_good_girl.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/goodgirlnobox-woman.jpg?v=1777912548',
    'paco_rabanne_1_million.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/pacorabanne1millionroyal-man_80ae62a3-52c4-4b89-b761-a90f1d9ccae4.jpg?v=1781566716',
    'jpg_le_male.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/jpglemaleleparfum-man.jpg?v=1775843778',
    'jpg_la_belle.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/jpglabelle2019-woman_4585339c-aca3-46a5-8dd8-c42a8515e896.jpg?v=1775843655',
    'ysl_black_opium.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/yvessaintlaurentyslblackopiumedp-woman.jpg?v=1775845994',
    'ysl_y_edp.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/YSL_Y_EDP_100ml.jpg?v=1775846011',
    'versace_bright_crystal.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/brightcrystal-woman_a4b904ca-b3a5-4d4b-aada-134f959a6b0b.jpg?v=1775839309',
    'marc_jacobs_daisy.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/marcjacobsdaisy-woman_7d38754a-c5b1-4e56-94df-cb913dceb147.jpg?v=1775840504',
    'guerlain_shalimar.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/guerlainshalimarEDP-woman.jpg?v=1775842932',
    'hermes_terre_d_hermes.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/hermesterre-man_c5c0071e-e0dc-4c66-aac1-ee36d6bc6ea1.jpg?v=1781564551',
    'lattafa_yara.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/LattafaYara-woman_7481e262-8259-44da-a049-f97cb0509595.jpg?v=1775844171',
    'lattafa_oud_for_glory.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/LattafaOudForGlory100mlEDP-man_c364751f-9b43-4a9a-bced-c4390ace1f43.jpg?v=1775844130',
    'montblanc_explorer.jpg': 'https://cdn.shopify.com/s/files/1/0215/6845/4756/files/montblancexplorer-man_6e4577a9-ef6e-466f-82c7-431c909398c8.jpg?v=1775844594'
}

dest_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'public', 'images')
os.makedirs(dest_dir, exist_ok=True)

for fname, url in IMAGES_TO_DOWNLOAD.items():
    dest_path = os.path.join(dest_dir, fname)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp, open(dest_path, 'wb') as out_file:
            out_file.write(resp.read())
        print(f"Downloaded: {fname} ({os.path.getsize(dest_path)} bytes)")
    except Exception as e:
        print(f"Failed {fname}: {e}")
