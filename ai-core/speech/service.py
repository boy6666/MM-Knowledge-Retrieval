"""
语音服务
- 语音转文字: Sherpa-ONNX (本地)
- 文字转语音: Edge-TTS (云端免费)
"""
import asyncio
from pathlib import Path


class SpeechRecognizer:
    """语音转文字 (Sherpa-ONNX)"""

    def __init__(self, model_dir: str = "tools/sherpa-onnx"):
        self._recognizer = None
        self._model_dir = Path(model_dir)

    @property
    def recognizer(self):
        if self._recognizer is None:
            try:
                import sherpa_onnx
                # 需要模型文件: encoder, decoder, joiner, tokens
                encoder = str(self._model_dir / "encoder.onnx")
                decoder = str(self._model_dir / "decoder.onnx")
                joiner = str(self._model_dir / "joiner.onnx")
                tokens = str(self._model_dir / "tokens.txt")

                if not all(Path(f).exists() for f in [encoder, decoder, joiner, tokens]):
                    raise FileNotFoundError(
                        "Sherpa-ONNX 模型文件不完整。"
                        "下载: https://github.com/k2-fsa/sherpa-onnx/releases"
                    )

                self._recognizer = sherpa_onnx.OfflineRecognizer.from_files(
                    encoder=encoder,
                    decoder=decoder,
                    joiner=joiner,
                    tokens=tokens,
                    num_threads=2,
                )
            except ImportError:
                raise ImportError(
                    "请安装 sherpa-onnx: pip install sherpa-onnx\n"
                    "或从 https://github.com/k2-fsa/sherpa-onnx/releases 下载预编译包"
                )
        return self._recognizer

    def transcribe(self, audio_path: str) -> str:
        """音频文件 → 文字"""
        import wave
        import numpy as np

        with wave.open(audio_path, "rb") as f:
            frames = f.readframes(f.getnframes())
            samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768

        stream = self.recognizer.create_stream()
        stream.accept_waveform(16000, samples)
        stream.input_finished()
        self.recognizer.decode_stream(stream)
        return stream.result.text.strip()

    @property
    def is_ready(self) -> bool:
        try:
            return self.recognizer is not None
        except Exception:
            return False


class TextToSpeech:
    """文字转语音 (Edge-TTS, 免费)"""

    async def speak(self, text: str, lang: str = "zh-CN") -> bytes:
        """文字 → 语音音频数据"""
        import edge_tts
        communicate = edge_tts.Communicate(text, voice=f"{lang}-XiaoxiaoNeural")
        audio_chunks = []
        async for chunk in communicate.stream:
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])
        return b"".join(audio_chunks)

    async def speak_to_file(self, text: str, output_path: str):
        """文字 → 语音文件"""
        import edge_tts
        communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
        await communicate.save(output_path)

    def speak_sync(self, text: str, output_path: str):
        """同步版 (用于非 async 环境)"""
        asyncio.run(self.speak_to_file(text, output_path))


stt = SpeechRecognizer()
tts = TextToSpeech()
