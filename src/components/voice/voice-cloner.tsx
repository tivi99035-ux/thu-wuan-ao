"use client";

import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";

// Mock toast function for demo - replace with actual toast library
const toast = {
  success: (message: string) => console.log("Thành công:", message),
  error: (message: string) => console.error("Lỗi:", message),
  info: (message: string) => console.info("Thông tin:", message)
};

interface VoiceClonerProps {
  onCloningStart: () => void;
  onCloningComplete: (result: string) => void;
  onCloningError: (error: string) => void;
  isProcessing: boolean;
}

export function VoiceCloner({
  onCloningStart,
  onCloningComplete,
  onCloningError,
  isProcessing
}: VoiceClonerProps) {
  const [referenceFile, setReferenceFile] = useState<File | null>(null);
  const [targetFile, setTargetFile] = useState<File | null>(null);
  const [similarityThreshold, setSimilarityThreshold] = useState([0.8]);
  const [cloningProgress, setCloningProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  
  const refInputRef = useRef<HTMLInputElement>(null);
  const targetInputRef = useRef<HTMLInputElement>(null);

  const handleReferenceFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setReferenceFile(file);
      toast.success("Đã chọn tệp giọng nói tham khảo");
    }
  };

  const handleTargetFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setTargetFile(file);
      toast.success("Đã chọn tệp nội dung cần chuyển đổi");
    }
  };

  const simulateCloning = async () => {
    const steps = [
      { message: "Đang phân tích giọng nói tham khảo...", progress: 15 },
      { message: "Đang trích xuất đặc trưng giọng nói...", progress: 30 },
      { message: "Đang tạo mô hình giọng nói...", progress: 50 },
      { message: "Đang áp dụng đặc trưng vào âm thanh đích...", progress: 70 },
      { message: "Đang tinh chỉnh chất lượng giọng nói...", progress: 85 },
      { message: "Hoàn thành nhân bản giọng nói...", progress: 100 }
    ];

    for (const step of steps) {
      setStatusMessage(step.message);
      setCloningProgress(step.progress);
      await new Promise(resolve => setTimeout(resolve, 1500 + Math.random() * 1000));
    }

    // Simulate successful cloning result
    const mockAudioUrl = URL.createObjectURL(targetFile!);
    onCloningComplete(mockAudioUrl);
  };

  const handleStartCloning = async () => {
    if (!referenceFile) {
      toast.error("Vui lòng chọn tệp giọng nói tham khảo");
      return;
    }

    if (!targetFile) {
      toast.error("Vui lòng chọn tệp nội dung cần chuyển đổi");
      return;
    }

    onCloningStart();
    setCloningProgress(0);
    setStatusMessage("Bắt đầu nhân bản giọng nói...");

    try {
      await simulateCloning();
      toast.success("Nhân bản giọng nói hoàn thành thành công!");
    } catch (error) {
      console.error("Lỗi nhân bản giọng nói:", error);
      onCloningError("Nhân bản giọng nói thất bại. Vui lòng thử lại.");
      toast.error("Nhân bản giọng nói thất bại. Vui lòng thử lại.");
    }
  };

  const canStartCloning = !isProcessing && referenceFile && targetFile;

  return (
    <div className="space-y-6">
      {/* File Upload Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Reference Voice */}
        <Card className="p-4 bg-slate-800/30 border-slate-700">
          <h3 className="text-lg font-medium text-white mb-4">Giọng Nói Tham Khảo</h3>
          <div className="space-y-4">
            <div className="border-2 border-dashed border-slate-600 rounded-lg p-4 text-center">
              <div className="space-y-2">
                <div className="w-10 h-10 mx-auto rounded-full bg-purple-500/20 flex items-center justify-center">
                  <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                </div>
                <p className="text-sm text-slate-400">Chọn mẫu giọng nói để nhân bản</p>
                <Button
                  onClick={() => refInputRef.current?.click()}
                  size="sm"
                  variant="outline"
                  className="border-purple-500 text-purple-400"
                >
                  Chọn Tệp Tham Khảo
                </Button>
                <input
                  ref={refInputRef}
                  type="file"
                  accept=".wav,.mp3,.flac,.m4a"
                  onChange={handleReferenceFileSelect}
                  className="hidden"
                />
              </div>
            </div>
            {referenceFile && (
              <div className="p-3 bg-slate-700/50 rounded-lg">
                <p className="text-sm font-medium text-white truncate">{referenceFile.name}</p>
                <p className="text-xs text-slate-400">
                  {(referenceFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            )}
          </div>
        </Card>

        {/* Target Content */}
        <Card className="p-4 bg-slate-800/30 border-slate-700">
          <h3 className="text-lg font-medium text-white mb-4">Nội Dung Cần Chuyển Đổi</h3>
          <div className="space-y-4">
            <div className="border-2 border-dashed border-slate-600 rounded-lg p-4 text-center">
              <div className="space-y-2">
                <div className="w-10 h-10 mx-auto rounded-full bg-blue-500/20 flex items-center justify-center">
                  <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <p className="text-sm text-slate-400">Nội dung sẽ được nói bằng giọng tham khảo</p>
                <Button
                  onClick={() => targetInputRef.current?.click()}
                  size="sm"
                  variant="outline"
                  className="border-blue-500 text-blue-400"
                >
                  Chọn Nội Dung
                </Button>
                <input
                  ref={targetInputRef}
                  type="file"
                  accept=".wav,.mp3,.flac,.m4a"
                  onChange={handleTargetFileSelect}
                  className="hidden"
                />
              </div>
            </div>
            {targetFile && (
              <div className="p-3 bg-slate-700/50 rounded-lg">
                <p className="text-sm font-medium text-white truncate">{targetFile.name}</p>
                <p className="text-xs text-slate-400">
                  {(targetFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Cloning Settings */}
      <Card className="p-4 bg-slate-800/30 border-slate-700">
        <h3 className="text-lg font-medium text-white mb-4">Cài Đặt Nhân Bản</h3>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label className="text-white">Độ Tương Đồng Giọng Nói</Label>
            <Slider
              value={similarityThreshold}
              onValueChange={setSimilarityThreshold}
              max={1}
              min={0}
              step={0.1}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-slate-400">
              <span>Tự Nhiên (0.0)</span>
              <span className="font-mono">{similarityThreshold[0].toFixed(1)}</span>
              <span>Giống Hệt (1.0)</span>
            </div>
          </div>
          
          <div className="p-3 bg-slate-700/30 rounded-lg">
            <p className="text-xs text-slate-300 mb-1">💡 Mẹo:</p>
            <ul className="text-xs text-slate-400 space-y-1">
              <li>• Giọng tham khảo nên rõ ràng, không có tiếng ồn</li>
              <li>• Độ dài tham khảo từ 10-60 giây cho kết quả tốt nhất</li>
              <li>• Nội dung đích có thể dài hơn giọng tham khảo</li>
            </ul>
          </div>
        </div>
      </Card>

      {/* Processing Status */}
      {isProcessing && (
        <Card className="p-4 bg-slate-800/30 border-slate-700">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-white font-medium">Đang Nhân Bản Giọng Nói</span>
              <span className="text-slate-400">{cloningProgress}%</span>
            </div>
            <Progress value={cloningProgress} className="w-full" />
            <p className="text-sm text-slate-300">{statusMessage}</p>
          </div>
        </Card>
      )}

      {/* Clone Button */}
      <div className="flex justify-center">
        <Button
          onClick={handleStartCloning}
          disabled={!canStartCloning}
          size="lg"
          className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white px-8 py-3"
        >
          {isProcessing ? "Đang Nhân Bản..." : "Bắt Đầu Nhân Bản Giọng Nói"}
        </Button>
      </div>

      {/* Instructions */}
      <Card className="p-4 bg-slate-800/30 border-slate-700">
        <h3 className="text-lg font-medium text-white mb-3">Cách Sử Dụng</h3>
        <div className="space-y-2 text-sm text-slate-300">
          <p><span className="font-medium">Bước 1:</span> Tải lên tệp giọng nói tham khảo (người mà bạn muốn nhân bản giọng)</p>
          <p><span className="font-medium">Bước 2:</span> Tải lên nội dung cần chuyển đổi (văn bản đã được đọc bằng giọng khác)</p>
          <p><span className="font-medium">Bước 3:</span> Điều chỉnh độ tương đồng theo mong muốn</p>
          <p><span className="font-medium">Bước 4:</span> Nhấn &quot;Bắt Đầu Nhân Bản Giọng Nói&quot; và đợi kết quả</p>
        </div>
      </Card>
    </div>
  );
}