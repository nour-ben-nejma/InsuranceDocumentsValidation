import os
import glob
import shutil
import tempfile
from abc import ABC, abstractmethod
from typing import Optional

class BaseStorageProvider(ABC):
    @abstractmethod
    def upload_file(self, content: bytes, filename: str) -> str:
        """Uploads file content and returns the file path or identifier."""
        pass

    @abstractmethod
    def delete_file(self, dossier_id: str, doc_key: str) -> None:
        """Deletes the file associated with a dossier and document key."""
        pass

    @abstractmethod
    def get_local_filepath(self, dossier_id: str, doc_key: str) -> Optional[str]:
        """Returns a local file path to the document. Downloads from S3 if necessary."""
        pass

    @abstractmethod
    def get_view_url(self, dossier_id: str, doc_key: str) -> Optional[str]:
        """Returns a URL to view the document (local route or S3 presigned URL)."""
        pass

    @abstractmethod
    def delete_dossier_files(self, dossier_id: str) -> None:
        """Deletes all files associated with a dossier."""
        pass


class LocalStorageProvider(BaseStorageProvider):
    def __init__(self, upload_dir: str):
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    def _find_file(self, dossier_id: str, doc_key: str) -> Optional[str]:
        pattern = os.path.join(self.upload_dir, f"{dossier_id}_{doc_key}.*")
        matches = glob.glob(pattern)
        return matches[0] if matches else None

    def upload_file(self, content: bytes, filename: str) -> str:
        # filename is e.g. "dossier_id_doc_key.ext"
        file_path = os.path.join(self.upload_dir, filename)
        with open(file_path, "wb") as f:
            f.write(content)
        return file_path

    def delete_file(self, dossier_id: str, doc_key: str) -> None:
        pattern = os.path.join(self.upload_dir, f"{dossier_id}_{doc_key}.*")
        for old_file in glob.glob(pattern):
            try:
                os.remove(old_file)
            except Exception as e:
                print(f"[LocalStorageProvider] Error deleting file {old_file}: {e}")

    def get_local_filepath(self, dossier_id: str, doc_key: str) -> Optional[str]:
        return self._find_file(dossier_id, doc_key)

    def get_view_url(self, dossier_id: str, doc_key: str) -> Optional[str]:
        # Return the local API endpoint path
        return f"/dossiers/{dossier_id}/documents/{doc_key}/view"

    def delete_dossier_files(self, dossier_id: str) -> None:
        pattern = os.path.join(self.upload_dir, f"{dossier_id}_*")
        for old_file in glob.glob(pattern):
            try:
                os.remove(old_file)
            except Exception as e:
                print(f"[LocalStorageProvider] Error deleting dossier file {old_file}: {e}")


class S3StorageProvider(BaseStorageProvider):
    def __init__(
        self,
        bucket_name: str,
        access_key: str,
        secret_key: str,
        region: str = "us-east-1",
        endpoint_url: Optional[str] = None
    ):
        try:
            import boto3
            from botocore.config import Config
        except ImportError:
            raise RuntimeError(
                "La bibliothèque 'boto3' est requise pour utiliser le stockage S3. "
                "Veuillez l'installer avec : pip install boto3"
            )

        self.bucket_name = bucket_name
        
        # Configure client with signature version for presigned URLs
        config = Config(signature_version='s3v4')
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            endpoint_url=endpoint_url,
            config=config
        )

        # Create temporary directory for local caching/OCR processing
        self.tmp_dir = os.path.join(tempfile.gettempdir(), "idv_s3_cache")
        os.makedirs(self.tmp_dir, exist_ok=True)

    def _find_s3_key(self, dossier_id: str, doc_key: str) -> Optional[str]:
        """Lists keys with prefix to find the correct extension."""
        prefix = f"{dossier_id}_{doc_key}."
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            for obj in response.get("Contents", []):
                key = obj["Key"]
                # Verify exact prefix match (excluding directory matches if any)
                if key.startswith(prefix):
                    return key
        except Exception as e:
            print(f"[S3StorageProvider] Error listing objects: {e}")
        return None

    def upload_file(self, content: bytes, filename: str) -> str:
        # Delete old key with different extension first if any
        # extract dossier_id and doc_key from filename (e.g. dossierId_docKey.png)
        base = os.path.splitext(filename)[0]
        if "_" in base:
            parts = base.split("_")
            dossier_id = parts[0]
            doc_key = "_".join(parts[1:])
            self.delete_file(dossier_id, doc_key)

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=filename,
            Body=content
        )
        return filename

    def delete_file(self, dossier_id: str, doc_key: str) -> None:
        # Find key
        key = self._find_s3_key(dossier_id, doc_key)
        if key:
            try:
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            except Exception as e:
                print(f"[S3StorageProvider] Error deleting key {key}: {e}")

        # Also clean up any local cached copy
        for old_file in glob.glob(os.path.join(self.tmp_dir, f"{dossier_id}_{doc_key}.*")):
            try:
                os.remove(old_file)
            except Exception:
                pass

    def get_local_filepath(self, dossier_id: str, doc_key: str) -> Optional[str]:
        key = self._find_s3_key(dossier_id, doc_key)
        if not key:
            return None

        # Check if already cached locally
        ext = os.path.splitext(key)[1]
        local_path = os.path.join(self.tmp_dir, f"{dossier_id}_{doc_key}{ext}")
        if os.path.exists(local_path):
            return local_path

        # Clean old cached extensions first
        for old_file in glob.glob(os.path.join(self.tmp_dir, f"{dossier_id}_{doc_key}.*")):
            try:
                os.remove(old_file)
            except Exception:
                pass

        # Download from S3 to cache
        try:
            self.s3_client.download_file(self.bucket_name, key, local_path)
            return local_path
        except Exception as e:
            print(f"[S3StorageProvider] Error downloading {key}: {e}")
            return None

    def get_view_url(self, dossier_id: str, doc_key: str) -> Optional[str]:
        key = self._find_s3_key(dossier_id, doc_key)
        if not key:
            return None

        # Generate a presigned URL that expires in 15 minutes (900 seconds)
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=900
            )
            return url
        except Exception as e:
            print(f"[S3StorageProvider] Error generating presigned URL: {e}")
            return None

    def delete_dossier_files(self, dossier_id: str) -> None:
        prefix = f"{dossier_id}_"
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            objects_to_delete = []
            for obj in response.get("Contents", []):
                objects_to_delete.append({"Key": obj["Key"]})

            if objects_to_delete:
                self.s3_client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={"Objects": objects_to_delete}
                )
        except Exception as e:
            print(f"[S3StorageProvider] Error deleting dossier files: {e}")

        # Clean local cache too
        for old_file in glob.glob(os.path.join(self.tmp_dir, f"{dossier_id}_*")):
            try:
                os.remove(old_file)
            except Exception:
                pass



class SupabaseStorageProvider(BaseStorageProvider):
    def __init__(self, url: str, service_key: str, bucket: str):
        try:
            from supabase import create_client
        except ImportError:
            raise RuntimeError(
                "La bibliothèque 'supabase' est requise. "
                "Installez-la avec : pip install supabase"
            )
        self.client = create_client(url, service_key)
        self.bucket = bucket
        self.tmp_dir = os.path.join(tempfile.gettempdir(), "idv_supabase_cache")
        os.makedirs(self.tmp_dir, exist_ok=True)

    def _object_key(self, dossier_id: str, doc_key: str, ext: str = "") -> str:
        return f"{dossier_id}_{doc_key}{ext}"

    def _find_remote_path(self, dossier_id: str, doc_key: str) -> Optional[str]:
        """Lists bucket objects to find the file with any extension."""
        prefix = f"{dossier_id}_{doc_key}."
        try:
            objects = self.client.storage.from_(self.bucket).list()
            for obj in objects:
                if obj["name"].startswith(prefix):
                    return obj["name"]
        except Exception as e:
            print(f"[SupabaseStorageProvider] Error listing objects: {e}")
        return None

    def upload_file(self, content: bytes, filename: str) -> str:
        # Delete old version first (different extension possible)
        base = os.path.splitext(filename)[0]
        if "_" in base:
            parts = base.split("_")
            dossier_id = parts[0]
            doc_key = "_".join(parts[1:])
            self.delete_file(dossier_id, doc_key)

        try:
            ext = os.path.splitext(filename)[1].lower()
            content_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else \
                           "image/png" if ext == ".png" else \
                           "application/pdf" if ext == ".pdf" else \
                           "application/octet-stream"
            self.client.storage.from_(self.bucket).upload(
                path=filename,
                file=content,
                file_options={"content-type": content_type, "upsert": "true"}
            )
        except Exception as e:
            print(f"[SupabaseStorageProvider] Error uploading {filename}: {e}")
        return filename

    def delete_file(self, dossier_id: str, doc_key: str) -> None:
        remote_path = self._find_remote_path(dossier_id, doc_key)
        if remote_path:
            try:
                self.client.storage.from_(self.bucket).remove([remote_path])
            except Exception as e:
                print(f"[SupabaseStorageProvider] Error deleting {remote_path}: {e}")
        # Clean local cache
        for f in glob.glob(os.path.join(self.tmp_dir, f"{dossier_id}_{doc_key}.*")):
            try:
                os.remove(f)
            except Exception:
                pass

    def get_local_filepath(self, dossier_id: str, doc_key: str) -> Optional[str]:
        remote_path = self._find_remote_path(dossier_id, doc_key)
        if not remote_path:
            return None

        ext = os.path.splitext(remote_path)[1]
        local_path = os.path.join(self.tmp_dir, f"{dossier_id}_{doc_key}{ext}")
        if os.path.exists(local_path):
            return local_path

        # Clean old cached extensions
        for f in glob.glob(os.path.join(self.tmp_dir, f"{dossier_id}_{doc_key}.*")):
            try:
                os.remove(f)
            except Exception:
                pass

        try:
            data = self.client.storage.from_(self.bucket).download(remote_path)
            with open(local_path, "wb") as f:
                f.write(data)
            return local_path
        except Exception as e:
            print(f"[SupabaseStorageProvider] Error downloading {remote_path}: {e}")
            return None

    def get_view_url(self, dossier_id: str, doc_key: str) -> Optional[str]:
        remote_path = self._find_remote_path(dossier_id, doc_key)
        if not remote_path:
            return None
        try:
            # Generate a signed URL valid for 15 minutes
            res = self.client.storage.from_(self.bucket).create_signed_url(
                remote_path, expires_in=900
            )
            return res.get("signedURL") or res.get("signedUrl")
        except Exception as e:
            print(f"[SupabaseStorageProvider] Error generating signed URL: {e}")
            return None

    def delete_dossier_files(self, dossier_id: str) -> None:
        prefix = f"{dossier_id}_"
        try:
            objects = self.client.storage.from_(self.bucket).list()
            to_delete = [obj["name"] for obj in objects if obj["name"].startswith(prefix)]
            if to_delete:
                self.client.storage.from_(self.bucket).remove(to_delete)
        except Exception as e:
            print(f"[SupabaseStorageProvider] Error deleting dossier files: {e}")
        # Clean local cache
        for f in glob.glob(os.path.join(self.tmp_dir, f"{dossier_id}_*")):
            try:
                os.remove(f)
            except Exception:
                pass


# Helper to instantiate the correct provider
_provider: Optional[BaseStorageProvider] = None

def get_storage_provider() -> BaseStorageProvider:
    global _provider
    if _provider is not None:
        return _provider

    # --- Supabase Storage ---
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    supabase_bucket = os.getenv("SUPABASE_BUCKET")
    if supabase_url and supabase_key and supabase_bucket:
        print(f"[Storage] Using Supabase Storage Provider (Bucket: {supabase_bucket})")
        _provider = SupabaseStorageProvider(
            url=supabase_url,
            service_key=supabase_key,
            bucket=supabase_bucket
        )
        return _provider

    # --- S3 / Compatible Storage ---
    bucket_name = os.getenv("S3_BUCKET_NAME")
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    endpoint_url = os.getenv("S3_ENDPOINT_URL")
    if bucket_name and access_key and secret_key:
        print(f"[Storage] Using S3 Storage Provider (Bucket: {bucket_name})")
        _provider = S3StorageProvider(
            bucket_name=bucket_name,
            access_key=access_key,
            secret_key=secret_key,
            region=region,
            endpoint_url=endpoint_url
        )
        return _provider

    # --- Fallback: Local Storage ---
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    upload_dir = os.path.join(base_dir, "storage", "images")
    print(f"[Storage] Using Local Storage Provider (Folder: {upload_dir})")
    _provider = LocalStorageProvider(upload_dir=upload_dir)
    return _provider
