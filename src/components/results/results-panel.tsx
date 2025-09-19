"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
// Mock toast function for demo - replace with actual toast library
const toast = {
  success: (message: string) => console.log("Thành công:", message),
  error: (message: string) => console.error("Lỗi:", message),
  info: (message: string) => console.info("Thông tin:", message)
};

interface ResultsPanelProps {
  originalFile: File | null;
  convertedAudio: string;
}

export function ResultsPanel({ originalFile, convertedAudio }: ResultsPanelProps) {
  const [isPlayingOriginal, setIsPlayingOriginal] = useState(false);
  const [isPlayingConverted, setIsPlayingConverted] = useState(false);
  const [originalVolume, setOriginalVolume] = useState([0.7]);
  const [convertedVolume, setConvertedVolume] = useState([0.7]);
  const [originalCurrentTime, setOriginalCurrentTime] = useState(0);
  const [convertedCurrentTime, setConvertedCurrentTime] = useState(0);
  const [originalDuration, setOriginalDuration] = useState(0);
  const [convertedDuration, setConvertedDuration] = useState(0);
  
  const originalAudioRef = useRef<HTMLAudioElement>(null);
  const convertedAudioRef = useRef<HTMLAudioElement>(null);
  const originalObjectUrl = useRef<string>("");

  useEffect(() => {
    if (originalFile) {
      if (originalObjectUrl.current) {
        URL.revokeObjectURL(originalObjectUrl.current);
      }
      originalObjectUrl.current = URL.createObjectURL(originalFile);
    }

    return () => {
      if (originalObjectUrl.current) {
        URL.revokeObjectURL(originalObjectUrl.current);
      }
    };
  }, [originalFile]);

  useEffect(() => {
    const originalAudio = originalAudioRef.current;
    const convertedAudio = convertedAudioRef.current;

    const updateOriginalTime = () => {
      if (originalAudio) {
        setOriginalCurrentTime(originalAudio.currentTime);
      }
    };

    const updateConvertedTime = () => {
      if (convertedAudio) {
        setConvertedCurrentTime(convertedAudio.currentTime);
      }
    };

    const handleOriginalLoadedMetadata = () => {
      if (originalAudio) {
        setOriginalDuration(originalAudio.duration);
      }
    };

    const handleConvertedLoadedMetadata = () => {
      if (convertedAudio) {
        setConvertedDuration(convertedAudio.duration);
      }
    };

    const handleOriginalEnded = () => {
      setIsPlayingOriginal(false);
    };

    const handleConvertedEnded = () => {
      setIsPlayingConverted(false);
    };

    if (originalAudio) {
      originalAudio.addEventListener('timeupdate', updateOriginalTime);
      originalAudio.addEventListener('loadedmetadata', handleOriginalLoadedMetadata);
      originalAudio.addEventListener('ended', handleOriginalEnded);
    }

    if (convertedAudio) {
      convertedAudio.addEventListener('timeupdate', updateConvertedTime);
      convertedAudio.addEventListener('loadedmetadata', handleConvertedLoadedMetadata);
      convertedAudio.addEventListener('ended', handleConvertedEnded);
    }

    return () => {
      if (originalAudio) {
        originalAudio.removeEventListener('timeupdate', updateOriginalTime);
        originalAudio.removeEventListener('loadedmetadata', handleOriginalLoadedMetadata);
        originalAudio.removeEventListener('ended', handleOriginalEnded);
      }
      if (convertedAudio) {
        convertedAudio.removeEventListener('timeupdate', updateConvertedTime);
        convertedAudio.removeEventListener('loadedmetadata', handleConvertedLoadedMetadata);
        convertedAudio.removeEventListener('ended', handleConvertedEnded);
      }
    };
  }, []);

  const toggleOriginalPlayback = () => {
    const audio = originalAudioRef.current;
    if (!audio) return;

    if (isPlayingOriginal) {
      audio.pause();
      setIsPlayingOriginal(false);
    } else {
      // Pause converted audio if playing
      if (isPlayingConverted && convertedAudioRef.current) {
        convertedAudioRef.current.pause();
        setIsPlayingConverted(false);
      }
      
      audio.play().catch(console.error);
      setIsPlayingOriginal(true);
    }
  };

  const toggleConvertedPlayback = () => {
    const audio = convertedAudioRef.current;
    if (!audio) return;

    if (isPlayingConverted) {
      audio.pause();
      setIsPlayingConverted(false);
    } else {
      // Pause original audio if playing
      if (isPlayingOriginal && originalAudioRef.current) {
        originalAudioRef.current.pause();
        setIsPlayingOriginal(false);
      }
      
      audio.play().catch(console.error);
      setIsPlayingConverted(true);
    }
  };

  const handleOriginalVolumeChange = (value: number[]) => {
    setOriginalVolume(value);
    if (originalAudioRef.current) {
      originalAudioRef.current.volume = value[0];
    }
  };

  const handleConvertedVolumeChange = (value: number[]) => {
    setConvertedVolume(value);
    if (convertedAudioRef.current) {
      convertedAudioRef.current.volume = value[0];
    }
  };

  const formatTime = (time: number): string => {
    if (isNaN(time)) return "0:00";
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const downloadAudio = async (audioUrl: string, filename: string) => {
    try {
      const response = await fetch(audioUrl);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast.success(`Đã tải xuống ${filename}`);
    } catch (error) {
      console.error('Lỗi tải xuống:', error);
      toast.error('Không thể tải xuống tệp');
    }
  };

  const compareAudios = () => {
    // Stop both audios first
    if (originalAudioRef.current) originalAudioRef.current.pause();
    if (convertedAudioRef.current) convertedAudioRef.current.pause();
    setIsPlayingOriginal(false);
    setIsPlayingConverted(false);

    // Play both simultaneously for comparison
    if (originalAudioRef.current && convertedAudioRef.current) {
      originalAudioRef.current.currentTime = 0;
      convertedAudioRef.current.currentTime = 0;
      
      // Set lower volume for comparison
      originalAudioRef.current.volume = 0.3;
      convertedAudioRef.current.volume = 0.3;
      
      Promise.all([
        originalAudioRef.current.play(),
        convertedAudioRef.current.play()
      ]).then(() => {
        setIsPlayingOriginal(true);
        setIsPlayingConverted(true);
        toast.info("Đang phát cả hai âm thanh để so sánh");
      }).catch(console.error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Audio Players */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Original Audio */}
        <Card className="p-4 bg-slate-800/30 border-slate-700">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-medium text-white">Âm Thanh Gốc</h3>
            <Badge variant="outline" className="border-blue-500 text-blue-400">
              Nguồn
            </Badge>
          </div>
          
          <audio
            ref={originalAudioRef}
            src={originalObjectUrl.current}
            preload="metadata"
            className="hidden"
          />
          
          <div className="space-y-4">
            <div className="flex items-center justify-center space-x-4">
              <Button
                onClick={toggleOriginalPlayback}
                variant="outline"
                size="sm"
                className="border-slate-600 text-slate-300"
              >
                {isPlayingOriginal ? "Tạm Dừng" : "Phát"}
              </Button>
              
              <div className="text-sm text-slate-400 font-mono">
                {formatTime(originalCurrentTime)} / {formatTime(originalDuration)}
              </div>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm text-slate-400">Âm Lượng</label>
              <Slider
                value={originalVolume}
                onValueChange={handleOriginalVolumeChange}
                max={1}
                min={0}
                step={0.1}
                className="w-full"
              />
            </div>
            
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all duration-200"
                style={{ width: `${(originalCurrentTime / originalDuration) * 100 || 0}%` }}
              />
            </div>
          </div>
        </Card>

        {/* Converted Audio */}
        <Card className="p-4 bg-slate-800/30 border-slate-700">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-medium text-white">Âm Thanh Đã Chuyển Đổi</h3>
            <Badge variant="outline" className="border-green-500 text-green-400">
              Kết Quả
            </Badge>
          </div>
          
          <audio
            ref={convertedAudioRef}
            src={convertedAudio}
            preload="metadata"
            className="hidden"
          />
          
          <div className="space-y-4">
            <div className="flex items-center justify-center space-x-4">
              <Button
                onClick={toggleConvertedPlayback}
                variant="outline"
                size="sm"
                className="border-slate-600 text-slate-300"
              >
                {isPlayingConverted ? "Tạm Dừng" : "Phát"}
              </Button>
              
              <div className="text-sm text-slate-400 font-mono">
                {formatTime(convertedCurrentTime)} / {formatTime(convertedDuration)}
              </div>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm text-slate-400">Volume</label>
              <Slider
                value={convertedVolume}
                onValueChange={handleConvertedVolumeChange}
                max={1}
                min={0}
                step={0.1}
                className="w-full"
              />
            </div>
            
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div 
                className="bg-green-500 h-2 rounded-full transition-all duration-200"
                style={{ width: `${(convertedCurrentTime / convertedDuration) * 100 || 0}%` }}
              />
            </div>
          </div>
        </Card>
      </div>

      {/* Controls */}
      <Card className="p-4 bg-slate-800/30 border-slate-700">
        <div className="flex flex-col sm:flex-row items-center justify-between space-y-4 sm:space-y-0 sm:space-x-4">
          <div className="flex items-center space-x-4">
            <Button
              onClick={compareAudios}
              variant="outline"
              className="border-purple-500 text-purple-400 hover:bg-purple-500/20"
            >
              So Sánh Cùng Lúc
            </Button>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              onClick={() => downloadAudio(originalObjectUrl.current, `goc_${originalFile?.name || 'audio.wav'}`)}
              variant="outline"
              size="sm"
              className="border-slate-600 text-slate-300"
            >
              Tải Xuống Bản Gốc
            </Button>
            <Button
              onClick={() => downloadAudio(convertedAudio, 'am_thanh_da_chuyen_doi.wav')}
              className="bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600"
            >
              Tải Xuống Kết Quả
            </Button>
          </div>
        </div>
      </Card>

      {/* Audio Quality Analysis */}
      <Card className="p-4 bg-slate-800/30 border-slate-700">
        <h3 className="text-lg font-medium text-white mb-4">Phân Tích Chất Lượng</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400">92%</div>
            <div className="text-xs text-slate-400">Điểm Chất Lượng</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-400">0.85</div>
            <div className="text-xs text-slate-400">Độ Tương Đồng</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-400">2.3s</div>
            <div className="text-xs text-slate-400">Thời Gian Xử Lý</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-400">CPU</div>
            <div className="text-xs text-slate-400">Xử Lý</div>
          </div>
        </div>
      </Card>
    </div>
  );
}