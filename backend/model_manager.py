"""
Model Manager Module
Handles loading, downloading, and management of voice conversion models
"""

import os
import json
import logging
import asyncio
import aiohttp
import aiofiles
from typing import Dict, List, Optional, Any
from pathlib import Path
import hashlib
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    """Configuration for a voice conversion model"""
    id: str
    name: str
    description: str
    language: str
    gender: str
    size_mb: float
    download_url: Optional[str]
    local_path: Optional[str]
    checksum: Optional[str]
    version: str
    available: bool = False

class ModelManager:
    """Manages voice conversion models"""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.loaded_models: Dict[str, Any] = {}
        self.model_configs: Dict[str, ModelConfig] = {}
        self.config_file = self.models_dir / "models_config.json"
        
    async def initialize(self):
        """Initialize the model manager"""
        logger.info("Initializing model manager...")
        await self._load_model_configs()
        await self._scan_local_models()
        
    async def _load_model_configs(self):
        """Load model configurations"""
        # Default model configurations
        default_configs = [
            ModelConfig(
                id="seed-vc-base",
                name="Seed-VC Base",
                description="High-quality general purpose voice conversion model",
                language="Multi",
                gender="Neutral",
                size_mb=150.5,
                download_url="https://huggingface.co/Plachta/Seed-VC/resolve/main/seed-vc-base.onnx",
                local_path=None,
                checksum="abc123def456",
                version="1.0.0"
            ),
            ModelConfig(
                id="seed-vc-fast",
                name="Seed-VC Fast",
                description="CPU-optimized model for faster processing with good quality",
                language="Multi",
                gender="Neutral",
                size_mb=85.2,
                download_url="https://huggingface.co/Plachta/Seed-VC/resolve/main/seed-vc-fast.onnx",
                local_path=None,
                checksum="def456ghi789",
                version="1.0.0"
            ),
            ModelConfig(
                id="seed-vc-hifi",
                name="Seed-VC Hi-Fi",
                description="High fidelity model with best quality (slower processing)",
                language="Multi",
                gender="Neutral",
                size_mb=280.8,
                download_url="https://huggingface.co/Plachta/Seed-VC/resolve/main/seed-vc-hifi.onnx",
                local_path=None,
                checksum="ghi789jkl012",
                version="1.0.0"
            )
        ]
        
        # Load from config file if exists
        if self.config_file.exists():
            try:
                async with aiofiles.open(self.config_file, 'r') as f:
                    content = await f.read()
                    config_data = json.loads(content)
                    
                for config_dict in config_data:
                    config = ModelConfig(**config_dict)
                    self.model_configs[config.id] = config
                    
            except Exception as e:
                logger.warning(f"Failed to load model config: {e}")
                # Use default configs
                for config in default_configs:
                    self.model_configs[config.id] = config
        else:
            # Use default configs and save them
            for config in default_configs:
                self.model_configs[config.id] = config
            await self._save_model_configs()
    
    async def _save_model_configs(self):
        """Save model configurations to file"""
        try:
            config_data = []
            for config in self.model_configs.values():
                config_dict = {
                    "id": config.id,
                    "name": config.name,
                    "description": config.description,
                    "language": config.language,
                    "gender": config.gender,
                    "size_mb": config.size_mb,
                    "download_url": config.download_url,
                    "local_path": config.local_path,
                    "checksum": config.checksum,
                    "version": config.version,
                    "available": config.available
                }
                config_data.append(config_dict)
            
            async with aiofiles.open(self.config_file, 'w') as f:
                await f.write(json.dumps(config_data, indent=2))
                
        except Exception as e:
            logger.error(f"Failed to save model configs: {e}")
    
    async def _scan_local_models(self):
        """Scan for locally available models"""
        logger.info("Scanning for local models...")
        
        for model_id, config in self.model_configs.items():
            model_path = self.models_dir / f"{model_id}.onnx"
            
            if model_path.exists():
                # Verify checksum if available
                if config.checksum:
                    file_checksum = await self._calculate_checksum(model_path)
                    if file_checksum == config.checksum:
                        config.available = True
                        config.local_path = str(model_path)
                        logger.info(f"Model {model_id} found and verified")
                    else:
                        logger.warning(f"Model {model_id} checksum mismatch")
                else:
                    # No checksum available, assume it's valid
                    config.available = True
                    config.local_path = str(model_path)
                    logger.info(f"Model {model_id} found (no checksum verification)")
    
    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        async with aiofiles.open(file_path, "rb") as f:
            async for chunk in f:
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()[:12]  # First 12 characters
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        models = []
        for config in self.model_configs.values():
            model_info = {
                "id": config.id,
                "name": config.name,
                "description": config.description,
                "language": config.language,
                "gender": config.gender,
                "available": config.available,
                "size_mb": config.size_mb,
                "download_url": config.download_url if not config.available else None
            }
            models.append(model_info)
        
        return models
    
    async def download_model(self, model_id: str, progress_callback=None):
        """Download a model from remote source"""
        if model_id not in self.model_configs:
            raise ValueError(f"Model {model_id} not found in configurations")
        
        config = self.model_configs[model_id]
        
        if not config.download_url:
            raise ValueError(f"No download URL available for model {model_id}")
        
        if config.available:
            logger.info(f"Model {model_id} already available locally")
            return
        
        logger.info(f"Starting download of model {model_id}")
        
        model_path = self.models_dir / f"{model_id}.onnx"
        temp_path = self.models_dir / f"{model_id}.onnx.tmp"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(config.download_url) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to download model: HTTP {response.status}")
                    
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    async with aiofiles.open(temp_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            if progress_callback and total_size > 0:
                                progress = (downloaded / total_size) * 100
                                await progress_callback(progress)
            
            # Verify checksum if available
            if config.checksum:
                file_checksum = await self._calculate_checksum(temp_path)
                if file_checksum != config.checksum:
                    raise Exception(f"Checksum verification failed for {model_id}")
            
            # Move temp file to final location
            temp_path.rename(model_path)
            
            # Update config
            config.available = True
            config.local_path = str(model_path)
            
            await self._save_model_configs()
            
            logger.info(f"Model {model_id} downloaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to download model {model_id}: {e}")
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
            raise
    
    async def load_model(self, model_id: str) -> Any:
        """Load a model into memory"""
        if model_id in self.loaded_models:
            return self.loaded_models[model_id]
        
        if model_id not in self.model_configs:
            raise ValueError(f"Model {model_id} not found")
        
        config = self.model_configs[model_id]
        
        if not config.available or not config.local_path:
            raise ValueError(f"Model {model_id} not available locally")
        
        logger.info(f"Loading model {model_id}")
        
        try:
            # Simulate model loading (replace with actual ONNX loading)
            await asyncio.sleep(1.0)  # Simulate loading time
            
            # In a real implementation, you would load the ONNX model here:
            # import onnxruntime as ort
            # session = ort.InferenceSession(config.local_path, providers=['CPUExecutionProvider'])
            # self.loaded_models[model_id] = session
            
            # For now, store a mock model
            mock_model = {
                "id": model_id,
                "config": config,
                "loaded": True,
                "providers": ["CPUExecutionProvider"]
            }
            
            self.loaded_models[model_id] = mock_model
            logger.info(f"Model {model_id} loaded successfully")
            
            return mock_model
            
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            raise
    
    async def unload_model(self, model_id: str):
        """Unload a model from memory"""
        if model_id in self.loaded_models:
            del self.loaded_models[model_id]
            logger.info(f"Model {model_id} unloaded")
    
    async def ensure_model_loaded(self, model_id: str):
        """Ensure a model is loaded, download if necessary"""
        if model_id not in self.model_configs:
            raise ValueError(f"Model {model_id} not found")
        
        config = self.model_configs[model_id]
        
        # Download if not available
        if not config.available:
            await self.download_model(model_id)
        
        # Load if not loaded
        if model_id not in self.loaded_models:
            await self.load_model(model_id)
    
    async def load_default_models(self):
        """Load default models that are available locally"""
        logger.info("Loading default models...")
        
        # Try to load the fast model first (smallest, most likely to be available)
        priority_models = ["seed-vc-fast", "seed-vc-base"]
        
        for model_id in priority_models:
            if model_id in self.model_configs and self.model_configs[model_id].available:
                try:
                    await self.load_model(model_id)
                    break
                except Exception as e:
                    logger.warning(f"Failed to load default model {model_id}: {e}")
    
    def get_model(self, model_id: str) -> Optional[Any]:
        """Get a loaded model"""
        return self.loaded_models.get(model_id)
    
    def is_model_loaded(self, model_id: str) -> bool:
        """Check if a model is loaded"""
        return model_id in self.loaded_models
    
    def is_model_available(self, model_id: str) -> bool:
        """Check if a model is available locally"""
        if model_id not in self.model_configs:
            return False
        return self.model_configs[model_id].available
    
    async def cleanup(self):
        """Clean up loaded models"""
        logger.info("Cleaning up model manager...")
        self.loaded_models.clear()