// ============================================================
//  Mini-librairie YAML pour le fichier intents.yaml
//  Gère le sous-ensemble : maps + listes de scalaires
//  Format cible :
//    intents:
//      "greeting":
//        "patterns":
//          - "bonjour"
// ============================================================

function _quote(s) {
  // double-quote toujours pour éviter tout souci de caractères spéciaux
  return '"' + String(s).replace(/\\/g, '\\\\').replace(/"/g, '\\"') + '"';
}

// ---------- ÉMETTEUR ----------
function emitIntents(obj) {
  var lines = [];
  lines.push('intents:');
  var names = Object.keys(obj || {}).sort();
  names.forEach(function (name) {
    var conf = obj[name] || {};
    lines.push('  ' + _quote(name) + ':');
    lines.push('    ' + _quote('patterns') + ':');
    var pats = Array.isArray(conf.patterns) ? conf.patterns : [];
    if (pats.length === 0) {
      lines.push('      []');
    }
    pats.forEach(function (p) {
      if (p && String(p).trim()) {
        lines.push('      - ' + _quote(String(p)));
      }
    });
  });
  return lines.join('\n') + '\n';
}

// ---------- PARSER (sous-ensemble block) ----------
function parseIntents(text) {
  var result = {};      // { intentName: { patterns: [...] } }
  var lines = String(text).split(/\r?\n/);
  var currentIntent = null;
  var inPatterns = false;

  lines.forEach(function (raw) {
    var line = raw.replace(/\s+$/, '');
    if (!line.trim() || /^\s*#/.test(line)) return; // vide ou commentaire

    // niveau d'indentation
    var indent = line.length - line.replace(/^ +/, '').length;

    // Map au niveau 2 : "intentName":
    if (indent === 2 && /:\s*$/.test(line) && !/^\s*-/.test(line)) {
      currentIntent = unquote(line.replace(/:\s*$/, '').trim());
      result[currentIntent] = { patterns: [] };
      inPatterns = false;
      return;
    }
    // Patterns au niveau 4 : "patterns":
    if (indent === 4 && /:\s*$/.test(line)) {
      inPatterns = true;
      return;
    }
    // élément de liste : - "phrase"   (indent >= 6)
    if (/^\s*-/.test(line)) {
      var val = line.replace(/^\s*-\s*/, '');
      if (currentIntent && inPatterns) {
        result[currentIntent].patterns.push(unquote(val));
      }
      return;
    }
    // ligne au niveau 0 = autre clé racine -> ignorer (on ne touche qu'aux intents)
    if (indent === 0 && currentIntent === null) {
      // "intents:" attendu -> on ne fait rien de spécial
      return;
    }
  });

  // conserve l'ordre d'insertion pour stabilité
  return result;
}

function unquote(s) {
  s = s.trim();
  if (s.length >= 2 && s[0] === '"' && s[s.length - 1] === '"') {
    s = s.slice(1, -1).replace(/\\"/g, '"').replace(/\\\\/g, '\\');
  } else if (s.length >= 2 && s[0] === "'" && s[s.length - 1] === "'") {
    s = s.slice(1, -1).replace(/''/g, "'");
  }
  return s;
}

// expose pour node (test) — en navigateur ces fonctions sont globales
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { emitIntents: emitIntents, parseIntents: parseIntents };
}
