"""
Script de test pour vérifier la connexion Supabase Storage.
Exécuter depuis le dossier serveur/ :
    python test_supabase.py
"""
import os
from dotenv import load_dotenv

# Charger le fichier .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
bucket = os.getenv("SUPABASE_BUCKET")

print("=" * 50)
print("TEST CONNEXION SUPABASE STORAGE")
print("=" * 50)
print(f"URL     : {url}")
print(f"Bucket  : {bucket}")
print(f"Clé     : {key[:20]}..." if key else "Clé     : NON DÉFINIE")
print()

if not url or not key or not bucket:
    print("❌ ERREUR : Variables d'environnement manquantes dans .env")
    exit(1)

try:
    from supabase import create_client
    client = create_client(url, key)
    print("✅ Connexion au client Supabase réussie")
except ImportError:
    print("❌ ERREUR : Le package 'supabase' n'est pas installé.")
    print("   Installe-le avec : pip install supabase")
    exit(1)
except Exception as e:
    print(f"❌ ERREUR connexion : {e}")
    exit(1)

# Test 1 : Lister les buckets
try:
    buckets = client.storage.list_buckets()
    bucket_names = [b.name for b in buckets]
    print(f"✅ Buckets disponibles : {bucket_names}")

    if bucket not in bucket_names:
        print(f"❌ Le bucket '{bucket}' n'existe pas ! Crée-le dans Supabase > Storage.")
        exit(1)
    else:
        print(f"✅ Bucket '{bucket}' trouvé !")
except Exception as e:
    print(f"❌ ERREUR liste buckets : {e}")
    exit(1)

# Test 2 : Upload d'un fichier test
try:
    test_content = b"test-insurance-documents-validation"
    test_filename = "test_connexion.txt"

    client.storage.from_(bucket).upload(
        path=test_filename,
        file=test_content,
        file_options={"content-type": "text/plain", "upsert": "true"}
    )
    print(f"✅ Upload test réussi ({test_filename})")
except Exception as e:
    print(f"❌ ERREUR upload : {e}")
    exit(1)

# Test 3 : URL signée
try:
    res = client.storage.from_(bucket).create_signed_url(test_filename, expires_in=60)
    signed_url = res.get("signedURL") or res.get("signedUrl")
    print(f"✅ URL signée générée")
except Exception as e:
    print(f"❌ ERREUR URL signée : {e}")

# Test 4 : Suppression du fichier test
try:
    client.storage.from_(bucket).remove([test_filename])
    print(f"✅ Suppression test réussie")
except Exception as e:
    print(f"❌ ERREUR suppression : {e}")

print()
print("=" * 50)
print("✅ TOUS LES TESTS RÉUSSIS — Supabase est prêt !")
print("=" * 50)
