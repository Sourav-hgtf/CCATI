import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { getReports, generateReport } from '../api/reports';
import { FileSpreadsheet, Download, RefreshCw, CheckCircle2, Eye } from 'lucide-react';

export const Reports: React.FC = () => {
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const { data: reports, isLoading } = useQuery({
    queryKey: ['executive-reports'],
    queryFn: () => getReports(),
  });

  const mutation = useMutation({
    mutationFn: (id: string) => generateReport(id),
    onSuccess: (res, id) => {
      setDownloadingId(id);
      setTimeout(() => setDownloadingId(null), 3000);
    },
  });

  if (isLoading || !reports) {
    return <div className="p-12 text-center text-gray-400">Loading Executive Reports Interface...</div>;
  }

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-2">
          <FileSpreadsheet className="w-6 h-6 text-primary" />
          <span>Executive Intelligence Reporting Center</span>
        </h1>
        <p className="text-xs text-gray-400 mt-1">Exportable executive reports, ROI financial audits, and technical model drift evaluations.</p>
      </div>

      {/* Reports Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {reports.map((rep) => {
          const isGenerating = mutation.isPending && mutation.variables === rep.id;
          const isDone = downloadingId === rep.id;

          return (
            <div key={rep.id} className="dark-card p-6 flex flex-col justify-between space-y-4 border-border hover:border-primary/50">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] uppercase font-bold text-primary px-2 py-0.5 rounded bg-primary/10 border border-primary/30">
                    {rep.category}
                  </span>
                  <span className="text-xs text-gray-400 font-mono">{rep.file_format} &bull; {rep.size}</span>
                </div>

                <h3 className="text-base font-bold text-white">{rep.title}</h3>
                <p className="text-xs text-gray-400">{rep.description}</p>
              </div>

              <div className="pt-3 border-t border-border flex items-center justify-between text-xs">
                <span className="text-[11px] text-gray-500">Updated: {rep.last_generated}</span>

                <button
                  onClick={() => mutation.mutate(rep.id)}
                  disabled={isGenerating}
                  className="px-3 py-1.5 rounded-lg bg-surfaceElevated hover:bg-surfaceHover border border-border text-gray-200 hover:text-white font-semibold flex items-center space-x-1.5 transition"
                >
                  {isDone ? (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-emerald-400">Generated</span>
                    </>
                  ) : (
                    <>
                      <Download className="w-3.5 h-3.5" />
                      <span>{isGenerating ? 'Exporting...' : 'Export'}</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
