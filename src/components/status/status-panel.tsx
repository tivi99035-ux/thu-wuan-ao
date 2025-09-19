"use client";

import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

interface StatusPanelProps {
  status: string;
  isProcessing: boolean;
}

export function StatusPanel({ status, isProcessing }: StatusPanelProps) {
  const getStatusColor = (status: string) => {
    if (status.includes("Lỗi")) return "bg-red-500/20 text-red-400 border-red-500/30";
    if (status.includes("Đang xử lý") || status.includes("Đang chuyển đổi")) return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
    if (status.includes("hoàn tất")) return "bg-green-500/20 text-green-400 border-green-500/30";
    return "bg-blue-500/20 text-blue-400 border-blue-500/30";
  };

  const getStatusIcon = (status: string) => {
    if (status.includes("Lỗi")) {
      return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    }
    
    if (isProcessing) {
      return (
        <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      );
    }
    
    if (status.includes("hoàn tất")) {
      return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      );
    }
    
    return (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-3">
        <Badge 
          variant="outline" 
          className={`flex items-center space-x-2 px-3 py-1 ${getStatusColor(status)}`}
        >
          {getStatusIcon(status)}
          <span>{status}</span>
        </Badge>
      </div>

      {isProcessing && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400">Đang xử lý...</span>
            <span className="text-slate-300">Vui lòng đợi</span>
          </div>
          <Progress value={undefined} className="w-full" />
        </div>
      )}

      <div className="space-y-3 text-sm">
        <div className="flex items-center justify-between py-2 border-b border-slate-700">
          <span className="text-slate-400">Sử dụng CPU:</span>
          <div className="flex items-center space-x-2">
            <div className="w-16 bg-slate-700 rounded-full h-2">
              <div className="bg-blue-500 h-2 rounded-full w-3/4"></div>
            </div>
            <span className="text-slate-300">75%</span>
          </div>
        </div>

        <div className="flex items-center justify-between py-2 border-b border-slate-700">
          <span className="text-slate-400">Bộ nhớ:</span>
          <div className="flex items-center space-x-2">
            <div className="w-16 bg-slate-700 rounded-full h-2">
              <div className="bg-green-500 h-2 rounded-full w-1/2"></div>
            </div>
            <span className="text-slate-300">4.2/8GB</span>
          </div>
        </div>

        <div className="flex items-center justify-between py-2">
          <span className="text-slate-400">Hàng đợi:</span>
          <span className="text-slate-300">0 đang chờ</span>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium text-white">Hoạt Động Gần Đây</h4>
        <div className="space-y-1 text-xs">
          <div className="flex items-center justify-between text-slate-400">
            <span>Hệ thống đã khởi tạo</span>
            <span>2 phút trước</span>
          </div>
          <div className="flex items-center justify-between text-slate-400">
            <span>Mô hình đã tải</span>
            <span>1 phút trước</span>
          </div>
          {status !== "Sẵn sàng" && (
            <div className="flex items-center justify-between text-blue-400">
              <span>{status}</span>
              <span>Hiện tại</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}