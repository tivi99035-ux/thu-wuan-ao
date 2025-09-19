"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
// Mock toast function for demo - replace with actual toast library
const toast = {
  success: (message: string) => console.log("Thành công:", message),
  error: (message: string) => console.error("Lỗi:", message),
  info: (message: string) => console.info("Thông tin:", message)
};

interface VoiceConverterProps {
  audioFile: File;
  isProcessing: boolean;
  onConversionStart: () => void;
  onConversionComplete: (result: string) => void;
  onConversionError: (error: string) => void;
}

interface VoiceModel {
  id: string;
  name: string;
  description: string;
  language: string;
  gender: string;
  available: boolean;
}

const availableModels: VoiceModel[] = [
  {
    id: "seed-vc-base",
    name: "Seed-VC Cơ Bản",
    description: "Chuyển đổi giọng nói chất lượng cao đa năng",
    language: "Đa ngôn ngữ",
    gender: "Trung tính",
    available: true
  },
  {
    id: "seed-vc-fast",
    name: "Seed-VC Nhanh",
    description: "Tối ưu CPU để xử lý nhanh hơn",
    language: "Đa ngôn ngữ",
    gender: "Trung tính",
    available: true
  },
  {
    id: "seed-vc-hifi",
    name: "Seed-VC Chất Lượng Cao",
    description: "Chuyển đổi giọng nói độ trung thực cao (chậm hơn)",
    language: "Đa ngôn ngữ",
    gender: "Trung tính",
    available: true
  }
];

export function VoiceConverter({
  audioFile,
  isProcessing,
  onConversionStart,
  onConversionComplete,
  onConversionError
}: VoiceConverterProps) {
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [targetSpeaker, setTargetSpeaker] = useState<string>("");
  const [conversionStrength, setConversionStrength] = useState([0.8]);
  const [preservePitch, setPreservePitch] = useState([0.5]);
  const [noiseReduction, setNoiseReduction] = useState([0.3]);
  const [conversionProgress, setConversionProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");

  const targetSpeakers = [
    { id: "speaker_001", name: "Giọng Nam A", type: "Nam", quality: "Cao" },
    { id: "speaker_002", name: "Giọng Nữ A", type: "Nữ", quality: "Cao" },
    { id: "speaker_003", name: "Giọng Nam B", type: "Nam", quality: "Trung Bình" },
    { id: "speaker_004", name: "Giọng Nữ B", type: "Nữ", quality: "Trung Bình" },
    { id: "custom", name: "Giọng Tùy Chỉnh", type: "Tùy Chỉnh", quality: "Biến Đổi" }
  ];

  useEffect(() => {
    if (!selectedModel && availableModels.length > 0) {
      setSelectedModel(availableModels[0].id);
    }
  }, [selectedModel]);

  const simulateConversion = async () => {
    const steps = [
      { message: "Đang khởi tạo quy trình chuyển đổi...", progress: 10 },
      { message: "Đang tải mô hình giọng nói...", progress: 25 },
      { message: "Đang tiền xử lý âm thanh...", progress: 40 },
      { message: "Đang trích xuất đặc trưng giọng nói...", progress: 55 },
      { message: "Đang chuyển đổi đặc điểm giọng nói...", progress: 70 },
      { message: "Đang áp dụng hậu xử lý...", progress: 85 },
      { message: "Đang hoàn thiện kết quả...", progress: 100 }
    ];

    for (const step of steps) {
      setStatusMessage(step.message);
      setConversionProgress(step.progress);
      await new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 400));
    }

    // Simulate successful conversion with a blob URL
    const mockAudioUrl = URL.createObjectURL(audioFile);
    onConversionComplete(mockAudioUrl);
  };

  const handleStartConversion = async () => {
    if (!selectedModel) {
      toast.error("Vui lòng chọn mô hình giọng nói");
      return;
    }

    if (!targetSpeaker) {
      toast.error("Vui lòng chọn giọng nói đích");
      return;
    }

    onConversionStart();
    setConversionProgress(0);
    setStatusMessage("Bắt đầu chuyển đổi...");

    try {
      await simulateConversion();
      toast.success("Chuyển đổi giọng nói hoàn thành thành công!");
    } catch (error) {
      console.error("Lỗi chuyển đổi:", error);
      onConversionError("Chuyển đổi thất bại. Vui lòng thử lại.");
      toast.error("Chuyển đổi thất bại. Vui lòng thử lại.");
    }
  };

  const canStartConversion = !isProcessing && selectedModel && targetSpeaker;

  return (
    <div className="space-y-6">
      {/* Model Selection */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label className="text-white">Mô Hình Giọng Nói</Label>
          <Select value={selectedModel} onValueChange={setSelectedModel}>
            <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
              <SelectValue placeholder="Chọn mô hình giọng nói" />
            </SelectTrigger>
            <SelectContent className="bg-slate-700 border-slate-600">
              {availableModels.map((model) => (
                <SelectItem key={model.id} value={model.id}>
                  <div className="flex flex-col">
                    <span>{model.name}</span>
                    <span className="text-xs text-slate-400">{model.description}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label className="text-white">Giọng Nói Đích</Label>
          <Select value={targetSpeaker} onValueChange={setTargetSpeaker}>
            <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
              <SelectValue placeholder="Chọn giọng nói đích" />
            </SelectTrigger>
            <SelectContent className="bg-slate-700 border-slate-600">
              {targetSpeakers.map((speaker) => (
                <SelectItem key={speaker.id} value={speaker.id}>
                  <div className="flex items-center justify-between w-full">
                    <div className="flex flex-col">
                      <span>{speaker.name}</span>
                      <span className="text-xs text-slate-400">{speaker.type}</span>
                    </div>
                    <Badge variant="outline" className="ml-2 text-xs">
                      {speaker.quality}
                    </Badge>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Conversion Settings */}
      <Card className="p-4 bg-slate-800/30 border-slate-700">
        <h3 className="text-lg font-medium text-white mb-4">Cài Đặt Chuyển Đổi</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-2">
            <Label className="text-white">Độ Mạnh Chuyển Đổi</Label>
            <Slider
              value={conversionStrength}
              onValueChange={setConversionStrength}
              max={1}
              min={0}
              step={0.1}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-slate-400">
              <span>Nhẹ</span>
              <span>{conversionStrength[0].toFixed(1)}</span>
              <span>Mạnh</span>
            </div>
          </div>

          <div className="space-y-2">
            <Label className="text-white">Bảo Tồn Cao Độ</Label>
            <Slider
              value={preservePitch}
              onValueChange={setPreservePitch}
              max={1}
              min={0}
              step={0.1}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-slate-400">
              <span>Tự Nhiên</span>
              <span>{preservePitch[0].toFixed(1)}</span>
              <span>Gốc</span>
            </div>
          </div>

          <div className="space-y-2">
            <Label className="text-white">Giảm Nhiễu</Label>
            <Slider
              value={noiseReduction}
              onValueChange={setNoiseReduction}
              max={1}
              min={0}
              step={0.1}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-slate-400">
              <span>Tắt</span>
              <span>{noiseReduction[0].toFixed(1)}</span>
              <span>Tối Đa</span>
            </div>
          </div>
        </div>
      </Card>

      {/* Processing Status */}
      {isProcessing && (
        <Card className="p-4 bg-slate-800/30 border-slate-700">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-white font-medium">Đang Xử Lý Âm Thanh</span>
              <span className="text-slate-400">{conversionProgress}%</span>
            </div>
            <Progress value={conversionProgress} className="w-full" />
            <p className="text-sm text-slate-300">{statusMessage}</p>
          </div>
        </Card>
      )}

      {/* Audio Info */}
      <Card className="p-4 bg-slate-800/30 border-slate-700">
        <h3 className="text-lg font-medium text-white mb-3">Thông Tin Âm Thanh Đầu Vào</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-slate-400">Tên tệp:</span>
            <p className="text-white truncate">{audioFile.name}</p>
          </div>
          <div>
            <span className="text-slate-400">Kích thước:</span>
            <p className="text-white">{(audioFile.size / 1024 / 1024).toFixed(2)} MB</p>
          </div>
          <div>
            <span className="text-slate-400">Định dạng:</span>
            <p className="text-white">{audioFile.type || 'Không rõ'}</p>
          </div>
          <div>
            <span className="text-slate-400">Trạng thái:</span>
            <p className="text-green-400">Sẵn sàng</p>
          </div>
        </div>
      </Card>

      {/* Convert Button */}
      <div className="flex justify-center">
        <Button
          onClick={handleStartConversion}
          disabled={!canStartConversion}
          size="lg"
          className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white px-8 py-3"
        >
          {isProcessing ? "Đang Chuyển Đổi..." : "Bắt Đầu Chuyển Đổi Giọng Nói"}
        </Button>
      </div>
    </div>
  );
}