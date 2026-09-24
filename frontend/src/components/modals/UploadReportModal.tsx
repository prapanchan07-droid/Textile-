import React, { useState, useEffect, useRef } from 'react';
import { 
  X, 
  Upload, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw, 
  History, 
  FileCheck, 
  AlertTriangle,
  FolderOpen,
  Trash2,
  Plus
} from 'lucide-react';
import { 
  ingestionService, 
  JobStatusResult, 
  FileStatusEntry, 
  ReportHistoryItem 
} from '../../services/ingestionService';

interface UploadReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: () => void;
}

const REPORT_TYPES = [
  'PRODUCTION',
  'PREPARATORY_PRODUCTION',
  'SPINNING_PRODUCTION',
  'WEAVING',
  'QUALITY',
  'DOWNTIME',
  'ENERGY',
  'MAINTENANCE',
  'MANPOWER',
  'BUSINESS'
];

export const UploadReportModal: React.FC<UploadReportModalProps> = ({
  isOpen,
  onClose,
  onUploadSuccess,
}) => {
  const [activeTab, setActiveTab] = useState<'upload' | 'history'>('upload');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [reportTypeOverride, setReportTypeOverride] = useState<string>('');
  const [dateOverride, setDateOverride] = useState<string>('');
  
  const [uploading, setUploading] = useState<boolean>(false);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatusResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [history, setHistory] = useState<ReportHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (isOpen && activeTab === 'history') {
      fetchHistory();
    }
  }, [isOpen, activeTab]);

  useEffect(() => {
    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, []);

  const fetchHistory = async () => {
    setLoadingHistory(true);
    try {
      const data = await ingestionService.getUploadHistory();
      setHistory(data);
    } catch (err) {
      console.warn('Failed to load history:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  if (!isOpen) return null;

  const handleAddFiles = (newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles);
    setSelectedFiles((prev) => {
      const existingNames = new Set(prev.map((f) => f.name + f.size));
      const filteredNew = fileArray.filter((f) => !existingNames.has(f.name + f.size));
      return [...prev, ...filteredNew];
    });
    setError(null);
  };

  const handleRemoveFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, idx) => idx !== index));
  };

  const openFilePicker = (e?: React.MouseEvent) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleAddFiles(e.target.files);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleAddFiles(e.dataTransfer.files);
    }
  };

  const startPollingJobStatus = (jobId: string) => {
    if (pollTimerRef.current) clearInterval(pollTimerRef.current);

    pollTimerRef.current = setInterval(async () => {
      try {
        const res = await ingestionService.getJobStatus(jobId);
        setJobStatus(res);

        if (res.status === 'COMPLETED' || res.status === 'FAILED') {
          if (pollTimerRef.current) clearInterval(pollTimerRef.current);
          setUploading(false);
          if (res.success_count > 0 || res.duplicate_count > 0) {
            onUploadSuccess();
          }
        }
      } catch (err: any) {
        console.warn('Error polling job status:', err);
      }
    }, 1000);
  };

  const executeJobUpload = async (forceReplace: boolean = false) => {
    if (selectedFiles.length === 0) return;

    setUploading(true);
    setError(null);
    setJobStatus(null);

    try {
      const res = await ingestionService.createIngestionJob(
        selectedFiles,
        reportTypeOverride || undefined,
        dateOverride || undefined,
        forceReplace
      );

      setActiveJobId(res.job_id);
      startPollingJobStatus(res.job_id);
    } catch (err: any) {
      setUploading(false);
      const userMsg = err.message?.includes('timeout')
        ? 'Processing is taking longer than expected. The reports are still being processed in the background.'
        : err.message || 'Failed to initiate report processing.';
      setError(userMsg);
    }
  };

  const handleResetForm = () => {
    setSelectedFiles([]);
    setJobStatus(null);
    setError(null);
    setActiveJobId(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-150">
      {/* Hidden File Input supporting multiple file selection */}
      <input
        type="file"
        ref={fileInputRef}
        multiple
        style={{ display: 'none' }}
        accept=".xlsx,.xls,.csv,.pdf,.jpg,.jpeg,.png"
        onChange={handleFileChange}
      />

      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl w-full max-w-xl overflow-hidden flex flex-col max-h-[90vh] relative z-10">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Upload className="w-4 h-4 text-blue-600" />
              Report Data Ingestion System
            </h2>
            <p className="text-xs text-slate-500 font-medium">
              Upload multiple XLSX, XLS, CSV, PDF, or scanned image reports
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex border-b border-slate-100 bg-slate-50/30 px-6 pt-2 gap-4">
          <button
            type="button"
            onClick={() => setActiveTab('upload')}
            className={`pb-2.5 text-xs font-bold transition-colors border-b-2 flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'upload'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Upload className="w-3.5 h-3.5" />
            Upload New Reports ({selectedFiles.length})
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('history')}
            className={`pb-2.5 text-xs font-bold transition-colors border-b-2 flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'history'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            Upload History
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4">
          {activeTab === 'upload' ? (
            <>
              {/* Drag & Drop Zone */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={openFilePicker}
                className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all duration-200 ${
                  isDragging
                    ? 'border-blue-500 bg-blue-50/50 scale-[0.99]'
                    : 'border-slate-200 hover:border-blue-400 bg-slate-50/40 hover:bg-slate-50'
                }`}
              >
                <div className="w-10 h-10 bg-blue-50 rounded-full flex items-center justify-center text-blue-600 mx-auto mb-2 pointer-events-none">
                  <Upload className="w-5 h-5" />
                </div>
                <h3 className="text-xs font-bold text-slate-900 pointer-events-none">
                  Click to browse or drag & drop multiple factory reports
                </h3>
                <p className="text-[11px] text-slate-400 mt-0.5 pointer-events-none">
                  Select multiple files with Ctrl/Shift • Excel (.xlsx, .xls), CSV, PDF, JPG, PNG
                </p>

                <div className="mt-3">
                  <button
                    type="button"
                    onClick={openFilePicker}
                    className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl shadow-sm transition-colors inline-flex items-center gap-1.5 cursor-pointer"
                  >
                    <FolderOpen className="w-3.5 h-3.5" />
                    Browse Files
                  </button>
                </div>
              </div>

              {/* Selected Files List UI */}
              {selectedFiles.length > 0 && (
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3">
                  <div className="flex items-center justify-between border-b border-slate-200/80 pb-2">
                    <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                      <FileText className="w-4 h-4 text-blue-600" />
                      Selected Reports ({selectedFiles.length})
                    </span>

                    {!uploading && !jobStatus && (
                      <button
                        type="button"
                        onClick={openFilePicker}
                        className="text-[11px] text-blue-600 hover:text-blue-800 font-bold flex items-center gap-1 cursor-pointer"
                      >
                        <Plus className="w-3 h-3" />
                        Add More Files
                      </button>
                    )}
                  </div>

                  {/* Individual File Items */}
                  <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1">
                    {selectedFiles.map((file, idx) => {
                      const fileStatus = jobStatus?.file_statuses?.find((f) => f.filename === file.name);

                      return (
                        <div
                          key={`${file.name}-${idx}`}
                          className="bg-white border border-slate-200/80 rounded-lg p-2.5 flex items-center justify-between text-xs"
                        >
                          <div className="flex items-center gap-2.5 min-w-0 flex-1">
                            <FileText className="w-4 h-4 text-slate-400 shrink-0" />
                            <div className="min-w-0 flex-1">
                              <h4 className="font-bold text-slate-800 truncate">{file.name}</h4>
                              <span className="text-[10px] font-mono text-slate-400">
                                {(file.size / 1024).toFixed(1)} KB
                              </span>
                            </div>
                          </div>

                          <div className="flex items-center gap-2 shrink-0">
                            {/* Live Status Badges */}
                            {fileStatus ? (
                              fileStatus.status === 'SUCCESS' ? (
                                <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded-full text-[10px] font-bold flex items-center gap-1">
                                  <CheckCircle2 className="w-3 h-3" /> Processed
                                </span>
                              ) : fileStatus.status === 'DUPLICATE' ? (
                                <span className="px-2 py-0.5 bg-amber-100 text-amber-800 rounded-full text-[10px] font-bold flex items-center gap-1">
                                  <AlertTriangle className="w-3 h-3" /> Duplicate
                                </span>
                              ) : fileStatus.status === 'FAILED' ? (
                                <span className="px-2 py-0.5 bg-rose-100 text-rose-800 rounded-full text-[10px] font-bold flex items-center gap-1">
                                  <AlertCircle className="w-3 h-3" /> Failed
                                </span>
                              ) : (
                                <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full text-[10px] font-bold flex items-center gap-1">
                                  <RefreshCw className="w-3 h-3 animate-spin" /> Processing
                                </span>
                              )
                            ) : (
                              <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded-full text-[10px] font-bold">
                                Ready
                              </span>
                            )}

                            {/* Individual Remove Button */}
                            {!uploading && (
                              <button
                                type="button"
                                onClick={() => handleRemoveFile(idx)}
                                className="p-1 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition-colors"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Optional Overrides */}
                  {!jobStatus && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-slate-200/60">
                      <div>
                        <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                          Report Type Override (Optional)
                        </label>
                        <select
                          value={reportTypeOverride}
                          onChange={(e) => setReportTypeOverride(e.target.value)}
                          className="w-full text-xs font-semibold bg-white border border-slate-200 rounded-lg p-2 focus:outline-none focus:border-blue-500"
                        >
                          <option value="">Auto-Detect from content</option>
                          {REPORT_TYPES.map((t) => (
                            <option key={t} value={t}>
                              {t}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                          Report Date Override (Optional)
                        </label>
                        <input
                          type="date"
                          value={dateOverride}
                          onChange={(e) => setDateOverride(e.target.value)}
                          className="w-full text-xs font-semibold bg-white border border-slate-200 rounded-lg p-2 focus:outline-none focus:border-blue-500"
                        />
                      </div>
                    </div>
                  )}

                  {/* Start Processing Action Button */}
                  {!jobStatus && !uploading && (
                    <button
                      type="button"
                      onClick={() => executeJobUpload(false)}
                      className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-sm transition-colors flex items-center justify-center gap-2 cursor-pointer"
                    >
                      <Upload className="w-4 h-4" />
                      Process & Ingest {selectedFiles.length} Report{selectedFiles.length > 1 ? 's' : ''}
                    </button>
                  )}
                </div>
              )}

              {/* Live Multi-File Processing Progress Bar */}
              {uploading && jobStatus && (
                <div className="p-4 bg-blue-50/70 border border-blue-200 rounded-xl space-y-2">
                  <div className="flex justify-between text-xs font-bold text-slate-800">
                    <span className="flex items-center gap-2">
                      <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
                      Processing {jobStatus.processed_count} of {jobStatus.total_files} reports...
                    </span>
                    <span className="font-mono text-blue-600 font-bold">{jobStatus.progress_pct}%</span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden">
                    <div
                      className="bg-blue-600 h-full transition-all duration-300"
                      style={{ width: `${jobStatus.progress_pct}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Error Alert */}
              {error && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {/* Processing Completed Summary */}
              {jobStatus && jobStatus.status === 'COMPLETED' && (
                <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl space-y-3 animate-in fade-in duration-200">
                  <div className="flex items-center justify-between border-b border-emerald-200 pb-2">
                    <span className="text-xs font-bold text-emerald-800 flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      Ingestion Job Completed
                    </span>
                    <span className="text-xs font-mono text-emerald-700 font-bold">
                      {jobStatus.success_count} Passed • {jobStatus.duplicate_count} Duplicate • {jobStatus.failed_count} Failed
                    </span>
                  </div>

                  <div className="space-y-1 text-xs">
                    {jobStatus.file_statuses.map((fs, fIdx) => (
                      <div key={fIdx} className="flex items-center justify-between text-[11px] bg-white/70 p-2 rounded-lg">
                        <span className="font-semibold text-slate-800 truncate">{fs.filename}</span>
                        <span
                          className={`font-bold ${
                            fs.status === 'SUCCESS'
                              ? 'text-emerald-700'
                              : fs.status === 'DUPLICATE'
                              ? 'text-amber-700'
                              : 'text-rose-700'
                          }`}
                        >
                          {fs.message}
                        </span>
                      </div>
                    ))}
                  </div>

                  <div className="pt-2 flex justify-between items-center">
                    <button
                      type="button"
                      onClick={handleResetForm}
                      className="text-xs font-bold text-slate-500 hover:text-slate-800"
                    >
                      Upload Additional Files
                    </button>

                    <button
                      type="button"
                      onClick={onClose}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-sm transition-colors cursor-pointer"
                    >
                      Done & Update Dashboard
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            /* Upload History Tab */
            <div className="space-y-3">
              {loadingHistory ? (
                <div className="py-8 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
                  <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
                  Loading upload history...
                </div>
              ) : history.length === 0 ? (
                <div className="py-8 text-center text-xs text-slate-400">
                  No uploaded reports found in database history.
                </div>
              ) : (
                <div className="space-y-2">
                  {history.map((item) => (
                    <div
                      key={item.id}
                      className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-3">
                        <FileCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                        <div>
                          <h4 className="font-bold text-slate-900">{item.filename}</h4>
                          <div className="flex items-center gap-2 text-[10px] text-slate-500 font-mono mt-0.5">
                            <span>{item.report_type}</span>
                            <span>•</span>
                            <span>{item.upload_timestamp}</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded-full text-[10px] font-bold">
                          ✓ Processed
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
