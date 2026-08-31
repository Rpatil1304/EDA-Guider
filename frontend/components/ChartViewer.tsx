'use client';

export default function ChartViewer({ chartData }: { chartData: any }) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">Visualization</h2>
      {/* Chart rendering logic */}
      <div className="bg-gray-100 h-80 rounded flex items-center justify-center">
        <p className="text-gray-600">Chart will render here</p>
      </div>
    </div>
  );
}
