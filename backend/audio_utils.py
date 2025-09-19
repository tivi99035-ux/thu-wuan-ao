"""
Audio Processing Utilities
CPU-optimized audio preprocessing and postprocessing
"""

import numpy as np
import soundfile as sf
import librosa
import asyncio
import logging
from typing import Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class AudioProcessor:
    """CPU-optimized audio processing utilities"""
    
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.hop_length = 256
        self.win_length = 1024
        self.n_fft = 1024
        
    async def preprocess(
        self,
        input_path: str,
        target_sr: Optional[int] = None,
        normalize: bool = True,
        noise_reduction: float = 0.3
    ) -> np.ndarray:
        """
        Preprocess audio file for voice conversion
        
        Args:
            input_path: Path to input audio file
            target_sr: Target sample rate (defaults to self.sample_rate)
            normalize: Whether to normalize audio
            noise_reduction: Noise reduction strength (0.0 to 1.0)
            
        Returns:
            Preprocessed audio data
        """
        try:
            logger.info(f"Preprocessing audio: {input_path}")
            
            if target_sr is None:
                target_sr = self.sample_rate
            
            # Load audio file
            audio, sr = await self._load_audio_async(input_path)
            
            # Resample if necessary
            if sr != target_sr:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
                sr = target_sr
            
            # Convert to mono if stereo
            if len(audio.shape) > 1:
                audio = librosa.to_mono(audio)
            
            # Apply noise reduction
            if noise_reduction > 0:
                audio = await self._reduce_noise(audio, sr, strength=noise_reduction)
            
            # Normalize audio
            if normalize:
                audio = self._normalize_audio(audio)
            
            # Trim silence
            audio = self._trim_silence(audio, sr)
            
            logger.info(f"Audio preprocessed: {len(audio)} samples at {sr}Hz")
            return audio
            
        except Exception as e:
            logger.error(f"Audio preprocessing failed: {e}")
            raise
    
    async def _load_audio_async(self, file_path: str) -> Tuple[np.ndarray, int]:
        """Load audio file asynchronously"""
        def load_audio():
            return sf.read(file_path)
        
        # Run in thread to avoid blocking
        loop = asyncio.get_event_loop()
        audio, sr = await loop.run_in_executor(None, load_audio)
        
        return audio.astype(np.float32), sr
    
    async def _reduce_noise(
        self, 
        audio: np.ndarray, 
        sr: int, 
        strength: float = 0.3
    ) -> np.ndarray:
        """Apply noise reduction to audio"""
        try:
            # Simple spectral subtraction for noise reduction
            # This is a basic implementation - replace with more sophisticated methods
            
            # Compute STFT
            stft = librosa.stft(audio, n_fft=self.n_fft, hop_length=self.hop_length)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Estimate noise floor from first few frames
            noise_frames = min(10, magnitude.shape[1] // 10)
            noise_floor = np.mean(magnitude[:, :noise_frames], axis=1, keepdims=True)
            
            # Apply spectral subtraction
            alpha = strength * 2  # Noise reduction factor
            enhanced_magnitude = magnitude - alpha * noise_floor
            
            # Ensure non-negative values
            enhanced_magnitude = np.maximum(enhanced_magnitude, 0.1 * magnitude)
            
            # Reconstruct audio
            enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
            enhanced_audio = librosa.istft(
                enhanced_stft, 
                hop_length=self.hop_length, 
                length=len(audio)
            )
            
            return enhanced_audio.astype(np.float32)
            
        except Exception as e:
            logger.warning(f"Noise reduction failed, using original audio: {e}")
            return audio
    
    def _normalize_audio(self, audio: np.ndarray, target_db: float = -20.0) -> np.ndarray:
        """Normalize audio to target RMS level"""
        # Calculate current RMS
        rms = np.sqrt(np.mean(audio**2))
        
        if rms > 0:
            # Convert target dB to linear scale
            target_rms = 10**(target_db / 20.0)
            
            # Apply gain
            gain = target_rms / rms
            normalized_audio = audio * gain
            
            # Prevent clipping
            max_val = np.max(np.abs(normalized_audio))
            if max_val > 0.95:
                normalized_audio = normalized_audio * 0.95 / max_val
            
            return normalized_audio
        
        return audio
    
    def _trim_silence(
        self, 
        audio: np.ndarray, 
        sr: int, 
        threshold_db: float = -40.0
    ) -> np.ndarray:
        """Trim silence from beginning and end of audio"""
        try:
            # Use librosa to trim silence
            trimmed_audio, _ = librosa.effects.trim(
                audio, 
                top_db=-threshold_db,
                frame_length=2048,
                hop_length=512
            )
            
            # Ensure minimum length
            min_length = int(0.1 * sr)  # 100ms minimum
            if len(trimmed_audio) < min_length:
                return audio
            
            return trimmed_audio
            
        except Exception as e:
            logger.warning(f"Silence trimming failed: {e}")
            return audio
    
    async def postprocess(
        self,
        audio: np.ndarray,
        sr: int,
        enhance_quality: bool = True,
        apply_compressor: bool = True
    ) -> np.ndarray:
        """
        Postprocess converted audio
        
        Args:
            audio: Audio data to postprocess
            sr: Sample rate
            enhance_quality: Whether to apply quality enhancement
            apply_compressor: Whether to apply dynamic range compression
            
        Returns:
            Postprocessed audio data
        """
        try:
            logger.info("Postprocessing converted audio")
            
            processed_audio = audio.copy()
            
            # Apply quality enhancement
            if enhance_quality:
                processed_audio = await self._enhance_quality(processed_audio, sr)
            
            # Apply dynamic range compression
            if apply_compressor:
                processed_audio = self._apply_compressor(processed_audio)
            
            # Final normalization
            processed_audio = self._normalize_audio(processed_audio, target_db=-16.0)
            
            # Apply soft limiting to prevent clipping
            processed_audio = self._soft_limit(processed_audio)
            
            return processed_audio
            
        except Exception as e:
            logger.error(f"Audio postprocessing failed: {e}")
            return audio
    
    async def _enhance_quality(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Apply quality enhancement to audio"""
        try:
            # Apply harmonic enhancement
            enhanced_audio = self._enhance_harmonics(audio, sr)
            
            # Apply subtle high-frequency enhancement
            enhanced_audio = self._enhance_high_frequencies(enhanced_audio, sr)
            
            return enhanced_audio
            
        except Exception as e:
            logger.warning(f"Quality enhancement failed: {e}")
            return audio
    
    def _enhance_harmonics(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Enhance harmonic content"""
        # Simple harmonic enhancement using second-order harmonics
        try:
            # Generate harmonics
            harmonics = np.sign(audio) * (audio**2)
            
            # Mix with original audio
            enhanced_audio = 0.85 * audio + 0.15 * harmonics
            
            return enhanced_audio
            
        except Exception as e:
            logger.warning(f"Harmonic enhancement failed: {e}")
            return audio
    
    def _enhance_high_frequencies(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Apply subtle high-frequency enhancement"""
        try:
            # Apply high-shelf filter
            from scipy import signal
            
            # Design high-shelf filter
            freq = 4000  # 4kHz
            gain_db = 2.0  # 2dB boost
            
            # Convert to normalized frequency
            nyquist = sr / 2
            normalized_freq = freq / nyquist
            
            if normalized_freq < 1.0:
                # Design filter
                b, a = signal.iirfilter(
                    2, normalized_freq, 
                    btype='highpass', 
                    ftype='butter'
                )
                
                # Apply filter with gain
                filtered = signal.filtfilt(b, a, audio)
                gain_linear = 10**(gain_db / 20.0)
                
                # Mix with original
                enhanced_audio = audio + 0.1 * (gain_linear - 1) * filtered
                
                return enhanced_audio
            
        except Exception as e:
            logger.warning(f"High-frequency enhancement failed: {e}")
        
        return audio
    
    def _apply_compressor(
        self, 
        audio: np.ndarray, 
        threshold: float = -12.0,
        ratio: float = 4.0,
        attack_time: float = 0.003,
        release_time: float = 0.1
    ) -> np.ndarray:
        """Apply dynamic range compression"""
        try:
            # Simple feed-forward compressor
            threshold_linear = 10**(threshold / 20.0)
            
            # Calculate envelope
            envelope = np.abs(audio)
            
            # Smooth envelope (attack/release)
            sr = self.sample_rate
            attack_coeff = np.exp(-1.0 / (attack_time * sr))
            release_coeff = np.exp(-1.0 / (release_time * sr))
            
            smoothed_envelope = np.zeros_like(envelope)
            for i in range(1, len(envelope)):
                if envelope[i] > smoothed_envelope[i-1]:
                    # Attack
                    smoothed_envelope[i] = (
                        attack_coeff * smoothed_envelope[i-1] + 
                        (1 - attack_coeff) * envelope[i]
                    )
                else:
                    # Release
                    smoothed_envelope[i] = (
                        release_coeff * smoothed_envelope[i-1] + 
                        (1 - release_coeff) * envelope[i]
                    )
            
            # Calculate gain reduction
            gain_reduction = np.ones_like(smoothed_envelope)
            above_threshold = smoothed_envelope > threshold_linear
            
            if np.any(above_threshold):
                # Apply compression to signals above threshold
                compressed_level = (
                    threshold_linear * 
                    (smoothed_envelope[above_threshold] / threshold_linear)**(1/ratio)
                )
                gain_reduction[above_threshold] = compressed_level / smoothed_envelope[above_threshold]
            
            # Apply gain reduction
            compressed_audio = audio * gain_reduction
            
            return compressed_audio
            
        except Exception as e:
            logger.warning(f"Compression failed: {e}")
            return audio
    
    def _soft_limit(self, audio: np.ndarray, threshold: float = 0.95) -> np.ndarray:
        """Apply soft limiting to prevent clipping"""
        limited_audio = np.tanh(audio / threshold) * threshold
        return limited_audio
    
    async def save_audio(
        self, 
        audio: np.ndarray, 
        output_path: str, 
        sr: int = None,
        format: str = 'WAV'
    ) -> None:
        """Save audio to file"""
        try:
            if sr is None:
                sr = self.sample_rate
            
            # Ensure audio is in correct format
            audio = audio.astype(np.float32)
            
            # Ensure audio is not clipping
            max_val = np.max(np.abs(audio))
            if max_val > 1.0:
                audio = audio / max_val * 0.95
            
            # Save audio file
            def save_file():
                sf.write(output_path, audio, sr, format=format)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, save_file)
            
            logger.info(f"Audio saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save audio: {e}")
            raise
    
    def get_audio_info(self, audio: np.ndarray, sr: int) -> dict:
        """Get audio information and statistics"""
        info = {
            "duration": len(audio) / sr,
            "samples": len(audio),
            "sample_rate": sr,
            "rms": float(np.sqrt(np.mean(audio**2))),
            "peak": float(np.max(np.abs(audio))),
            "dynamic_range": float(np.max(audio) - np.min(audio)),
        }
        
        # Calculate frequency statistics using FFT
        fft = np.fft.fft(audio)
        freqs = np.fft.fftfreq(len(audio), 1/sr)
        magnitude = np.abs(fft[:len(fft)//2])
        
        # Find dominant frequency
        dominant_freq_idx = np.argmax(magnitude)
        info["dominant_frequency"] = float(freqs[dominant_freq_idx])
        
        # Calculate spectral centroid
        spectral_centroid = np.sum(freqs[:len(magnitude)] * magnitude) / np.sum(magnitude)
        info["spectral_centroid"] = float(spectral_centroid)
        
        return info