"use client";

import { useState, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Card } from "@/components/ui/card";
// Mock toast function for demo - replace with actual toast library
const toast = {
  success: (message: string) => console.log("Thành công:", message),
  error: (message: string) => console.error("Lỗi:", message),
  info: (message: string) => console.info("Thông tin:", message)
};

interface AudioUploaderProps {
  onFileUpload: (file: File) => void;
}

export function AudioUploader({ onFileUpload }: AudioUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const acceptedFormats = ["audio/wav", "audio/mp3", "audio/mpeg", "audio/flac", "audio/m4a"];
  const maxFileSize = 100 * 1024 * 1024; // 100MB

  const validateFile = (file: File): boolean => {
    if (!acceptedFormats.includes(file.type) && !file.name.match(/\.(wav|mp3|flac|m4a)$/i)) {
      toast.error("Vui lòng tải lên tệp âm thanh hợp lệ (WAV, MP3, FLAC, hoặc M4A)");
      return false;
    }

    if (file.size > maxFileSize) {
      toast.error("Kích thước tệp phải nhỏ hơn 100MB");
      return false;
    }

    return true;
  };

  const handleFileSelect = useCallback((file: File) => {
    if (validateFile(file)) {
      setSelectedFile(file);
      
      // Simulate upload progress
      let progress = 0;
      const interval = setInterval(() => {
        progress += 10;
        setUploadProgress(progress);
        
        if (progress >= 100) {
          clearInterval(interval);
          onFileUpload(file);
          toast.success("Tệp âm thanh đã được tải lên thành công!");
        }
      }, 100);
    }
  }, [onFileUpload]);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragOut = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files[0]) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      const audioChunks: Blob[] = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        const audioFile = new File([audioBlob], 'recorded-audio.wav', { type: 'audio/wav' });
        handleFileSelect(audioFile);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      // Start timer
      intervalRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

      toast.success("Đã bắt đầu ghi âm");
    } catch (error) {
      toast.error("Không thể truy cập microphone");
      console.error("Lỗi ghi âm:", error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      
      toast.success("Đã dừng ghi âm");
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-4">
      {/* File Upload Area */}
      <Card
        className={`border-2 border-dashed transition-all duration-200 ${
          isDragging
            ? 'border-purple-500 bg-purple-500/10'
            : 'border-slate-600 hover:border-slate-500 bg-slate-800/30'
        }`}
        onDragEnter={handleDragIn}
        onDragLeave={handleDragOut}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <div className="p-8 text-center">
          <div className="mx-auto w-12 h-12 rounded-full bg-slate-700 flex items-center justify-center mb-4">
            <svg className="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          
          <h3 className="text-lg font-medium text-white mb-2">Tải Lên Tệp Âm Thanh</h3>
          <p className="text-slate-400 mb-4">
            Kéo và thả tệp âm thanh vào đây, hoặc nhấn để chọn tệp
          </p>
          
          <Button
            onClick={() => fileInputRef.current?.click()}
            variant="outline"
            className="border-slate-600 text-slate-300 hover:bg-slate-700"
          >
            Chọn Tệp
          </Button>
          
          <input
            ref={fileInputRef}
            type="file"
            accept=".wav,.mp3,.flac,.m4a"
            onChange={handleFileInputChange}
            className="hidden"
          />
          
          <p className="text-xs text-slate-500 mt-4">
            Định dạng hỗ trợ: WAV, MP3, FLAC, M4A (Tối đa 100MB)
          </p>
        </div>
      </Card>

      {/* Recording Section */}
      <Card className="p-6 bg-slate-800/30 border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-white">Ghi Âm</h3>
          {isRecording && (
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
              <span className="text-red-400 font-mono">{formatTime(recordingTime)}</span>
            </div>
          )}
        </div>
        
        <div className="flex items-center space-x-4">
          {!isRecording ? (
            <Button onClick={startRecording} className="bg-red-500 hover:bg-red-600">
              Bắt Đầu Ghi
            </Button>
          ) : (
            <Button onClick={stopRecording} variant="outline" className="border-red-500 text-red-400">
              Dừng Ghi
            </Button>
          )}
          
          <p className="text-sm text-slate-400">
            Nhấn để ghi âm trực tiếp từ microphone của bạn
          </p>
        </div>
      </Card>

      {/* Upload Progress */}
      {uploadProgress > 0 && uploadProgress < 100 && (
        <Card className="p-4 bg-slate-800/30 border-slate-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-white">Đang tải lên...</span>
            <span className="text-sm text-slate-400">{uploadProgress}%</span>
          </div>
          <Progress value={uploadProgress} className="w-full" />
        </Card>
      )}

      {/* Selected File Info */}
      {selectedFile && uploadProgress >= 100 && (
        <Card className="p-4 bg-slate-800/30 border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-white">{selectedFile.name}</p>
              <p className="text-xs text-slate-400">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB • {selectedFile.type}
              </p>
            </div>
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
          </div>
        </Card>
      )}
    </div>
  );
}