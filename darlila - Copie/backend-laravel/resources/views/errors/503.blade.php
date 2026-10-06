<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Planet Kids — Maintenance</title>
<style>
  :root { --indigo:#0F1A2B; --indigo2:#1B2C47; --gold:#C9A227; --gold2:#E4C767; --ivory:#FAF6EC; }
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    font-family: Georgia, 'Times New Roman', serif;
    background: linear-gradient(140deg, var(--indigo) 0%, var(--indigo2) 100%);
    color: var(--ivory); min-height: 100vh;
    display: flex; align-items: center; justify-content: center;
    text-align: center; padding: 40px 20px;
  }
  .zellige {
    width: 100%; height: 34px; position: fixed; top: 0; left: 0;
    background-repeat: repeat-x; background-size: 68px 34px; opacity: .8;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='68' height='34' viewBox='0 0 68 34'%3E%3Cg fill='none' stroke='%23C9A227' stroke-width='1.1' opacity='0.55'%3E%3Cpath d='M17 2 L25 17 L17 32 L9 17 Z'/%3E%3Cpath d='M51 2 L59 17 L51 32 L43 17 Z'/%3E%3Cpath d='M0 17 L8.5 9 L17 17 L8.5 25 Z'/%3E%3Cpath d='M34 17 L42.5 9 L51 17 L42.5 25 Z'/%3E%3Cpath d='M68 17 L59.5 9 L51 17 L59.5 25 Z'/%3E%3C/g%3E%3C/svg%3E");
  }
  .star { width: 88px; height: 88px; margin: 0 auto 26px; animation: spin 14s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .logo { font-size: 30px; letter-spacing: 1px; color: var(--gold2); margin-bottom: 8px; }
  .logo .dot { display:inline-block; width:9px; height:9px; border-radius:50%; background: var(--gold); margin-right: 10px; }
  h1 { font-size: clamp(26px, 5vw, 40px); margin-bottom: 16px; font-weight: 600; }
  p.msg { max-width: 480px; margin: 0 auto 8px; line-height: 1.7; opacity: .92; font-size: 16px; }
  .ar { direction: rtl; font-family: 'Traditional Arabic', 'Amiri', serif; opacity: .8; font-size: 15px; }
  .wa {
    display: inline-flex; align-items: center; gap: 10px; margin-top: 30px;
    background: #25D366; color: #fff; text-decoration: none;
    padding: 14px 28px; border-radius: 3px; font-size: 14px; font-weight: 600;
    font-family: Arial, sans-serif;
  }
  .retry { margin-top: 14px; opacity: .55; font-size: 13px; font-family: Arial, sans-serif; }
</style>
</head>
<body>
<div class="zellige"></div>

<div>
  <svg class="star" viewBox="0 0 100 100" fill="none" stroke="#C9A227" stroke-width="1.4">
    <path d="M50 4 L61 39 L96 50 L61 61 L50 96 L39 61 L4 50 L39 39 Z"/>
    <path d="M50 22 L57 43 L78 50 L57 57 L50 78 L43 57 L22 50 L43 43 Z" opacity=".7"/>
    <circle cx="50" cy="50" r="4" fill="#C9A227" stroke="none"/>
  </svg>

  <div class="logo-pill"><img src="/logo-planet-kids.png" alt="Planet Kids" style="height:30px;"></div>
  <div class="tagline">KHEMICI SHOP</div>
  <h1>Nous revenons très vite</h1>
  <p class="msg">{{ $message ?? 'La boutique est momentanément en maintenance pour s’améliorer. Merci de votre patience !' }}</p>
  <p class="msg ar">المتجر مغلق مؤقتاً للصيانة والتحسين. شكراً لصبركم!</p>

  <a class="wa" href="https://wa.me/213555000000" target="_blank" rel="noopener">
    En attendant, commandez sur WhatsApp
  </a>

  <p class="retry">Réessayez dans quelques minutes — HTTP 503 (Retry-After: {{ $retryAfter ?? 300 }} s)</p>
</div>
</body>
</html>
