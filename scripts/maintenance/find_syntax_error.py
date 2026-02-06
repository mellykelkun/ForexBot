import ast
import sys

def find_syntax_error(filename):
    """Trouve l'erreur de syntaxe exacte"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier la syntaxe
        ast.parse(content)
        print("✅ Aucune erreur de syntaxe trouvée")
        return True
        
    except SyntaxError as e:
        print(f"❌ Erreur de syntaxe trouvée:")
        print(f"   Fichier: {filename}")
        print(f"   Ligne {e.lineno}: {e.msg}")
        
        # Afficher le contexte
        lines = content.split('\n')
        error_line = e.lineno - 1
        start = max(0, error_line - 2)
        end = min(len(lines), error_line + 3)
        
        print(f"\n📝 Contexte autour de la ligne {e.lineno}:")
        for i in range(start, end):
            marker = ">>> " if i == error_line else "    "
            print(f"{marker}{i+1}: {lines[i]}")
        
        return False

if __name__ == "__main__":
    find_syntax_error("backend/bots/bot_btcusd_ultra_scalper_v8_robus.py")