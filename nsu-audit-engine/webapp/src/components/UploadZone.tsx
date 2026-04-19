import React, { useRef, useState } from 'react';
import { UploadCloud, FileText, Loader2, X } from 'lucide-react';
import { cn } from '../lib/utils';

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
  isLoading: boolean;
}

export function UploadZone({ onFileSelect, isLoading }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      setSelectedFileName(file.name);
      onFileSelect(file);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      setSelectedFileName(file.name);
      onFileSelect(file);
    }
  };

  const clearSelection = (e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedFileName(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div 
      className={cn(
        "relative rounded-2xl border-2 border-dashed transition-all duration-200 ease-out overflow-hidden group",
        isDragging ? "border-nsu-cyan bg-nsu-cyan/5" : "border-slate-200 hover:border-slate-300 hover:bg-slate-50/50",
        selectedFileName ? "bg-white border-slate-200" : "bg-white",
        isLoading && "opacity-70 pointer-events-none"
      )}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => !selectedFileName && fileInputRef.current?.click()}
    >
      <input 
        type="file" 
        className="hidden" 
        ref={fileInputRef} 
        onChange={handleFileInput}
        accept=".pdf,.csv,.xlsx,.xls,.docx,.doc,.txt,.json,image/*"
      />

      <div className="flex flex-col items-center justify-center p-12 text-center">
        {isLoading ? (
          <div className="flex flex-col items-center space-y-4">
            <Loader2 className="w-12 h-12 text-nsu-blue animate-spin" />
            <p className="text-slate-600 font-medium">Scanning Transcript...</p>
          </div>
        ) : selectedFileName ? (
          <div className="flex flex-col items-center space-y-4">
            <div className="w-16 h-16 bg-blue-50 text-nsu-blue rounded-2xl flex items-center justify-center">
              <FileText className="w-8 h-8" />
            </div>
            <div className="flex items-center space-x-2">
              <span className="font-medium text-slate-900">{selectedFileName}</span>
              <button 
                onClick={clearSelection}
                className="p-1 hover:bg-slate-100 rounded-full text-slate-400 hover:text-red-500 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-sm text-slate-500">Processing queued.</p>
          </div>
        ) : (
          <div className="flex flex-col items-center space-y-4 cursor-pointer">
            <div className="w-16 h-16 bg-slate-50 text-slate-400 group-hover:text-nsu-blue group-hover:bg-blue-50 transition-colors rounded-2xl flex items-center justify-center">
              <UploadCloud className="w-8 h-8" />
            </div>
            <div>
              <p className="font-medium text-slate-900 text-lg">Click to upload or drag and drop</p>
              <p className="text-slate-500 mt-1">Supports PDF, Excel, CSV, DOCX, and Pictures (PNG, JPG)</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
