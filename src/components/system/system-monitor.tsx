"use client";

import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { wsClient } from "@/lib/websocket-client";

interface SystemStats {
  system: {
    cpu_percent: number;
    memory: {
      total: number;
      used: number;
      percent: number;
    };
    cpu_count: number;
  };
  workers: {
    [key: string]: {
      cpu_usage: number;
      memory_usage: number;
      jobs_processed: number;
      status: string;
    };
  };
  queue: {
    queue_size: number;
    processing_jobs: number;
    max_workers: number;
    worker_utilization: number;
    estimated_wait_time?: number;
  };
  connections: {
    active: number;
    total_jobs: number;
  };
}

export function SystemMonitor() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<string>("disconnected");
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    // WebSocket event handlers
    const handleSystemStatus = (data: any) => {
      if (data.type === 'system_status') {
        setStats(data);
        setLastUpdate(new Date());
      }
    };

    const handleConnection = () => {
      setConnectionStatus("connected");
      // Request initial system status
      wsClient.requestSystemStatus();
    };

    const handleDisconnection = () => {
      setConnectionStatus("disconnected");
    };

    // Register handlers
    wsClient.on('system_status', handleSystemStatus);
    wsClient.onConnection(handleConnection);
    wsClient.onDisconnection(handleDisconnection);

    // Set initial connection status
    setConnectionStatus(wsClient.getConnectionState());

    // Request system status if already connected
    if (wsClient.isConnected()) {
      wsClient.requestSystemStatus();
    }

    // Cleanup on unmount
    return () => {
      wsClient.off('system_status', handleSystemStatus);
    };
  }, []);

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusColor = (status: string): string => {
    switch (status.toLowerCase()) {
      case 'connected':
      case 'healthy':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'processing':
      case 'connecting':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'disconnected':
      case 'error':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      default:
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    }
  };

  if (!stats) {
    return (
      <Card className="p-6 bg-slate-800/50 border-slate-700">
        <h2 className="text-xl font-semibold mb-4 text-white">Giám Sát Hệ Thống</h2>
        <div className="flex items-center justify-center py-8">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-blue-500 animate-pulse"></div>
            <span className="text-slate-400">Đang tải thông tin hệ thống...</span>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6 bg-slate-800/50 border-slate-700">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-white">Giám Sát Hệ Thống</h2>
        <div className="flex items-center space-x-2">
          <Badge variant="outline" className={getStatusColor(connectionStatus)}>
            {connectionStatus === 'connected' ? 'Kết Nối' : 'Ngắt Kết Nối'}
          </Badge>
          {lastUpdate && (
            <span className="text-xs text-slate-400">
              Cập nhật: {lastUpdate.toLocaleTimeString('vi-VN')}
            </span>
          )}
        </div>
      </div>

      <div className="space-y-6">
        {/* System Resources */}
        <div>
          <h3 className="text-lg font-medium text-white mb-3">Tài Nguyên Hệ Thống</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-400">CPU ({stats.system.cpu_count} nhân)</span>
                  <span className="text-slate-300">{stats.system.cpu_percent.toFixed(1)}%</span>
                </div>
                <Progress value={stats.system.cpu_percent} className="h-2" />
              </div>
              
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-400">Bộ Nhớ</span>
                  <span className="text-slate-300">
                    {formatBytes(stats.system.memory.used)} / {formatBytes(stats.system.memory.total)}
                  </span>
                </div>
                <Progress value={stats.system.memory.percent} className="h-2" />
              </div>
            </div>
          </div>
        </div>

        {/* Worker Status */}
        <div>
          <h3 className="text-lg font-medium text-white mb-3">Trạng Thái Worker</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="text-center p-3 bg-slate-700/30 rounded-lg">
              <div className="text-xl font-bold text-blue-400">{stats.queue.max_workers}</div>
              <div className="text-xs text-slate-400">Worker Tối Đa</div>
            </div>
            <div className="text-center p-3 bg-slate-700/30 rounded-lg">
              <div className="text-xl font-bold text-green-400">{stats.queue.processing_jobs}</div>
              <div className="text-xs text-slate-400">Đang Xử Lý</div>
            </div>
            <div className="text-center p-3 bg-slate-700/30 rounded-lg">
              <div className="text-xl font-bold text-yellow-400">{stats.queue.queue_size}</div>
              <div className="text-xs text-slate-400">Hàng Đợi</div>
            </div>
            <div className="text-center p-3 bg-slate-700/30 rounded-lg">
              <div className="text-xl font-bold text-purple-400">{stats.queue.worker_utilization.toFixed(0)}%</div>
              <div className="text-xs text-slate-400">Sử Dụng</div>
            </div>
          </div>
        </div>

        {/* Connection Stats */}
        <div>
          <h3 className="text-lg font-medium text-white mb-3">Kết Nối Người Dùng</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex justify-between p-3 bg-slate-700/30 rounded-lg">
              <span className="text-slate-400">Kết nối đang hoạt động:</span>
              <span className="text-white font-medium">{stats.connections.active}</span>
            </div>
            <div className="flex justify-between p-3 bg-slate-700/30 rounded-lg">
              <span className="text-slate-400">Công việc đang theo dõi:</span>
              <span className="text-white font-medium">{stats.connections.total_jobs}</span>
            </div>
          </div>
        </div>

        {/* Queue Information */}
        {stats.queue.queue_size > 0 && (
          <div>
            <h3 className="text-lg font-medium text-white mb-3">Thông Tin Hàng Đợi</h3>
            <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-yellow-400 font-medium">Có {stats.queue.queue_size} công việc đang chờ</span>
                <span className="text-yellow-300 text-sm">
                  Thời gian chờ ước tính: {Math.round((stats.queue.estimated_wait_time || 0) / 60)} phút
                </span>
              </div>
              <Progress value={stats.queue.worker_utilization} className="h-2" />
            </div>
          </div>
        )}

        {/* Performance Metrics */}
        <div>
          <h3 className="text-lg font-medium text-white mb-3">Hiệu Suất</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">Độ sử dụng Worker:</span>
              <span className={`font-medium ${stats.queue.worker_utilization > 80 ? 'text-red-400' : stats.queue.worker_utilization > 50 ? 'text-yellow-400' : 'text-green-400'}`}>
                {stats.queue.worker_utilization.toFixed(1)}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Trạng thái Redis:</span>
              <span className="text-green-400">Hoạt động</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">WebSocket:</span>
              <span className={connectionStatus === 'connected' ? 'text-green-400' : 'text-red-400'}>
                {connectionStatus === 'connected' ? 'Kết nối' : 'Ngắt kết nối'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}