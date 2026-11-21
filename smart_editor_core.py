import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable


SUPPORTED_LANGUAGES = {
    "ar": "العربية",
    "kmr": "الكرمانجية",
    "ckb": "السورانية",
    "en": "الإنجليزية",
}


def normalize_language_code(lang: str) -> str:
    code = (lang or "").strip().lower()
    aliases = {
        "arabic": "ar", "عربي": "ar", "العربية": "ar",
        "kurmanji": "kmr", "كرمانجي": "kmr", "الكرمانجية": "kmr",
        "sorani": "ckb", "سوراني": "ckb", "السورانية": "ckb",
        "english": "en", "انكليزي": "en", "إنجليزي": "en", "الإنجليزية": "en",
    }
    code = aliases.get(code, code)
    if code not in SUPPORTED_LANGUAGES:
        raise ValueError(f"اللغة غير مدعومة: {lang}")
    return code


class SmartVideoEditorProject:
    """نواة حفظ المشاريع وإعدادات الميزات مع حذف يدوي فقط (لا حذف تلقائي نهائياً)."""

    def __init__(
        self,
        projects_root: str = "projects_data",
        tts_synthesizer: Callable[[str, str, str, float, float, str], None] | None = None,
        stt_transcriber: Callable[[str, str], list[dict]] | None = None,
    ):
        self.root = Path(projects_root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.tts_synthesizer = tts_synthesizer
        self.stt_transcriber = stt_transcriber
        self.index_file = self.root / "projects_index.json"
        if not self.index_file.exists():
            self._save_index([])

        self.voices = {
            "narrator_warm": "راوٍ دافئ",
            "dialogue_male": "حوار ذكوري",
            "dialogue_female": "حوار أنثوي",
            "expressive_lead": "تعبيري واضح",
        }

    def _load_index(self) -> list[dict]:
        with self.index_file.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _save_index(self, projects: list[dict]) -> None:
        with self.index_file.open("w", encoding="utf-8") as f:
            json.dump(projects, f, ensure_ascii=False, indent=2)

    def _update_project(self, project_id: str, updater) -> dict:
        projects = self._load_index()
        for idx, p in enumerate(projects):
            if p["id"] == project_id:
                updater(p)
                p["updated_at"] = datetime.now().isoformat(timespec="seconds")
                projects[idx] = p
                self._save_index(projects)
                return p
        raise KeyError(f"المشروع غير موجود: {project_id}")

    def create_project(self, name: str, source_video: str = "") -> dict:
        projects = self._load_index()
        now = datetime.now()
        pid = now.strftime("proj_%Y%m%d_%H%M%S_%f")
        pdir = self.root / pid
        pdir.mkdir(parents=True, exist_ok=True)

        rec = {
            "id": pid,
            "name": name.strip() or "مشروع",
            "source_video": source_video.strip(),
            "created_at": now.isoformat(timespec="seconds"),
            "updated_at": now.isoformat(timespec="seconds"),
            "dir": str(pdir.resolve()),
            "cuts": [],
            "av_sync_offset_sec": 0.0,
            "enable_subtitles": False,
            "active_language": "ar",
            "subtitles": [],
            "enable_voiceover": False,
            "voiceover_lines": [],
            "chroma_key": {"enabled": False, "key_color": "0x00FF00", "similarity": 0.22, "blend": 0.08},
            "image_zoom": {"enabled": False, "zoom_factor": 1.25, "duration_sec": 5.0},
            "voice_changer": {"enabled": False, "preset": "natural", "pitch_semitones": 0.0},
            "noise_removal": {"enabled": False, "noise_reduction_db": 18.0},
            "tracks": [{"id": "trk_1", "name": "مسار 1", "items": []}],
        }
        projects.append(rec)
        self._save_index(projects)
        return rec

    def list_projects(self) -> list[dict]:
        return self._load_index()

    def delete_project_manually(self, project_id: str) -> bool:
        """حذف يدوي صريح فقط؛ لا يتم استدعاؤها تلقائياً أبداً."""
        projects = self._load_index()
        target = next((p for p in projects if p["id"] == project_id), None)
        if not target:
            return False
        pdir = Path(target["dir"])
        if pdir.exists():
            shutil.rmtree(pdir)
        self._save_index([p for p in projects if p["id"] != project_id])
        return True

    def plan_demo_cuts(self, project_id: str) -> list[dict]:
        cuts = [
            {"id": 1, "start": 0.0, "end": 4.5, "mode": "speech", "enabled": True},
            {"id": 2, "start": 4.5, "end": 9.0, "mode": "music", "enabled": True},
        ]
        self._update_project(project_id, lambda p: p.update({"cuts": cuts}))
        return cuts

    def set_feature_flag(self, project_id: str, key: str, enabled: bool) -> dict:
        def _upd(p: dict):
            if key in {"enable_subtitles", "enable_voiceover"}:
                p[key] = bool(enabled)
            elif key in p and isinstance(p[key], dict):
                p[key]["enabled"] = bool(enabled)
        return self._update_project(project_id, _upd)
