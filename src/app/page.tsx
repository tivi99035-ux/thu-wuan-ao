"use client";

import { useState } from "react";
import { Header } from "@/components/layout/header";
import { AudioUploader } from "@/components/audio/audio-uploader";
import { VoiceConverter } from "@/components/voice/voice-converter";
import { VoiceCloner } from "@/components/voice/voice-cloner";
import { ResultsPanel } from "@/components/results/results-panel";
import { StatusPanel } from "@/components/status/status-panel";
import { SystemMonitor } from "@/components/system/system-monitor";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function HomePage() {
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [conversionResult, setConversionResult] = useState<string | null>(null);
  const [cloningResult, setCloningResult] = useState<string | null>(null);
  const [processingStatus, setProcessingStatus] = useState<string>("Sẵn sàng");
  const [activeTab, setActiveTab] = useState("convert");

  const handleAudioUpload = (file: File) => {
    setAudioFile(file);
    setConversionResult(null);
    setProcessingStatus("Đã tải âm thanh");
  };

  const handleConversionStart = () => {
    setIsProcessing(true);
    setProcessingStatus("Đang xử lý...");
  };

  const handleConversionComplete = (result: string) => {
    setConversionResult(result);
    setIsProcessing(false);
    setProcessingStatus("Chuyển đổi hoàn tất");
  };

  const handleConversionError = (error: string) => {
    console.error("Lỗi chuyển đổi:", error);
    setIsProcessing(false);
    setProcessingStatus(`Lỗi: ${error}`);
  };

  const handleCloningStart = () => {
    setIsProcessing(true);
    setProcessingStatus("Đang nhân bản giọng nói...");
  };

  const handleCloningComplete = (result: string) => {
    setCloningResult(result);
    setIsProcessing(false);
    setProcessingStatus("Nhân bản giọng nói hoàn tất");
  };

  const handleCloningError = (error: string) => {
    console.error("Lỗi nhân bản giọng nói:", error);
    setIsProcessing(false);
    setProcessingStatus(`Lỗi: ${error}`);
  };

  return (
    <div className="min-h-screen">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Voice Processing */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="p-6 bg-slate-800/50 border-slate-700">
              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid w-full grid-cols-2 mb-6">
                  <TabsTrigger value="convert">Chuyển Đổi Giọng Nói</TabsTrigger>
                  <TabsTrigger value="clone">Nhân Bản Giọng Nói</TabsTrigger>
                </TabsList>
                
                <TabsContent value="convert" className="space-y-6">
                  <div className="space-y-6">
                    <div>
                      <h2 className="text-xl font-semibold mb-4 text-white">Tải Lên Âm Thanh</h2>
                      <AudioUploader onFileUpload={handleAudioUpload} />
                    </div>

                    {audioFile && (
                      <div>
                        <h2 className="text-xl font-semibold mb-4 text-white">Cài Đặt Chuyển Đổi</h2>
                        <VoiceConverter
                          audioFile={audioFile}
                          isProcessing={isProcessing}
                          onConversionStart={handleConversionStart}
                          onConversionComplete={handleConversionComplete}
                          onConversionError={handleConversionError}
                        />
                      </div>
                    )}
                  </div>
                </TabsContent>
                
                <TabsContent value="clone" className="space-y-6">
                  <div>
                    <h2 className="text-xl font-semibold mb-4 text-white">Nhân Bản Giọng Nói AI</h2>
                    <VoiceCloner
                      isProcessing={isProcessing}
                      onCloningStart={handleCloningStart}
                      onCloningComplete={handleCloningComplete}
                      onCloningError={handleCloningError}
                    />
                  </div>
                </TabsContent>
              </Tabs>
            </Card>

            {(conversionResult || cloningResult) && (
              <Card className="p-6 bg-slate-800/50 border-slate-700">
                <h2 className="text-xl font-semibold mb-4 text-white">Kết Quả</h2>
                <ResultsPanel
                  originalFile={activeTab === "convert" ? audioFile : null}
                  convertedAudio={conversionResult || cloningResult || ""}
                />
              </Card>
            )}
          </div>

          {/* Right Column - Status and Information */}
          <div className="space-y-6">
            <Card className="p-6 bg-slate-800/50 border-slate-700">
              <h2 className="text-xl font-semibold mb-4 text-white">Trạng Thái Xử Lý</h2>
              <StatusPanel
                status={processingStatus}
                isProcessing={isProcessing}
              />
            </Card>

            <Card className="p-6 bg-slate-800/50 border-slate-700">
              <h2 className="text-xl font-semibold mb-4 text-white">Thông Tin Hệ Thống</h2>
              <div className="space-y-3 text-sm text-slate-300">
                <div className="flex justify-between">
                  <span>Chế độ xử lý:</span>
                  <span className="text-green-400">Tối ưu CPU</span>
                </div>
                <div className="flex justify-between">
                  <span>Loại mô hình:</span>
                  <span className="text-blue-400">Seed-VC</span>
                </div>
                <div className="flex justify-between">
                  <span>Trạng thái hàng đợi:</span>
                  <span className="text-yellow-400">Khả dụng</span>
                </div>
                <div className="flex justify-between">
                  <span>Kích thước tối đa:</span>
                  <span>100 MB</span>
                </div>
              </div>
            </Card>

            <Card className="p-6 bg-slate-800/50 border-slate-700">
              <h2 className="text-xl font-semibold mb-4 text-white">Hướng Dẫn Nhanh</h2>
              <div className="space-y-3 text-sm text-slate-300">
                <div>
                  <h3 className="font-medium text-white mb-2">🔄 Chuyển Đổi Giọng Nói:</h3>
                  <div className="space-y-1 text-xs">
                    <p>1. Tải lên tệp âm thanh</p>
                    <p>2. Chọn mô hình giọng nói đích</p>
                    <p>3. Điều chỉnh cài đặt</p>
                    <p>4. Bắt đầu chuyển đổi</p>
                  </div>
                </div>
                <div>
                  <h3 className="font-medium text-white mb-2">🎭 Nhân Bản Giọng Nói:</h3>
                  <div className="space-y-1 text-xs">
                    <p>1. Tải giọng tham khảo</p>
                    <p>2. Tải nội dung cần đổi</p>
                    <p>3. Điều chỉnh độ tương đồng</p>
                    <p>4. Bắt đầu nhân bản</p>
                  </div>
                </div>
              </div>
            </Card>

            <SystemMonitor />
          </div>
        </div>
      </main>
    </div>
  );
}