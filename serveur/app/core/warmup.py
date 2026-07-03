#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/core/warmup.py

Lance une inference factice au demarrage du serveur pour forcer cuDNN a
faire son auto-tuning et stabiliser la memoire GPU AVANT que le premier
vrai document n'arrive. A appeler dans l'evenement startup de FastAPI,
juste apres ModelManager.get_instance().load().
"""

import time
import torch
from PIL import Image

from app.ocr.inference import query_qwen


def warmup_model():
    print("[WARMUP] Demarrage du rechauffement GPU...")
    t0 = time.perf_counter()
    try:
        dummy_image = Image.new("RGB", (600, 600), color=(255, 255, 255))
        _ = query_qwen(
            dummy_image,
            'Reponds uniquement: {"ok": true}',
            max_tokens=16,
            resolution_limit=512,
            label="warmup",
        )
        torch.cuda.synchronize()
        print(f"[WARMUP] OK Rechauffement termine en {time.perf_counter()-t0:.1f}s")
    except Exception as e:
        print(f"[WARMUP] Echec du rechauffement (non bloquant) : {e}")