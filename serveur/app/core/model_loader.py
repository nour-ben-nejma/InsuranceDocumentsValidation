#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ModelManager – charge le modele Qwen2.5-VL-7B (tounsi17/qwen) UNE SEULE FOIS
et le garde en memoire pour toute la duree de vie du serveur FastAPI.

Pourquoi un singleton :
  - Sur Colab, le modele etait recharge a chaque session (cellule d'init).
  - Dans une API, si on n'utilise pas de singleton, chaque appel a la fonction
    d'extraction rechargerait ~6-8 GB de VRAM depuis le disque a chaque requete
    -> latence enorme + risque de saturer les 8 GB de la RTX 4060.
  - Avec le singleton, le chargement (10-40s selon le disque) ne se fait
    qu'une fois, au demarrage du serveur (voir app/main.py -> startup event).
"""

import os
import sys
import time
import threading

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import torch
from transformers import (
    Qwen2_5_VLForConditionalGeneration,
    AutoProcessor,
    BitsAndBytesConfig,
)

MODEL_NAME = "tounsi17/qwen"


class ModelManager:
    """
    Singleton thread-safe. Usage partout dans le code :

        from app.core.model_loader import ModelManager

        mgr = ModelManager.get_instance()
        model = mgr.model
        processor = mgr.processor
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        # Empeche l'instanciation directe (utiliser get_instance())
        if ModelManager._instance is not None:
            raise RuntimeError(
                "ModelManager est un singleton. Utilise ModelManager.get_instance()."
            )
        self.model = None
        self.processor = None
        self.device = None
        self._loaded = False

    @classmethod
    def get_instance(cls) -> "ModelManager":
        """Retourne l'instance unique, la cree si necessaire (thread-safe)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def load(self, force_reload: bool = False):
        """
        Charge le modele en memoire. Appele UNE FOIS au demarrage du serveur
        (voir app/main.py). Si le modele est deja charge, ne fait rien
        (sauf si force_reload=True).
        """
        if self._loaded and not force_reload:
            print("[ModelManager] Modele deja charge, skip.")
            return

        if not torch.cuda.is_available():
            raise RuntimeError(
                "Aucun GPU CUDA detecte. Verifie que venv_ocr est active "
                "et que torch a ete installe avec --index-url .../cu121 "
                "(voir torch.cuda.is_available())."
            )

        print(f"[ModelManager] GPU detecte : {torch.cuda.get_device_name(0)}")
        print(f"[ModelManager] Chargement de {MODEL_NAME} en 4-bit...")

        t0 = time.perf_counter()

        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,  # economise ~300-400MB supplementaires
        )

        try:
            self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                MODEL_NAME,
                quantization_config=quantization_config,
                device_map={"": 0},
                attn_implementation="sdpa",
            )
            self.model.eval()

            self.processor = AutoProcessor.from_pretrained(MODEL_NAME)
            self.processor.tokenizer.padding_side = "left"

            self.device = "cuda"
            self._loaded = True

            elapsed = time.perf_counter() - t0
            print(f"[ModelManager] OK Modele charge en {elapsed:.1f}s")

        except Exception as e:
            print(f"[ModelManager] ECHEC du chargement : {e}")
            raise

    def unload(self):
        """Libere la memoire GPU (utile pour les tests ou un reload propre)."""
        if self.model is not None:
            del self.model
            del self.processor
            torch.cuda.empty_cache()
            self.model = None
            self.processor = None
            self._loaded = False
            print("[ModelManager] Modele decharge, VRAM liberee.")

    @property
    def is_loaded(self) -> bool:
        return self._loaded


# ---------------------------------------------------------------------
# Fonction utilitaire pour un acces rapide depuis n'importe quel module
# ---------------------------------------------------------------------
def get_model_and_processor():
    """
    Raccourci utilise dans ocr/inference.py :

        from app.core.model_loader import get_model_and_processor
        model, processor = get_model_and_processor()
    """
    mgr = ModelManager.get_instance()
    if not mgr.is_loaded:
        raise RuntimeError(
            "Le modele n'est pas encore charge. "
            "Verifie que ModelManager.get_instance().load() est appele "
            "dans l'evenement startup de FastAPI (app/main.py)."
        )
    return mgr.model, mgr.processor


if __name__ == "__main__":
    # Test manuel : python app/core/model_loader.py
    mgr = ModelManager.get_instance()
    mgr.load()
    print("Test OK :", mgr.is_loaded)