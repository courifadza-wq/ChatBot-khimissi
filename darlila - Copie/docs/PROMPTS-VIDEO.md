# 🎬 Prompts vidéo PRO — Hero Dar Lila

Deux prompts de niveau publicitaire pour générer les vidéos du diaporama
du hero (`public/hero-video.mp4` et `public/hero2-video.mp4`).

**Cible** : 16:9, 1920×1080, ~8 s, muet, H.264 ≤ 10 Mo
**Palette de marque** : ivoire `#FAF6EC` · or `#C9A227` / `#E4C767` · indigo `#0F1A2B`
**Règle d'or** : aucun visage de bébé ni visage humain (les IA génèrent des
visages peu naturels) — cadrage mains / silhouettes / produits, comme les
vraies publicités premium.

---

## VIDÉO 1 — « Le Rituel Douceur » (cosmétiques & layette)

### Prompt maître (copier-coller dans Sora / Kling / Runway / Luma)

```
CINEMATIC LUXURY COMMERCIAL, 8 seconds, 16:9, 1920×1080, 24fps, muted.

SCENE: A serene, sun-drenched artisanal nursery styling table near a tall
window with sheer linen curtains. On the table: perfectly folded ivory
organic-cotton baby onesies stacked with visible soft texture, a small
wooden baby hair brush, two amber glass cosmetic bottles with minimal
cream labels, a delicate knitted blanket draped with natural folds, and
a shallow ceramic bowl of white cream with a soft peak texture.

ACTION: A woman's elegant hands with natural manicure (NO FACE VISIBLE,
framed from wrists only) enter frame slowly and gently unfold the top
onesie, revealing embroidered detail; then fingertips take a pearl of
cream from the bowl and let it melt slowly between fingers in macro close-up.

CAMERA: Start on a slow lateral dolly left-to-right at table height
(35mm lens, f/2.0, shallow depth of field, background dissolving into
warm golden bokeh), then a seamless push-in to an extreme macro shot of
the cream texture between fingertips. Single continuous take, gimbal-smooth.

LIGHTING: Soft morning sunlight streaming through the linen curtain from
frame left, visible volumetric dust particles floating in the light beam,
gentle shadows, warm golden-hour color temperature (~4200K), subtle bounce
fill from an ivory reflector.

COLOR GRADE: Warm ivory and honey-gold palette — cream white #FAF6EC,
soft gold #E4C767, muted warm beige, one accent of deep indigo #0F1A2B
in the blanket edge. Filmic LUT, soft film grain, high-end skincare
commercial aesthetic.

MOOD: Tenderness, artisanal craftsmanship, pure premium softness.
Slow, breathing rhythm — nothing rushed.

STYLE: In the style of a high-end French skincare commercial shot on
ARRI Alexa with vintage-coated lenses. Photorealistic, ultra-detailed
fabric and cream textures.

NEGATIVE: no faces, no babies, no text, no logos, no watermarks,
no distorted hands, no extra fingers, no plastic-looking skin,
no oversaturation, no camera shake.
```

### Brief français (vidéaste / tournage réel)

Table de style « nursery artisanale » près d'une fenêtre à rideaux de lin.
Body en coton bio ivoire pliés, brosse en bois, flacons ambrés, bol de
crème blanche. Des mains de femme (poignets seulement, sans visage)
déplient le body, une goutte de crème fond entre les doigts en macro.
Travelling latéral lent puis push-in macro, 35 mm f/2.0, bokeh doré.
Soleil du matin à travers le lin, particules dans le faisceau, 4200 K.
Style publicité skincare française haut de gamme.

---

## VIDÉO 2 — « L'Élégance en Mouvement » (poussette premium)

### Prompt maître (copier-coller dans Sora / Kling / Runway / Luma)

```
CINEMATIC LIFESTYLE COMMERCIAL, 8 seconds, 16:9, 1920×1080, 24fps, muted.

SCENE: Golden hour on an elegant, tree-lined promenade with warm
sandstone architecture softly blurred in the background. Autumn-toned
light, long soft shadows stretching across a clean stone pavement.

SUBJECT: A premium baby stroller in ivory cream fabric with cognac
leather handles and subtle gold hardware details, gliding smoothly
toward camera. Seen from behind-the-shoulder: a mother's silhouette
(no face visible, cropped at the shoulders) pushes the stroller with
one graceful hand; a soft ivory muslin blanket drapes gently over the
stroller edge, moving slightly in the breeze. Camera never shows the
baby or any face — focus stays on the stroller's elegant lines, the
leather handle, and the wheel spokes turning in slow motion.

ACTION: The stroller approaches in a smooth, confident glide; light
flares gently between the trees as it passes; at the end of the take
the stroller turns softly toward the sun, backlight rim-lighting its
silhouette with a warm golden halo.

CAMERA: Low tracking shot moving backward in front of the stroller
(~60cm height, 50mm lens, f/2.2), keeping the stroller centered with
the sun flare drifting between branches; ends with a subtle slow-motion
(50% speed) as the light blooms. Single continuous take, Steadicam glide.

LIGHTING: Natural golden-hour backlight (sun low behind the trees,
~3500K), anamorphic-style horizontal lens flare, warm rim light on the
stroller edges, soft fill on fabric textures.

COLOR GRADE: Warm honey gold and cream palette matching an artisanal
luxury brand — ivory #FAF6EC, amber gold #C9A227, warm sandstone, deep
shadow tones in indigo #0F1A2B. Gentle film halation, cinematic 2.39
letterbox feel within 16:9 frame, fine film grain.

MOOD: Quiet confidence, family elegance, "crafted journeys". Calm,
aspirational, unhurried luxury.

STYLE: In the style of a premium European car commercial reinterpreted
for a luxury baby brand; shot on ARRI Alexa Mini with vintage
anamorphic lenses. Photorealistic.

NEGATIVE: no faces, no visible baby, no text, no logos, no watermarks,
no distorted wheels or spinning artifacts, no people walking past,
no modern plastic stroller look, no cold/blue tones, no camera shake.
```

### Brief français (vidéaste / tournage réel)

Promenade bordée d'arbres à l'heure dorée. Poussette premium (tissu ivoire,
poignée cuir cognac, détails dorés) glissant vers la caméra, poussée par
la silhouette d'une mère sans visage, cadrée aux épaules, mousseline
ivoire flottante. Travelling arrière bas (50 mm f/2.2), flare anamorphique,
final au ralenti avec halo doré. Contre-jour 3500 K, rim light doré.
Style publicité automobile premium européenne.

---

## Notes d'exécution

- **Outils IA recommandés** : Sora, Kling 2.0, Runway Gen-3 (cohérence) ;
  Hailuo/Minimax en alternative économique
- **Générer 3-4 variantes** de chaque prompt et garder la meilleure
- **Post-production** : léger fondu entrée/sortie (0,5 s) possible — le site
  gère déjà les transitions entre slides
- **Export** : H.264, 1920×1080, sans piste audio, ≤ 10 Mo
- **Dépôt final** : `frontend-vue/public/hero-video.mp4` et
  `frontend-vue/public/hero2-video.mp4` — détection automatique par le site
- Vidéos lourdes ? Passer par Bunny Stream (player intégré, voir README)
