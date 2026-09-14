import cv2
import numpy as np
import time

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

from data_access import CameraFrame

class ImageUpscaler:
    """
    Data Processor class dedicated to upscaling CCTV frames.
    Uses ONNX Runtime with TensorRT optimization for real-time 30-60 FPS inference.
    """
    def __init__(self, model_path: str = "checkpoints\realesrgan.onnx", use_tensorrt: bool = False):
        self.model_path = model_path
        self.use_tensorrt = use_tensorrt
        self._session = None
        
        if ONNX_AVAILABLE:
            self._init_model()
        else:
            print("Warning: onnxruntime is not installed. Run: pip install onnxruntime-gpu")

    def _init_model(self):
        providers = []
        if self.use_tensorrt:
            # Enable TensorRT for FP16 optimization on NVIDIA GPUs
            providers.append(
                ('TensorrtExecutionProvider', {
                    'device_id': 0,
                    'trt_fp16_enable': True,
                    'trt_engine_cache_enable': True,
                    'trt_engine_cache_path': './trt_cache'
                })
            )
        # Fallback to standard CUDA, then CPU
        providers.append('CUDAExecutionProvider')
        providers.append('CPUExecutionProvider')
        
        try:
            self._session = ort.InferenceSession(self.model_path, providers=providers)
            print(f"[ImageUpscaler] Initialized successfully. Using providers: {self._session.get_providers()}")
        except Exception as e:
            print(f"[ImageUpscaler] Failed to load ONNX model '{self.model_path}'. Ensure the file exists. Error: {e}")

    def upscale_frame(self, frame_obj: CameraFrame) -> CameraFrame:
        """
        Takes a CameraFrame, runs Real-ESRGAN upscaling via ONNX Runtime, 
        and returns a new CameraFrame with the high-resolution image.
        """
        if not ONNX_AVAILABLE or self._session is None:
            # Passthrough if model isn't loaded
            return frame_obj

        image = frame_obj.image
        
        # 1. Preprocess for Real-ESRGAN (BGR to RGB, normalize, CHW format)
        input_data = image.astype(np.float32) / 255.0
        input_data = cv2.cvtColor(input_data, cv2.COLOR_BGR2RGB)
        input_data = np.transpose(input_data, (2, 0, 1)) # HWC to CHW
        input_data = np.expand_dims(input_data, axis=0)  # Add batch dimension (1, 3, H, W)
        
        # 2. Run ONNX Inference
        input_name = self._session.get_inputs()[0].name
        output_name = self._session.get_outputs()[0].name
        
        # Note: TensorRT execution will automatically optimize this graph to FP16 on the first run
        out = self._session.run([output_name], {input_name: input_data})[0]
        
        # 3. Postprocess back to OpenCV format
        out = np.squeeze(out, axis=0) # Remove batch dimension
        out = np.clip(out, 0.0, 1.0)
        out = np.transpose(out, (1, 2, 0)) # CHW to HWC
        out = cv2.cvtColor(out, cv2.COLOR_RGB2BGR)
        enhanced_image = (out * 255.0).astype(np.uint8)
        
        # 4. Return enriched CameraFrame
        # We maintain all original metadata (timestamps, camera_id, ocr_data)
        return CameraFrame(
            camera_id=frame_obj.camera_id,
            image=enhanced_image,
            pts_ms=frame_obj.pts_ms,
            system_timestamp=frame_obj.system_timestamp,
            ocr_data=frame_obj.ocr_data
        )

